# 🧠 MyAIGist - AI-Powered Content Analysis & Q&A

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-success.svg)](https://openai.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**MyAIGist** is a lightweight, intelligent AI-powered assistant that transforms any content into an interactive Q&A experience. Upload documents or paste text to get instant summaries with three detail levels and ask detailed questions using text or voice input.

![MyAIGist Demo](https://via.placeholder.com/800x400/667eea/ffffff?text=MyAIGist+Demo+Screenshot)

---

## ✨ Features

### 📄 **Content Input**
- **Text Input**: Direct text analysis and processing
- **Document Upload**: PDF, DOCX, TXT files with intelligent parsing

### 🎯 **Three-Level AI Summaries**
- **⚡ Quick**: 2-3 key bullet points for fast overview
- **📄 Standard**: Balanced summary with main topics and details (default)
- **📚 Detailed**: Comprehensive analysis with context, insights, and implications

### 💬 **Intelligent Q&A System**
- **Text Questions**: Type questions naturally
- **🎤 Voice Questions**: Live audio recording with browser microphone
- **RAG-Enhanced Answers**: Retrieval-Augmented Generation for accurate responses
- **Audio Responses**: Text-to-speech for accessibility

### 🔊 **Voice Features**
- **Live Voice Recording**: Browser-based microphone recording for questions
- **Auto-Transcription**: Convert speech to text automatically
- **Audio Responses**: Listen to answers with text-to-speech
- **WebM Support**: Handles browser recordings with ffmpeg conversion

### 🎨 **Modern Interface**
- **Responsive Design**: Works perfectly on desktop and mobile
- **Dark Theme**: Beautiful gradient design with glassmorphism
- **Real-time Feedback**: Progress indicators and status updates
- **Smooth Animations**: Professional micro-interactions

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ 
- OpenAI API key
- FFmpeg (optional, for better audio processing)

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/myaigist.git
cd myaigist
```

### 2. Install Dependencies
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 3. Environment Setup
```bash
# Create .env file
cp .env.example .env

# Add your OpenAI API key
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
```

### 4. Run Application
```bash
python main.py
```

🎉 **Visit**: [http://localhost:8000](http://localhost:8000)

---

## 📦 Installation Options

### Option 1: Standard Installation
```bash
pip install -r requirements.txt
```

### Option 2: With FFmpeg (Recommended for voice features)
**macOS:**
```bash
brew install ffmpeg
pip install -r requirements.txt
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install ffmpeg
pip install -r requirements.txt
```

**Windows:**
Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

---

## 🏗 Architecture

### **Agent-Based Design**
- **DocumentProcessor**: Extracts text from PDF, DOCX, TXT files
- **Summarizer**: Multi-level AI summarization with OpenAI GPT
- **Transcriber**: Live audio transcription (Whisper) and text-to-speech
- **QAAgent**: RAG-powered question answering with semantic search

### **Tech Stack**
- **Backend**: Flask (Python web framework)
- **Frontend**: Vanilla JavaScript with AJAX
- **AI/ML**: OpenAI (GPT-4, GPT-3.5, Whisper, TTS)
- **Vector Search**: Scikit-learn cosine similarity
- **Audio**: Web Audio API + MediaRecorder
- **Styling**: Modern CSS with responsive design

### **Project Structure**
```
myaigist/
├── main.py                    # Flask server with API routes
├── requirements.txt           # Python dependencies
├── .env                      # Environment variables
├── templates/
│   └── index.html            # Main application interface
├── static/
│   ├── css/styles.css        # Responsive styling
│   ├── js/app.js            # Frontend JavaScript
│   └── audio/               # Generated audio files
├── agents/                   # AI agent modules
│   ├── document_processor.py # Document text extraction
│   ├── summarizer.py        # Multi-level summarization
│   ├── transcriber.py       # Audio processing
│   └── qa_agent.py          # RAG Q&A system
└── uploads/                  # Temporary file storage
```

---

## 🎯 Usage Examples

### 1. **Document Analysis**
```bash
1. Upload a PDF research paper
2. Select "Detailed" summary level
3. Get comprehensive analysis with insights
4. Ask: "What are the main findings?"
5. Get intelligent answer with source attribution
```

### 2. **Voice-Powered Q&A**
```bash
1. Paste article text
2. Use "Standard" summary (default)
3. Click microphone button
4. Ask question verbally: "What are the implications?"
5. Get both text and audio response
```

### 3. **Text Document Processing**
```bash
1. Upload Word document or PDF
2. Get "Quick" summary of key points
3. Ask: "What decisions were made?"
4. Use voice or text to ask follow-up questions
```

---

## 🔧 Configuration

### **Environment Variables (.env)**
```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
FLASK_ENV=development
FLASK_DEBUG=true
MAX_CONTENT_LENGTH=52428800  # 50MB
```

### **Summary Levels**
Customize in `agents/summarizer.py`:
```python
# Quick: 2-3 bullet points, 300 tokens
# Standard: 4-5 key points, 600 tokens  
# Detailed: 6+ sections, 1200 tokens
```

### **Audio Settings**
Configure in `agents/transcriber.py`:
```python
# Whisper model: whisper-1
# TTS voice: nova (alloy, echo, fable, onyx, shimmer)
# Audio format: MP3, WebM support
```

---

## 🚀 Deployment

### **Local Development**
```bash
python main.py  # Runs on http://localhost:8000
```

### **Production Deployment**

#### **Option 1: Simple Production Server**
```bash
# Install production WSGI server
pip install gunicorn

# Run with Gunicorn
gunicorn --bind 0.0.0.0:8000 main:app
```

#### **Option 2: Docker Deployment**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "main:app"]
```

#### **Option 3: Cloud Deployment (AWS/GCP/Azure)**
1. Set environment variables in cloud console
2. Deploy using cloud-specific Python app services
3. Configure domain and SSL certificates
4. Set up file storage for uploads

---

## 🔍 API Documentation

### **Process Content**
```http
POST /api/process-content
Content-Type: application/json

{
  "type": "text",
  "text": "Your content here",
  "summary_level": "standard"  // quick, standard, detailed
}
```

### **Ask Question**
```http
POST /api/ask-question
Content-Type: application/json

{
  "question": "What are the main points?"
}
```

### **Transcribe Audio (Q&A Voice Recording Only)**
```http
POST /api/transcribe-audio
Content-Type: multipart/form-data

file: <recorded_audio_blob>
```

---

## 🧪 Testing

### **Run Basic Tests**
```bash
# Test API endpoints
curl -X POST http://localhost:8000/api/process-content \
  -H "Content-Type: application/json" \
  -d '{"type":"text","text":"Test content","summary_level":"quick"}'

# Test file upload
curl -X POST http://localhost:8000/api/process-content \
  -F "file=@document.pdf" \
  -F "type=file" \
  -F "summary_level=standard"
```

### **Browser Compatibility**
- ✅ Chrome 80+
- ✅ Firefox 70+  
- ✅ Safari 13+
- ✅ Edge 80+

**Note**: Microphone features require HTTPS in production.

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### **Development Setup**
```bash
git clone https://github.com/yourusername/myaigist.git
cd myaigist
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### **Code Style**
- Follow PEP 8 for Python code
- Use meaningful variable names and docstrings
- Add comments for complex logic
- Test with multiple file types and browsers

### **Pull Request Process**
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes with tests
4. Commit: `git commit -m 'Add amazing feature'`
5. Push: `git push origin feature/amazing-feature`
6. Open a Pull Request

---

## 🐛 Troubleshooting

### **Common Issues**

#### **Microphone Not Working**
```bash
# Check browser permissions
# Chrome: Settings > Privacy > Microphone
# Firefox: about:preferences#privacy

# Test microphone access
navigator.mediaDevices.getUserMedia({audio:true})
```

#### **Voice Transcription Fails**
```bash
# Install/check FFmpeg (optional but recommended)
ffmpeg -version

# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
```

#### **OpenAI API Errors**
```bash
# Verify API key in .env file
echo $OPENAI_API_KEY

# Check API usage at: https://platform.openai.com/usage
# Ensure sufficient credits and correct permissions
```

#### **File Upload Issues**
```bash
# Check file size (50MB limit)
# Supported formats: PDF, DOCX, TXT
# Verify upload directory permissions
```

### **Debug Mode**
```bash
# Enable debug logging
export FLASK_DEBUG=true
python main.py

# Check debug endpoint
curl http://localhost:8000/debug
```

---

## 📊 Performance

### **Response Times** (typical)
- Text processing: 2-5 seconds
- Document processing: 3-10 seconds (depends on size)
- Q&A responses: 2-8 seconds
- Voice recording: Real-time

### **Supported File Sizes**
- Documents: Up to 50MB
- Text input: Up to 50,000 characters

### **Optimization Tips**
- Use "Quick" summaries for faster processing
- Keep voice recordings short for better transcription
- Use supported file formats for better performance

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🌟 Acknowledgments

- **OpenAI** for providing powerful language models and APIs
- **Flask** for the excellent Python web framework  
- **Web Audio API** for browser-based audio recording
- **Scikit-learn** for efficient vector similarity search
- **FFmpeg** for robust audio processing
- **Modern CSS** community for design inspiration

---

## 📞 Support

- **🐛 Bug Reports**: [GitHub Issues](https://github.com/yourusername/myaigist/issues)
- **💡 Feature Requests**: [GitHub Discussions](https://github.com/yourusername/myaigist/discussions)
- **📖 Documentation**: Check project files and code comments
- **💬 Questions**: Open a discussion or issue

---

## 🚀 Roadmap

### **Current Version: v1.0**
- ✅ Text and document input
- ✅ Three-level AI summaries  
- ✅ Voice recording for questions
- ✅ RAG-powered Q&A
- ✅ Modern responsive UI

### **Upcoming Features**
- 🔄 Streaming responses for real-time text generation
- 📤 Export summaries and Q&A sessions to PDF/Markdown
- 🔗 Share processed content with others
- 🎥 YouTube URL integration for video analysis
- 📊 Analytics dashboard for usage insights
- 💾 Session save/restore functionality
- 🌐 Multi-language support
- 🔌 REST API for third-party integrations

### **Future Enhancements**
- 💬 Multi-document collection analysis
- 🤖 Custom AI model fine-tuning
- ☁️ Cloud storage integration
- 🔒 Enterprise authentication (SSO)
- 📱 Native mobile apps

---

**⭐ If MyAIGist helps you work smarter, please star the repository and share it with others!**

*Built with ❤️ for researchers, professionals, and anyone who wants to have intelligent conversations with their content.*