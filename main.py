from flask import Flask, render_template, request, jsonify, send_from_directory, session
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
import uuid
import secrets

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

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/audio', exist_ok=True)

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

# Session-based QA agent management
def get_session_qa_agent():
    """Get or create a QA agent for the current session"""
    if 'session_id' not in session:
        session['session_id'] = secrets.token_hex(8)
        print(f"🆔 Created new session: {session['session_id']}")
    
    session_id = session['session_id']
    
    try:
        # Import here to avoid circular imports
        from agents.qa_agent import QAAgent
        
        # Create session-specific QA agent with custom vector store path
        qa = QAAgent(session_id=session_id)
        print(f"✅ QA Agent ready for session: {session_id}")
        return qa
    except Exception as e:
        print(f"❌ Error creating session QA agent: {e}")
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
                        audio_url = transcriber.text_to_speech(summary)
                        print(f"🔊 Generated audio: {audio_url}")
                    except Exception as e:
                        print(f"⚠️  Audio generation failed: {e}")
                
                # Store for QA with session-based agent - WITH DEBUGGING
                qa_success = False
                session_qa = get_session_qa_agent()
                if session_qa:
                    try:
                        print(f"💾 Storing text for Q&A (length: {len(text)})")
                        qa_success = session_qa.add_document(text, 'User Text Input')
                        print(f"✅ QA storage result: {qa_success}")
                        
                        # Vector store automatically saves after adding documents
                        print("✅ Document processed and vectors stored")
                        
                        # Verify storage worked
                        status = session_qa.get_status()
                        print(f"📊 QA Status after storage: {status}")
                        
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
                        audio_url = transcriber.text_to_speech(summary)
                        print(f"🔊 Generated audio: {audio_url}")
                    except Exception as e:
                        print(f"⚠️  Audio generation failed: {e}")
                
                # Store for QA with session-based agent - WITH DEBUGGING
                qa_success = False
                session_qa = get_session_qa_agent()
                if session_qa:
                    try:
                        print(f"💾 Storing document '{filename}' for Q&A (length: {len(text)})")
                        qa_success = session_qa.add_document(text, filename)
                        print(f"✅ QA storage result: {qa_success}")
                        
                        # Vector store automatically saves after adding documents
                        print("✅ Document processed and vectors stored")
                        
                        # Verify storage worked
                        status = session_qa.get_status()
                        print(f"📊 QA Status after storage: {status}")
                        
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
    # Get session-based QA agent
    session_qa = get_session_qa_agent()
    if not session_qa:
        return jsonify({'error': 'Q&A agent not available. Please check server logs.'}), 500
    
    try:
        data = request.get_json()
        question = data.get('question')
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        print(f"❓ Processing question: {question[:50]}...")
        
        # Debug QA agent status before answering
        status = session_qa.get_status()
        print(f"📊 QA Agent Status: {status}")
        
        if not status.get('ready_for_questions', False):
            return jsonify({
                'error': 'No documents available for Q&A. Please upload a document first.',
                'qa_status': status
            }), 400
        
        # Get answer from QA agent
        answer = session_qa.answer_question(question)
        
        # Generate audio for answer if transcriber is available
        audio_url = None
        if transcriber:
            try:
                audio_url = transcriber.text_to_speech(answer)
                print(f"🔊 Generated audio for answer: {audio_url}")
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
        return jsonify({
            'qa_agent_status': status,
            'ready_for_questions': status.get('ready_for_questions', False),
            'documents_loaded': status.get('documents_count', 0),
            'chunks_available': status.get('chunks_count', 0)
        })
    except Exception as e:
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