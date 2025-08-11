# 🧠 MyAIGist - AI-Powered Content Analysis & Q&A

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.2+-green.svg)](https://flask.palletsprojects.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-success.svg)](https://openai.com/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**MyAIGist** is an intelligent AI-powered assistant that transforms any content into an interactive Q&A experience using **real semantic search with OpenAI embeddings**. Upload documents or paste text to get instant multi-level summaries and ask detailed questions using text or voice input with Google Analytics tracking.

![MyAIGist Demo](https://via.placeholder.com/800x400/667eea/ffffff?text=MyAIGist+Demo+Screenshot)

---

## ✨ Latest Features (v2.0)

### 🎯 **Real Semantic Search & RAG**
- **OpenAI Embeddings**: True semantic understanding with `text-embedding-3-small`
- **Vector Store**: Container-friendly persistence with numpy + pickle
- **Advanced RAG**: Retrieval-Augmented Generation with cosine similarity
- **Smart Chunking**: Intelligent text segmentation for better context retrieval

### 📄 **Content Input & Processing**
- **Text Input**: Direct text analysis and processing
- **Document Upload**: PDF, DOCX, TXT files with intelligent parsing
- **Smart Parsing**: Extracts clean text from complex document formats

### 🎯 **Three-Level AI Summaries**
- **⚡ Quick**: 2-3 key bullet points (300 tokens) for fast overview
- **📄 Standard**: Balanced summary with main topics (600 tokens) - default
- **📚 Detailed**: Comprehensive analysis with insights (1200 tokens)

### 💬 **Advanced Q&A System**
- **Semantic Search**: Find relevant content using meaning, not just keywords
- **Context-Aware**: Retrieves most relevant document chunks for answers
- **Text & Voice**: Type questions or use microphone recording
- **Audio Responses**: Text-to-speech with configurable voices

### 🔊 **Voice Features**
- **Live Recording**: Browser-based microphone with real-time feedback
- **Auto-Transcription**: Whisper model converts speech to text
- **Audio Playback**: Listen to generated answers with TTS
- **Multiple Voices**: Choose from 6 different AI voices

### 📊 **Analytics & Tracking**
- **Google Analytics**: Track website visits and user interactions
- **Event Tracking**: Monitor content summarization and question events
- **Performance Metrics**: Response times and usage statistics

### 🐳 **Container & Cloud Ready**
- **Docker Support**: Full containerization with health checks
- **Docker Compose**: One-command deployment setup  
- **AWS Fargate Ready**: Optimized for serverless container deployment
- **Persistent Storage**: Vector embeddings survive container restarts

### 🎨 **Modern Interface**
- **Responsive Design**: Perfect on desktop, tablet, and mobile
- **Dark Theme**: Beautiful gradient design with glassmorphism
- **Real-time Feedback**: Progress indicators and status updates
- **Smooth Animations**: Professional micro-interactions

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ 
- OpenAI API key
- FFmpeg (optional, for better audio processing)
- Docker (optional, for containerized deployment)

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/myaigist.git
cd myaigist
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your keys
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBED_MODEL=text-embedding-3-small
OPENAI_TTS_MODEL=tts-1
OPENAI_WHISPER_MODEL=whisper-1
GA_MEASUREMENT_ID=G-XXXXXXXXX  # optional
```

### 3. Installation Options

#### Option A: Standard Python Installation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

#### Option B: Docker Deployment (Recommended)
```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t myaigist .
docker run -p 8000:8000 --env-file .env myaigist
```

🎉 **Visit**: [http://localhost:8000](http://localhost:8000)

---

## 🏗 Architecture

### **AI Agent System**
- **DocumentProcessor**: Extracts text from PDF, DOCX, TXT files
- **Summarizer**: Multi-level AI summarization with configurable models
- **VectorStore**: Semantic embeddings with persistence for containers
- **Embedder**: OpenAI embedding generation with batch support
- **Transcriber**: Audio transcription (Whisper) and text-to-speech
- **QAAgent**: RAG-powered Q&A with semantic similarity search

### **Tech Stack**
- **Backend**: Flask (Python web framework) with Gunicorn
- **AI/ML**: OpenAI (GPT-4o-mini, Whisper, TTS, Embeddings)
- **Vector Search**: OpenAI embeddings + numpy cosine similarity
- **Audio**: Web Audio API + MediaRecorder
- **Analytics**: Google Analytics 4 with event tracking
- **Deployment**: Docker + Docker Compose + AWS Fargate ready
- **Frontend**: Vanilla JavaScript with modern CSS

### **Updated Project Structure**
```
myaigist/
├── main.py                    # Flask server with API routes
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container configuration
├── docker-compose.yml         # Multi-service deployment
├── .env                      # Environment variables
├── templates/
│   └── index.html            # Main app with Google Analytics
├── static/
│   ├── css/styles.css        # Responsive styling
│   ├── js/app.js            # Frontend with GA tracking
│   └── audio/               # Generated TTS audio files
├── agents/                   # AI agent modules
│   ├── openai_client.py     # Centralized OpenAI client
│   ├── document_processor.py # Document text extraction
│   ├── summarizer.py        # Multi-level summarization
│   ├── embeddings.py        # OpenAI embedding generation
│   ├── vector_store.py      # Container-friendly vector storage
│   ├── transcriber.py       # Audio processing (Whisper/TTS)
│   ├── tts.py               # Text-to-speech agent
│   └── qa_agent.py          # Semantic RAG Q&A system
├── data/                     # Persistent vector storage
│   └── vector_store.pkl     # Embedding persistence
└── uploads/                  # Temporary file storage
```

---

## 🔧 Configuration

### **Environment Variables (.env)**
```bash
# Required - OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini                    # Chat model
OPENAI_EMBED_MODEL=text-embedding-3-small  # Embedding model  
OPENAI_TTS_MODEL=tts-1                      # Text-to-speech model
OPENAI_WHISPER_MODEL=whisper-1              # Speech-to-text model

# Optional - Analytics & Monitoring  
GA_MEASUREMENT_ID=G-XXXXXXXXX               # Google Analytics
AWS_REGION=us-east-1                        # CloudWatch region
CW_LOG_GROUP=/myaigist/llm                  # CloudWatch logs

# Optional - Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=false
MAX_CONTENT_LENGTH=52428800                 # 50MB file limit
```

### **Model Configuration**
All AI models are now configurable via environment variables:
- **Chat Model**: `gpt-4o-mini` (configurable)
- **Embeddings**: `text-embedding-3-small` (1536 dimensions)  
- **Voice**: 6 different TTS voices available
- **Transcription**: Whisper model for speech-to-text

### **Vector Store Settings**
```python
# Container-friendly persistence
VECTOR_STORE_PATH = "data/vector_store.pkl"
SIMILARITY_THRESHOLD = 0.1  # Minimum semantic similarity
TOP_K_CHUNKS = 3           # Number of chunks per query
```

---

## 🐳 Docker Deployment

### **Docker Compose (Recommended)**
```yaml
# docker-compose.yml
services:
  myaigist:
    build: .
    container_name: myaigist-app
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_MODEL=${OPENAI_MODEL}
      - OPENAI_EMBED_MODEL=${OPENAI_EMBED_MODEL}
      - GA_MEASUREMENT_ID=${GA_MEASUREMENT_ID}
    volumes:
      - ./uploads:/app/uploads
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### **AWS Fargate Deployment**
The application is optimized for serverless container deployment:

1. **Build and push to ECR**:
```bash
# Build for production
docker build -t myaigist .

# Tag for ECR
docker tag myaigist:latest your-account.dkr.ecr.region.amazonaws.com/myaigist:latest

# Push to ECR
docker push your-account.dkr.ecr.region.amazonaws.com/myaigist:latest
```

2. **Deploy to Fargate**:
- Uses persistent EFS storage for vector embeddings
- Environment variables managed through ECS task definition
- Auto-scaling based on CPU/memory usage
- Health checks with automatic container replacement

---

## 📊 Analytics & Tracking

### **Google Analytics Integration**
The application now includes comprehensive analytics:

```javascript
// Automatic tracking
- Page views and session duration
- Content summarization events (with detail level)
- Question asking events (with question length)
- Audio feature usage
- Error events and user interactions
```

### **Event Examples**
```javascript
// Content summarized
gtag('event', 'content_summarized', {
  content_type: 'text|file',
  summary_level: 'quick|standard|detailed',
  has_audio: true|false
});

// Question asked  
gtag('event', 'question_asked', {
  question_length: 42,
  has_audio_response: true|false
});
```

---

## 🎯 Usage Examples

### 1. **Document Analysis with Semantic Search**
```bash
1. Upload a PDF research paper (up to 50MB)
2. Select "Detailed" summary level  
3. Get comprehensive analysis with semantic understanding
4. Ask: "What methodology was used?"
5. Get precise answers from most relevant document sections
```

### 2. **Voice-Powered Q&A**
```bash
1. Paste article text or upload document
2. Use "Standard" summary (default)
3. Click microphone button and ask: "What are the implications?"
4. Get both text and audio response with source attribution
5. All interactions tracked in Google Analytics
```

### 3. **Container-Based Deployment**
```bash
1. Set environment variables in .env file
2. Run: docker-compose up --build
3. Application starts with persistent vector storage
4. Upload documents - embeddings survive container restarts
5. Scale horizontally with load balancer
```

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

Response:
{
  "success": true,
  "summary": "Generated summary...",
  "audio_url": "/static/audio/speech_123.mp3",
  "qa_stored": true,
  "embedding_stats": {
    "chunks_created": 5,
    "vectors_stored": 5
  }
}
```

### **Ask Question (Semantic RAG)**
```http
POST /api/ask-question  
Content-Type: application/json

{
  "question": "What are the main findings?"
}

Response:
{
  "success": true,
  "answer": "Based on the document analysis...",
  "audio_url": "/static/audio/answer_456.mp3", 
  "sources": [
    {
      "similarity": 0.89,
      "text_preview": "The study found that...",
      "document_title": "Research Paper"
    }
  ]
}
```

### **Transcribe Audio**
```http
POST /api/transcribe-audio
Content-Type: multipart/form-data

file: <recorded_audio_blob>

Response:
{
  "success": true,
  "transcription": "What are the key insights from this document?"
}
```

---

## 🧪 Testing & Development

### **Run Tests**
```bash
# Test semantic search
curl -X POST http://localhost:8000/api/process-content \
  -H "Content-Type: application/json" \
  -d '{"type":"text","text":"AI will transform how we work by automating routine tasks","summary_level":"quick"}'

# Test embedding-based Q&A
curl -X POST http://localhost:8000/api/ask-question \
  -H "Content-Type: application/json" \
  -d '{"question":"How will AI change work?"}'
```

### **Vector Store Debugging**
```bash
# Check vector store status
GET /api/status

# Response includes embedding statistics
{
  "documents_count": 3,
  "chunks_count": 15,
  "embedding_dimension": 1536,
  "memory_usage_mb": 2.4
}
```

---

## 🚀 Performance & Scaling

### **Response Times** (typical)
- Text processing with embeddings: 3-8 seconds
- Document processing: 5-15 seconds (depends on size and chunks)
- Semantic Q&A: 2-6 seconds
- Voice transcription: 1-3 seconds

### **Memory Usage**
- Base application: ~150MB
- Vector storage: ~1-2MB per 1000 document chunks
- Audio files: Auto-cleanup after 24 hours

### **Container Scaling**
```yaml
# ECS Service Configuration
cpu: 512      # 0.5 vCPU
memory: 1024  # 1GB RAM
min_capacity: 1
max_capacity: 10
target_cpu_utilization: 70%
```

---

## 🔒 Security & Privacy

### **Data Handling**
- Documents processed in-memory, deleted after processing
- Embeddings stored locally (no external vector database)
- Audio files auto-deleted after 24 hours
- No user data sent to third-parties except OpenAI API

### **API Security**
- CORS configured for production domains
- File upload validation and size limits
- Input sanitization for all user content

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🌟 Acknowledgments

- **OpenAI** for providing powerful language models, embeddings, and APIs
- **Flask** for the excellent Python web framework  
- **Google Analytics** for comprehensive user behavior tracking
- **Docker** for containerization and deployment flexibility
- **NumPy** for efficient vector operations and similarity calculations
- **Modern CSS** community for design inspiration

---

## 📞 Support

- **🐛 Bug Reports**: [GitHub Issues](https://github.com/yourusername/myaigist/issues)
- **💡 Feature Requests**: [GitHub Discussions](https://github.com/yourusername/myaigist/discussions)
- **📖 Documentation**: Check project files and code comments
- **💬 Questions**: Open a discussion or issue

---

## 🚀 Roadmap

### **Current Version: v2.0** ✅
- ✅ Real semantic search with OpenAI embeddings
- ✅ Container-ready vector storage with persistence
- ✅ Configurable AI models via environment variables  
- ✅ Google Analytics integration with event tracking
- ✅ Docker + Docker Compose deployment
- ✅ AWS Fargate optimization

### **Upcoming Features: v2.1** 🔄
- 🔄 Streaming responses for real-time text generation
- 🔄 Multiple document collections and management
- 🔄 Enhanced analytics dashboard 
- 🔄 API rate limiting and authentication
- 🔄 Batch document processing

### **Future Enhancements: v3.0** 🔮
- 💬 Multi-document cross-referencing and analysis
- 🤖 Custom embedding models and fine-tuning
- ☁️ S3/MinIO integration for large file storage
- 🔒 Enterprise SSO and user management
- 📱 Progressive Web App (PWA) support
- 🌐 Multi-language document processing

---

**⭐ If MyAIGist helps you work smarter with true semantic understanding, please star the repository and share it with others!**

*Built with ❤️ for researchers, professionals, and anyone who wants to have intelligent conversations with their content using real AI embeddings.*