from flask import Flask, render_template, request, jsonify, send_from_directory, session
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
import uuid
import secrets
from datetime import datetime
import hashlib

# Load environment variables
load_dotenv()

# Import our agents with error handling
try:
    from agents.document_processor import DocumentProcessor
    from agents.summarizer import Summarizer  
    from agents.transcriber import Transcriber
    from agents.qa_agent import QAAgent
    print("✅ Successfully imported all agent modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all agent modules exist in the 'agents' directory")

# Create Flask app with explicit static folder configuration
app = Flask(__name__, 
            static_folder='static',
            static_url_path='/static')

app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(16))

# Session configuration for better persistence
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 24 * 60 * 60  # 24 hours

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/audio', exist_ok=True)
os.makedirs('data', exist_ok=True)  # Ensure data directory for vector stores exists

# Check if we can write to the data directory (important for EFS)
try:
    test_file = 'data/test_write_permissions.tmp'
    with open(test_file, 'w') as f:
        f.write('test')
    os.remove(test_file)
    print("✅ Data directory is writable")
except Exception as e:
    print(f"❌ Data directory write test failed: {e}")
    print(f"📁 Data directory permissions: {oct(os.stat('data').st_mode)[-3:]}")
    print(f"📂 Current working directory: {os.getcwd()}")
    print(f"👤 Process user: {os.getuid()}")

# Initialize agents with proper error handling
doc_processor = None
summarizer = None
transcriber = None
qa_agent = None

try:
    doc_processor = DocumentProcessor()
    print("✅ DocumentProcessor initialized")
except Exception as e:
    print(f"❌ Error initializing DocumentProcessor: {e}")

try:
    summarizer = Summarizer()
    print("✅ Summarizer initialized")
except Exception as e:
    print(f"❌ Error initializing Summarizer: {e}")

try:
    transcriber = Transcriber()
    print("✅ Transcriber initialized")
except Exception as e:
    print(f"❌ Error initializing Transcriber: {e}")

try:
    qa_agent = QAAgent()
    print("✅ QAAgent initialized")
except Exception as e:
    print(f"❌ Error initializing QAAgent: {e}")

# Check if all required agents are available (except qa_agent which is now session-based)
all_agents_ready = all([doc_processor, summarizer, transcriber])
if all_agents_ready:
    print("✅ All core agents initialized successfully")
else:
    print("⚠️  Some core agents failed to initialize - some features may not work")

def create_text_document_title(session_qa, text):
    """Create a smart title for text documents"""
    user_id = get_user_identifier()
    
    # Count existing text documents for this user
    text_doc_count = 0
    if hasattr(session_qa.vector_store, 'metadata') and session_qa.vector_store.metadata:
        for metadata in session_qa.vector_store.metadata:
            if (metadata.get('user_id') == user_id and 
                metadata.get('doc_title', '').startswith('Text Entry')):
                text_doc_count += 1
    
    # Create title with preview
    text_preview = text.strip()[:50]
    if len(text.strip()) > 50:
        text_preview += "..."
    
    # Remove newlines and clean up preview
    text_preview = ' '.join(text_preview.split())
    
    title = f"Text Entry #{text_doc_count + 1}: {text_preview}"
    return title

def get_user_identifier():
    """Get consistent user ID across requests for multi-user isolation"""
    # Priority order:
    # 1. Existing session user_id
    # 2. Create stable ID from IP + User-Agent
    # 3. Set in session for persistence
    
    if 'user_id' in session:
        return session['user_id']
    
    # Create stable ID from IP + User-Agent for consistency across requests
    ip = request.headers.get('X-Forwarded-For', request.remote_addr or '127.0.0.1')
    if ',' in ip:
        ip = ip.split(',')[0].strip()  # Handle load balancer forwarded IPs
    
    ua = request.headers.get('User-Agent', 'unknown')
    user_hash = hashlib.md5(f"{ip}:{ua}".encode()).hexdigest()[:8]
    
    user_id = f"user_{user_hash}"
    session['user_id'] = user_id
    session.permanent = True  # Keep user ID persistent
    
    print(f"👤 User ID: {user_id} (IP: {ip[:12]}...)")
    return user_id

# Session-based QA agent management
def get_session_qa_agent():
    """Get or create a QA agent for the current session"""
    # Make session permanent for better persistence
    session.permanent = True
    
    if 'session_id' not in session:
        session['session_id'] = secrets.token_hex(8)
        session['created_at'] = str(datetime.now())
        print(f"🆔 Created new session: {session['session_id']}")
    else:
        print(f"🔄 Using existing session: {session['session_id']}")
    
    session_id = session['session_id']
    print(f"🔍 DEBUG: Session ID: {session_id}")
    print(f"🔍 DEBUG: Session created: {session.get('created_at', 'Unknown')}")
    print(f"🔍 DEBUG: Session keys: {list(session.keys())}")
    
    try:
        # Import here to avoid circular imports
        from agents.qa_agent import QAAgent
        
        # Get user identifier for multi-user isolation
        user_id = get_user_identifier()
        
        # Use shared multi-user vector store in production, session-based for local development
        flask_env = os.getenv('FLASK_ENV', 'development')
        if flask_env == 'production':
            print(f"🏭 Production mode: Using shared multi-user vector store")
            qa = QAAgent(session_id="shared", user_id=user_id)  # Shared store with user isolation
        else:
            print(f"🏠 Development mode: Using session-based vector store")
            qa = QAAgent(session_id=session_id, user_id=user_id)  # Session-specific for development
            
        status = qa.get_status()
        print(f"✅ QA Agent ready for session: {session_id} (mode: {flask_env})")
        print(f"📊 QA Agent Status: {status}")
        
        # Store session info for debugging
        session['last_qa_access'] = str(datetime.now())
        
        return qa
    except Exception as e:
        print(f"❌ Error creating session QA agent: {e}")
        import traceback
        traceback.print_exc()
        return None

def cleanup_old_sessions(max_age_hours=24):
    """Clean up old session vector store files"""
    try:
        import glob
        import time
        
        data_dir = 'data'
        if not os.path.exists(data_dir):
            return
            
        pattern = os.path.join(data_dir, 'vector_store_*.pkl')
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for file_path in glob.glob(pattern):
            file_age = current_time - os.path.getmtime(file_path)
            if file_age > max_age_seconds:
                try:
                    os.remove(file_path)
                    print(f"🧹 Cleaned up old session file: {file_path}")
                except OSError as e:
                    print(f"⚠️  Failed to cleanup {file_path}: {e}")
                    
    except Exception as e:
        print(f"❌ Error in session cleanup: {e}")

# Clean up old sessions on startup
cleanup_old_sessions()

@app.route('/')
def index():
    """Serve the main application page"""
    print("📄 Serving index.html")
    ga_measurement_id = os.getenv('GA_MEASUREMENT_ID')
    return render_template('index.html', ga_measurement_id=ga_measurement_id)

@app.route('/about')
def about():
    """Serve the about page"""
    print("ℹ️  Serving about.html")
    ga_measurement_id = os.getenv('GA_MEASUREMENT_ID')
    return render_template('about.html', ga_measurement_id=ga_measurement_id)

# Favicon route
@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Static file route (explicit)
@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files explicitly"""
    print(f"📁 Serving static file: {filename}")
    return send_from_directory('static', filename)

@app.route('/api/process-content', methods=['POST'])
def process_content():
    """Process uploaded content and return summary - TEXT AND DOCUMENTS ONLY"""
    print(f"🔄 Processing content request: {request.content_type}")
    
    # Check if summarizer is available
    if not summarizer:
        return jsonify({'error': 'Summarizer not available. Please check server logs.'}), 500
    
    try:
        summary_level = 'standard'  # Default level
        
        if request.is_json:
            # Handle JSON request (text input)
            data = request.get_json()
            content_type = data.get('type')
            summary_level = data.get('summary_level', 'standard')
            voice = data.get('voice', 'nova')
            
            print(f"📝 Processing text content with {summary_level} summary")
            
            if content_type == 'text':
                text = data.get('text')
                if not text:
                    return jsonify({'error': 'No text provided'}), 400
                
                print(f"📄 Text length: {len(text)} characters")
                
                # Process text with specified summary level
                summary = summarizer.summarize(text, detail_level=summary_level)
                
                # Generate audio if transcriber is available
                audio_url = None
                if transcriber:
                    try:
                        audio_url = transcriber.text_to_speech(summary, voice=voice)
                        print(f"🔊 Generated audio with {voice} voice: {audio_url}")
                    except Exception as e:
                        print(f"⚠️  Audio generation failed: {e}")
                
                # Store for QA with session-based agent - WITH ENHANCED DEBUGGING
                qa_success = False
                session_qa = get_session_qa_agent()
                if session_qa:
                    try:
                        print(f"🔍 CONTENT PROCESSING DEBUG:")
                        print(f"🆔 Session ID: {session.get('session_id')}")
                        print(f"📁 Vector store path: {session_qa.vector_store.persist_path}")
                        print(f"💾 Storing text for Q&A (length: {len(text)})")
                        
                        # Create a smart title for text documents
                        text_title = create_text_document_title(session_qa, text)
                        qa_success = session_qa.add_document(text, text_title)
                        print(f"✅ QA storage result: {qa_success}")
                        
                        # Vector store automatically saves after adding documents
                        print("✅ Document processed and vectors stored")
                        
                        # Verify storage worked
                        status = session_qa.get_status()
                        print(f"📊 QA Status after storage: {status}")
                        
                        # Verify file was actually saved
                        if os.path.exists(session_qa.vector_store.persist_path):
                            file_size = os.path.getsize(session_qa.vector_store.persist_path)
                            print(f"📦 Vector store file saved: {file_size} bytes")
                        else:
                            print(f"⚠️ Vector store file NOT found at: {session_qa.vector_store.persist_path}")
                        
                    except Exception as e:
                        print(f"❌ QA storage failed: {e}")
                        import traceback
                        traceback.print_exc()
                
                return jsonify({
                    'summary': summary,
                    'audio_url': audio_url,
                    'summary_level': summary_level,
                    'qa_stored': qa_success,
                    'success': True
                })
        else:
            # Handle file upload - DOCUMENTS ONLY
            file = request.files.get('file')
            content_type = request.form.get('type')
            summary_level = request.form.get('summary_level', 'standard')
            voice = request.form.get('voice', 'nova')
            
            print(f"📄 Processing {content_type} file: {file.filename if file else 'None'} with {summary_level} summary")
            
            if not file:
                return jsonify({'error': 'No file uploaded'}), 400
            
            # Only allow document files - NO AUDIO
            if content_type != 'file':
                return jsonify({'error': 'Only document files are supported'}), 400
            
            # Check if document processor is available
            if not doc_processor:
                return jsonify({'error': 'Document processor not available. Please check server logs.'}), 500
            
            # Save uploaded file
            filename = secure_filename(file.filename)
            file_id = str(uuid.uuid4())
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{filename}")
            file.save(file_path)
            
            try:
                # Extract text from document
                print(f"📖 Extracting text from: {filename}")
                text = doc_processor.extract_text(file_path)
                
                if not text:
                    return jsonify({'error': 'Could not extract text from the uploaded file'}), 400
                
                print(f"📄 Extracted text length: {len(text)} characters")
                
                # Generate summary with specified level
                summary = summarizer.summarize(text, detail_level=summary_level)
                
                # Generate audio if transcriber is available
                audio_url = None
                if transcriber:
                    try:
                        audio_url = transcriber.text_to_speech(summary, voice=voice)
                        print(f"🔊 Generated audio with {voice} voice: {audio_url}")
                    except Exception as e:
                        print(f"⚠️  Audio generation failed: {e}")
                
                # Store for QA with session-based agent - WITH ENHANCED DEBUGGING
                qa_success = False
                session_qa = get_session_qa_agent()
                if session_qa:
                    try:
                        print(f"🔍 FILE PROCESSING DEBUG:")
                        print(f"🆔 Session ID: {session.get('session_id')}")
                        print(f"📁 Vector store path: {session_qa.vector_store.persist_path}")
                        print(f"💾 Storing document '{filename}' for Q&A (length: {len(text)})")
                        
                        qa_success = session_qa.add_document(text, filename)
                        print(f"✅ QA storage result: {qa_success}")
                        
                        # Vector store automatically saves after adding documents
                        print("✅ Document processed and vectors stored")
                        
                        # Verify storage worked
                        status = session_qa.get_status()
                        print(f"📊 QA Status after storage: {status}")
                        
                        # Verify file was actually saved
                        if os.path.exists(session_qa.vector_store.persist_path):
                            file_size = os.path.getsize(session_qa.vector_store.persist_path)
                            print(f"📦 Vector store file saved: {file_size} bytes")
                        else:
                            print(f"⚠️ Vector store file NOT found at: {session_qa.vector_store.persist_path}")
                        
                    except Exception as e:
                        print(f"❌ QA storage failed: {e}")
                        import traceback
                        traceback.print_exc()
                
                return jsonify({
                    'summary': summary,
                    'audio_url': audio_url,
                    'summary_level': summary_level,
                    'qa_stored': qa_success,
                    'success': True
                })
                
            finally:
                # Clean up uploaded file
                if os.path.exists(file_path):
                    os.remove(file_path)
    
    except Exception as e:
        print(f"❌ Error processing content: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/ask-question', methods=['POST'])
def ask_question():
    """Handle Q&A requests"""
    print(f"🔍 =========================")
    print(f"🔍 ASK QUESTION DEBUG START")
    print(f"🔍 =========================")
    
    # Get session-based QA agent
    session_qa = get_session_qa_agent()
    if not session_qa:
        return jsonify({'error': 'Q&A agent not available. Please check server logs.'}), 500
    
    try:
        data = request.get_json()
        question = data.get('question')
        voice = data.get('voice', 'nova')  # Default voice for Q&A audio
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        print(f"❓ Processing question: {question[:50]}...")
        print(f"🆔 Session ID: {session.get('session_id', 'None')}")
        print(f"📁 Vector store path: {session_qa.vector_store.persist_path}")
        
        # Debug QA agent status before answering
        status = session_qa.get_status()
        print(f"📊 QA Agent Status: {status}")
        
        # Check if vector store file exists on disk
        import os
        vector_file_exists = os.path.exists(session_qa.vector_store.persist_path)
        print(f"💾 Vector store file exists: {vector_file_exists}")
        if vector_file_exists:
            file_size = os.path.getsize(session_qa.vector_store.persist_path)
            print(f"📦 Vector store file size: {file_size} bytes")
        
        # Enhanced debugging - try to reload if no vectors in memory
        if not status.get('ready_for_questions', False):
            print("⚠️ No documents detected, attempting diagnosis...")
            
            # Try to reload the vector store
            try:
                print("🔄 Reloading vector store from disk...")
                session_qa.vector_store.load()
                status_after_reload = session_qa.get_status()
                print(f"📊 Status after reload: {status_after_reload}")
                
                if status_after_reload.get('ready_for_questions', False):
                    print("✅ Successfully reloaded vectors!")
                    status = status_after_reload
                else:
                    print("❌ Still no vectors after reload")
                    return jsonify({
                        'error': 'No documents available for Q&A. Please upload a document first.',
                        'debug_info': {
                            'session_id': session.get('session_id'),
                            'vector_store_path': str(session_qa.vector_store.persist_path),
                            'file_exists': vector_file_exists,
                            'file_size': file_size if vector_file_exists else 0,
                            'documents_in_memory': len(session_qa.documents),
                            'vectors_in_memory': len(session_qa.vector_store.vectors),
                            'status_before_reload': status,
                            'status_after_reload': status_after_reload
                        }
                    }), 400
                    
            except Exception as reload_error:
                print(f"❌ Error reloading vector store: {reload_error}")
                return jsonify({
                    'error': 'No documents available for Q&A. Please upload a document first.',
                    'reload_error': str(reload_error),
                    'debug_info': {
                        'session_id': session.get('session_id'),
                        'vector_store_path': str(session_qa.vector_store.persist_path),
                        'file_exists': vector_file_exists
                    }
                }), 400
        
        # Get answer from QA agent
        answer = session_qa.answer_question(question)
        
        # Generate audio for answer if transcriber is available
        audio_url = None
        if transcriber:
            try:
                audio_url = transcriber.text_to_speech(answer, voice=voice)
                print(f"🔊 Generated audio for answer with {voice} voice: {audio_url}")
            except Exception as e:
                print(f"⚠️  Audio generation failed: {e}")
        
        return jsonify({
            'answer': answer,
            'audio_url': audio_url,
            'qa_status': status,
            'success': True
        })
        
    except Exception as e:
        print(f"❌ Error answering question: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/transcribe-audio', methods=['POST'])
def transcribe_audio_question():
    """Transcribe uploaded audio for questions ONLY (live recording from Q&A)"""
    # Check if transcriber is available
    if not transcriber:
        return jsonify({'error': 'Transcriber not available. Please check server logs.'}), 500
    
    try:
        file = request.files.get('file')
        if not file or not file.filename:
            return jsonify({'error': 'No audio file uploaded'}), 400
        
        print(f"🎤 Transcribing question audio: {file.filename}")
        
        # Use the transcriber's built-in method for handling uploaded files
        transcribed_text = transcriber.transcribe(file)
        
        # Check if transcription was successful
        if transcribed_text.startswith("Error"):
            return jsonify({'error': transcribed_text}), 500
        
        if not transcribed_text or len(transcribed_text.strip()) < 2:
            return jsonify({'error': 'Could not transcribe audio. Please try speaking more clearly.'}), 400
        
        return jsonify({
            'text': transcribed_text,
            'success': True
        })
                
    except Exception as e:
        print(f"❌ Error transcribing audio: {e}")
        return jsonify({'error': f'Transcription failed: {str(e)}'}), 500

# Debug and health check routes
@app.route('/debug')
def debug():
    """Debug route to check file structure and agent status"""
    import glob
    
    files = {
        'templates': glob.glob('templates/*'),
        'static_css': glob.glob('static/css/*'),
        'static_js': glob.glob('static/js/*'),
        'static_images': glob.glob('static/images/*'),
        'agents': glob.glob('agents/*')
    }
    
    agent_status = {
        'document_processor': doc_processor is not None,
        'summarizer': summarizer is not None,
        'transcriber': transcriber is not None,
        'qa_agent_session_based': True,  # Always True since we create on-demand
        'all_agents_ready': all_agents_ready
    }
    
    env_status = {
        'openai_api_key_set': bool(os.getenv('OPENAI_API_KEY')),
        'upload_folder_exists': os.path.exists(app.config['UPLOAD_FOLDER']),
        'static_audio_exists': os.path.exists('static/audio')
    }
    
    # QA Agent specific debugging
    qa_status = {}
    if qa_agent:
        try:
            qa_status = session_qa.get_status()
        except Exception as e:
            qa_status = {'error': str(e)}
    
    return jsonify({
        'files': files,
        'agents': agent_status,
        'environment': env_status,
        'qa_status': qa_status,
        'available_summary_levels': summarizer.get_available_levels() if summarizer else None
    })

@app.route('/api/qa-debug', methods=['GET'])
def qa_debug():
    """Specific debugging endpoint for Q&A functionality"""
    session_qa = get_session_qa_agent()
    if not session_qa:
        return jsonify({'error': 'QA agent not initialized'}), 500
    
    try:
        status = session_qa.get_status()
        
        # Check file system
        vector_file_exists = os.path.exists(session_qa.vector_store.persist_path)
        file_size = os.path.getsize(session_qa.vector_store.persist_path) if vector_file_exists else 0
        
        return jsonify({
            'session_info': {
                'session_id': session.get('session_id'),
                'created_at': session.get('created_at'),
                'last_qa_access': session.get('last_qa_access'),
                'session_keys': list(session.keys())
            },
            'qa_agent_status': status,
            'ready_for_questions': status.get('ready_for_questions', False),
            'documents_loaded': status.get('documents_count', 0),
            'chunks_available': status.get('chunks_count', 0),
            'vector_store_info': {
                'path': str(session_qa.vector_store.persist_path),
                'file_exists': vector_file_exists,
                'file_size': file_size,
                'vectors_in_memory': len(session_qa.vector_store.vectors),
                'documents_in_memory': len(session_qa.documents)
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user-documents', methods=['GET'])
def get_user_documents():
    """Get list of documents for current user"""
    try:
        session_qa = get_session_qa_agent()
        if not session_qa:
            return jsonify({'error': 'QA agent not initialized'}), 500
        
        user_id = get_user_identifier()
        
        # Get user's documents from vector store metadata
        user_docs = {}
        if hasattr(session_qa.vector_store, 'metadata') and session_qa.vector_store.metadata:
            for metadata in session_qa.vector_store.metadata:
                if metadata.get('user_id') == user_id:
                    doc_id = metadata.get('doc_id')
                    if doc_id and doc_id not in user_docs:
                        user_docs[doc_id] = {
                            'doc_id': doc_id,
                            'title': metadata.get('doc_title', 'Untitled'),
                            'upload_time': metadata.get('upload_time'),
                            'chunk_count': 0
                        }
                    if doc_id in user_docs:
                        user_docs[doc_id]['chunk_count'] += 1
        
        documents = list(user_docs.values())
        # Sort by upload time (most recent first)
        documents.sort(key=lambda x: x.get('upload_time', ''), reverse=True)
        
        return jsonify({
            'documents': documents,
            'total_count': len(documents),
            'user_id': user_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete-document', methods=['DELETE'])
def delete_document():
    """Delete a specific document for current user"""
    try:
        data = request.get_json()
        doc_id = data.get('doc_id')
        
        if not doc_id:
            return jsonify({'error': 'doc_id is required'}), 400
        
        session_qa = get_session_qa_agent()
        if not session_qa:
            return jsonify({'error': 'QA agent not initialized'}), 500
        
        user_id = get_user_identifier()
        
        # Load vector store to ensure we have latest data
        if not hasattr(session_qa.vector_store, 'vectors') or not session_qa.vector_store.vectors:
            session_qa.vector_store.load()
        
        # Check if document belongs to current user and exists
        doc_exists = False
        chunk_count = 0
        if hasattr(session_qa.vector_store, 'metadata'):
            for metadata in session_qa.vector_store.metadata:
                if (metadata.get('user_id') == user_id and 
                    metadata.get('doc_id') == doc_id):
                    doc_exists = True
                    chunk_count += 1
        
        if not doc_exists:
            return jsonify({'error': 'Document not found or access denied'}), 404
        
        # Remove document using existing method
        session_qa._remove_document_by_id(doc_id)
        session_qa.vector_store.save()
        
        print(f"🗑️ Deleted document {doc_id} for user {user_id} ({chunk_count} chunks removed)")
        
        return jsonify({
            'success': True,
            'message': f'Document deleted successfully',
            'doc_id': doc_id,
            'chunks_removed': chunk_count
        })
        
    except Exception as e:
        print(f"❌ Error deleting document: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-multiple-files', methods=['POST'])
def upload_multiple_files():
    """Upload multiple files at once with optimized batch processing"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files uploaded'}), 400
        
        files = request.files.getlist('files')
        if not files or all(file.filename == '' for file in files):
            return jsonify({'error': 'No files selected'}), 400
        
        # Check file count limit
        if len(files) > 5:
            return jsonify({'error': 'Maximum 5 files allowed per upload'}), 400
        
        # Get optional parameters
        summary_level = request.form.get('summary_level', 'standard')
        voice = request.form.get('voice', 'nova')
        
        session_qa = get_session_qa_agent()
        user_id = get_user_identifier()
        
        # Phase 1: Extract and validate all files first
        print("📄 Phase 1: Extracting text from all files...")
        file_data = []
        for file in files:
            if file.filename == '':
                continue
                
            filename = secure_filename(file.filename)
            
            # Check file type
            allowed_extensions = {'.pdf', '.docx', '.txt'}
            file_ext = os.path.splitext(filename.lower())[1]
            if file_ext not in allowed_extensions:
                file_data.append({
                    'filename': filename,
                    'success': False,
                    'error': 'File type not allowed. Supported: PDF, DOCX, TXT'
                })
                continue
            
            try:
                # Save and extract text
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
                file.save(file_path)
                text = doc_processor.extract_text(file_path)
                os.remove(file_path)
                
                if not text or len(text.strip()) < 10:
                    file_data.append({
                        'filename': filename,
                        'success': False,
                        'error': 'Could not extract text from file'
                    })
                    continue
                
                file_data.append({
                    'filename': filename,
                    'text': text,
                    'success': True
                })
                
            except Exception as e:
                file_data.append({
                    'filename': filename,
                    'success': False,
                    'error': str(e)
                })
        
        # Filter successful extractions
        valid_files = [f for f in file_data if f.get('success', False)]
        if not valid_files:
            return jsonify({
                'success': False,
                'results': file_data,
                'successful_uploads': 0,
                'total_files': len(file_data),
                'error': 'No files could be processed'
            })
        
        print(f"✅ Successfully extracted text from {len(valid_files)} files")
        
        # Phase 2: Batch generate summaries
        print("📋 Phase 2: Batch generating summaries...")
        texts_for_summary = [f['text'] for f in valid_files]
        
        # Generate summaries (could be optimized to batch if summarizer supports it)
        for i, file_entry in enumerate(valid_files):
            try:
                summary = summarizer.summarize(file_entry['text'], detail_level=summary_level)
                file_entry['summary'] = summary
            except Exception as e:
                print(f"⚠️ Summary generation failed for {file_entry['filename']}: {e}")
                file_entry['summary'] = f"Summary generation failed: {str(e)}"
        
        # Phase 3: Optimized batch document storage
        print("🔄 Phase 3: Batch storing documents for Q&A...")
        successful_uploads = 0
        
        if session_qa:
            # Load existing vector store once
            if not hasattr(session_qa.vector_store, 'vectors') or not session_qa.vector_store.vectors:
                session_qa.vector_store.load()
            
            # Clean up user documents once
            session_qa._cleanup_user_documents()
            
            # Collect all chunks from all documents for batch embedding
            all_chunks = []
            chunk_metadata = []
            
            for file_entry in valid_files:
                try:
                    # Clean and chunk text
                    cleaned_text = session_qa._clean_text(file_entry['text'])
                    chunks = session_qa._chunk_text(cleaned_text)
                    
                    if chunks:
                        doc_id = str(uuid.uuid4())
                        upload_time = datetime.now().isoformat()
                        
                        # Add document to session
                        document = {
                            'doc_id': doc_id,
                            'user_id': user_id,
                            'text': cleaned_text,
                            'title': file_entry['filename'],
                            'chunks': chunks,
                            'upload_time': upload_time
                        }
                        session_qa.documents.append(document)
                        
                        # Collect chunks for batch processing
                        for chunk_index, chunk in enumerate(chunks):
                            all_chunks.append(chunk)
                            chunk_metadata.append({
                                'user_id': user_id,
                                'doc_id': doc_id,
                                'chunk_index': chunk_index,
                                'title': file_entry['filename'],
                                'doc_title': file_entry['filename'],
                                'upload_time': upload_time,
                                'text': chunk[:100] + '...' if len(chunk) > 100 else chunk
                            })
                        
                        file_entry['qa_stored'] = True
                        file_entry['doc_id'] = doc_id
                        successful_uploads += 1
                    else:
                        file_entry['qa_stored'] = False
                        
                except Exception as e:
                    print(f"❌ Error processing {file_entry['filename']}: {e}")
                    file_entry['qa_stored'] = False
            
            # Batch create embeddings for all chunks at once
            if all_chunks:
                print(f"🚀 Creating embeddings for {len(all_chunks)} chunks in batch...")
                embeddings = session_qa.vector_store.embedder.create_embeddings_batch(all_chunks)
                
                # Add vectors to store with metadata
                for i, (embedding, metadata) in enumerate(zip(embeddings, chunk_metadata)):
                    if embedding:
                        vector = __import__('numpy').array(embedding, dtype=__import__('numpy').float32)
                        vector_id = f"vec_{len(session_qa.vector_store.vectors)}"
                        metadata_with_id = {'id': vector_id, 'text': all_chunks[i], **metadata}
                        
                        session_qa.vector_store.vectors.append(vector)
                        session_qa.vector_store.metadata.append(metadata_with_id)
                
                # Set dimension on first embedding
                if session_qa.vector_store.dimension is None and embeddings:
                    for emb in embeddings:
                        if emb:
                            session_qa.vector_store.dimension = len(emb)
                            break
                
                # Save vector store once
                session_qa.vector_store.save()
                print(f"✅ Batch processing complete: {len(all_chunks)} chunks processed")
        
        # Update results for failed extractions
        results = []
        for file_entry in file_data:
            if file_entry.get('success', False):
                results.append({
                    'filename': file_entry['filename'],
                    'success': True,
                    'summary': file_entry.get('summary', 'Summary not available'),
                    'text_length': len(file_entry.get('text', '')),
                    'qa_stored': file_entry.get('qa_stored', False)
                })
            else:
                results.append({
                    'filename': file_entry['filename'],
                    'success': False,
                    'error': file_entry.get('error', 'Unknown error')
                })
        
        # Generate combined summary if multiple files uploaded successfully
        combined_summary = None
        audio_url = None
        if successful_uploads > 1:
            summaries = [r['summary'] for r in results if r['success'] and 'summary' in r]
            if summaries:
                combined_text = "\n\n---\n\n".join(summaries)
                combined_summary = f"Successfully uploaded {successful_uploads} files with summaries:\n\n" + combined_text
                
                # Generate audio for combined summary
                if transcriber:
                    try:
                        audio_url = transcriber.text_to_speech(combined_summary, voice=voice)
                    except Exception as tts_error:
                        print(f"⚠️ TTS failed: {tts_error}")
        
        return jsonify({
            'success': successful_uploads > 0,
            'results': results,
            'successful_uploads': successful_uploads,
            'total_files': len([f for f in file_data if f.get('filename')]),
            'combined_summary': combined_summary,
            'audio_url': audio_url,
            'user_id': user_id
        })
        
    except Exception as e:
        print(f"❌ Error in multi-file upload: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-question', methods=['POST'])
def test_question():
    """Test endpoint for Q&A debugging"""
    session_qa = get_session_qa_agent()
    if not session_qa:
        return jsonify({'error': 'QA agent not initialized'}), 500
    
    try:
        # Test with a simple question
        test_answer = session_qa.answer_question("What is this document about?")
        status = session_qa.get_status()
        
        return jsonify({
            'test_answer': test_answer,
            'qa_status': status,
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/full-test', methods=['POST'])
def full_test():
    """Comprehensive test of the entire Q&A pipeline"""
    try:
        test_text = "This is a test document about artificial intelligence and machine learning. AI systems can process natural language and help with various tasks. Machine learning algorithms learn from data to make predictions."
        
        results = {
            'step1_summarizer': False,
            'step2_qa_storage': False,
            'step3_qa_retrieval': False,
            'step4_qa_answer': False,
            'errors': []
        }
        
        # Step 1: Test summarizer
        if summarizer:
            try:
                summary = summarizer.summarize(test_text, detail_level='quick')
                results['step1_summarizer'] = True
                results['summary'] = summary[:100] + "..."
            except Exception as e:
                results['errors'].append(f"Summarizer error: {e}")
        
        # Step 2: Test QA storage
        if qa_agent:
            try:
                stored = session_qa.add_document(test_text, "Test Document")
                results['step2_qa_storage'] = stored
                results['qa_status_after_storage'] = session_qa.get_status()
            except Exception as e:
                results['errors'].append(f"QA storage error: {e}")
        
        # Step 3: Test QA retrieval
        if qa_agent:
            try:
                context = session_qa._get_relevant_context("What is this about?")
                results['step3_qa_retrieval'] = len(context) > 0
                results['context_length'] = len(context)
            except Exception as e:
                results['errors'].append(f"QA retrieval error: {e}")
        
        # Step 4: Test full Q&A
        if qa_agent:
            try:
                answer = session_qa.answer_question("What is this document about?")
                results['step4_qa_answer'] = not answer.startswith("Error") and not answer.startswith("No documents")
                results['test_answer'] = answer[:200] + "..."
            except Exception as e:
                results['errors'].append(f"QA answer error: {e}")
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/clear-documents', methods=['POST'])
def clear_documents():
    """Clear all stored documents from Q&A agent"""
    session_qa = get_session_qa_agent()
    if not session_qa:
        return jsonify({'error': 'QA agent not available'}), 500
    
    try:
        session_qa.clear_documents()
        return jsonify({
            'success': True,
            'message': 'All documents cleared',
            'qa_status': session_qa.get_status()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rebuild-vectors', methods=['POST'])
def rebuild_vectors():
    """Force rebuild QA agent vectors"""
    session_qa = get_session_qa_agent()
    if not session_qa:
        return jsonify({'error': 'QA agent not available'}), 500
    
    try:
        print("ℹ️ Checking vector store status...")
        
        # No need to rebuild vectors - using new vector store with automatic persistence
        print("ℹ️ Vector store uses automatic persistence - no manual rebuild needed")
        status = session_qa.get_status()
        
        print(f"✅ Vector store status: {status}")
        
        return jsonify({
            'success': True,
            'message': 'Vector store uses automatic persistence - no rebuild needed',
            'qa_status': status
        })
    except Exception as e:
        print(f"❌ Error rebuilding vectors: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cleanup-audio', methods=['POST'])
def cleanup_audio():
    """Clean up old audio files"""
    if not transcriber:
        return jsonify({'error': 'Transcriber not available'}), 500
    
    try:
        transcriber.cleanup_old_files()
        return jsonify({'success': True, 'message': 'Audio cleanup completed'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/transcriber-debug', methods=['GET'])
def transcriber_debug():
    """Debug endpoint for transcriber functionality"""
    if not transcriber:
        return jsonify({'error': 'Transcriber not initialized'}), 500
    
    try:
        return jsonify({
            'transcriber_ready': True,
            'supported_formats': transcriber.get_supported_formats(),
            'available_voices': transcriber.get_available_voices(),
            'audio_directory_exists': transcriber.audio_dir.exists(),
            'audio_files_count': len(list(transcriber.audio_dir.glob('*.mp3')))
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cleanup-sessions', methods=['POST'])
def cleanup_sessions():
    """Clean up old session files"""
    try:
        cleanup_old_sessions()
        return jsonify({'success': True, 'message': 'Session cleanup completed'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy' if all_agents_ready else 'degraded',
        'agents_ready': all_agents_ready,
        'openai_configured': bool(os.getenv('OPENAI_API_KEY')),
        'session_based_qa': True
    })

if __name__ == '__main__':
    print("🚀 Starting MyAIGist server...")
    print("📁 Static folder:", app.static_folder)
    print("🌐 Visit: http://localhost:8000")
    print("🔧 Debug info: http://localhost:8000/debug")
    print("💚 Health check: http://localhost:8000/health")
    print("📋 Summary levels: Quick, Standard (default), Detailed")
    print("📄 Supported content: Text input, PDF/DOCX/TXT documents")
    print("🎤 Voice features: Live recording for Q&A questions only")
    print(f"🤖 OpenAI API configured: {bool(os.getenv('OPENAI_API_KEY'))}")
    print(f"🔧 All agents ready: {all_agents_ready}")
    
    app.run(debug=True, host='0.0.0.0', port=8000)