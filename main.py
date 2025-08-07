from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

# Import our agents
from agents.document_processor import DocumentProcessor
from agents.summarizer import Summarizer  
from agents.transcriber import Transcriber
from agents.qa_agent import QAAgent

# Create Flask app with explicit static folder configuration
app = Flask(__name__, 
            static_folder='static',
            static_url_path='/static')

app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/audio', exist_ok=True)

# Initialize agents
try:
    doc_processor = DocumentProcessor()
    summarizer = Summarizer()
    transcriber = Transcriber()
    qa_agent = QAAgent()
    print("✅ All agents initialized successfully")
except Exception as e:
    print(f"❌ Error initializing agents: {e}")

@app.route('/')
def index():
    """Serve the main application page"""
    print("📄 Serving index.html")
    return render_template('index.html')

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
                
                # Process text with specified summary level
                summary = summarizer.summarize(text, detail_level=summary_level)
                audio_url = transcriber.text_to_speech(summary)
                
                # Store for QA
                qa_agent.add_document(text, 'User Text')
                
                return jsonify({
                    'summary': summary,
                    'audio_url': audio_url,
                    'summary_level': summary_level,
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
            
            # Save uploaded file
            filename = secure_filename(file.filename)
            file_id = str(uuid.uuid4())
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{filename}")
            file.save(file_path)
            
            try:
                # Extract text from document
                text = doc_processor.extract_text(file_path)
                
                # Generate summary with specified level
                summary = summarizer.summarize(text, detail_level=summary_level)
                audio_url = transcriber.text_to_speech(summary)
                
                # Store for QA
                qa_agent.add_document(text, filename)
                
                return jsonify({
                    'summary': summary,
                    'audio_url': audio_url,
                    'summary_level': summary_level,
                    'success': True
                })
                
            finally:
                # Clean up uploaded file
                if os.path.exists(file_path):
                    os.remove(file_path)
    
    except Exception as e:
        print(f"❌ Error processing content: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ask-question', methods=['POST'])
def ask_question():
    """Handle Q&A requests"""
    try:
        data = request.get_json()
        question = data.get('question')
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        print(f"❓ Processing question: {question[:50]}...")
        
        # Get answer from QA agent
        answer = qa_agent.answer_question(question)
        
        # Generate audio for answer
        audio_url = transcriber.text_to_speech(answer)
        
        return jsonify({
            'answer': answer,
            'audio_url': audio_url,
            'success': True
        })
        
    except Exception as e:
        print(f"❌ Error answering question: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/transcribe-audio', methods=['POST'])
def transcribe_audio_question():
    """Transcribe uploaded audio for questions ONLY (live recording from Q&A)"""
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'No audio file uploaded'}), 400
        
        print(f"🎤 Transcribing question audio: {file.filename}")
        
        # Save and transcribe audio file
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{filename}")
        file.save(file_path)
        
        try:
            text = transcriber.transcribe_audio(file_path)
            return jsonify({
                'text': text,
                'success': True
            })
        finally:
            # Clean up uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)
                
    except Exception as e:
        print(f"❌ Error transcribing audio: {e}")
        return jsonify({'error': str(e)}), 500

# Debug route to check static files
@app.route('/debug')
def debug():
    """Debug route to check file structure"""
    import glob
    
    files = {
        'templates': glob.glob('templates/*'),
        'static_css': glob.glob('static/css/*'),
        'static_js': glob.glob('static/js/*'),
        'static_images': glob.glob('static/images/*')
    }
    
    return jsonify(files)

if __name__ == '__main__':
    print("🚀 Starting MyAIGist server...")
    print("📁 Static folder:", app.static_folder)
    print("🌐 Visit: http://localhost:8000")
    print("🔧 Debug info: http://localhost:8000/debug")
    print("📋 Summary levels: Quick, Standard (default), Detailed")
    print("📄 Supported content: Text input, PDF/DOCX/TXT documents")
    print("🎤 Voice features: Live recording for Q&A questions only")
    
    app.run(debug=True, host='0.0.0.0', port=8000)