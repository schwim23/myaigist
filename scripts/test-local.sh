#!/bin/bash

# Test Local Environment Script
# Usage: ./scripts/test-local.sh [commit_sha]

set -e

# Get commit SHA from parameter or current git
if [ "$1" ]; then
    COMMIT_SHA="$1"
else
    COMMIT_SHA=$(git rev-parse --short HEAD)
fi

echo "🧪 Testing MyAIGist $COMMIT_SHA locally"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "📋 Please create .env file with required environment variables:"
    echo "   OPENAI_API_KEY=your_key_here"
    echo "   OPENAI_MODEL=gpt-4o-mini"
    echo "   OPENAI_EMBED_MODEL=text-embedding-3-small"
    echo "   OPENAI_TTS_MODEL=tts-1"
    echo "   OPENAI_WHISPER_MODEL=whisper-1"
    exit 1
fi

# Check if image exists
if ! docker image inspect myaigist:$COMMIT_SHA > /dev/null 2>&1; then
    echo "❌ Docker image myaigist:$COMMIT_SHA not found!"
    echo "🔄 Run ./scripts/build-and-tag.sh first"
    exit 1
fi

# Kill any existing container
echo "🧹 Cleaning up existing containers..."
docker rm -f myaigist-local 2>/dev/null || true

# Start local container
echo "🚀 Starting local container..."
docker run -d \
  --name myaigist-local \
  -p 8000:8000 \
  --env-file .env \
  myaigist:$COMMIT_SHA

# Wait for container to start
echo "⏳ Waiting for application to start..."
sleep 5

# Test health check
echo "🏥 Testing health check..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -s http://localhost:8000/ > /dev/null; then
        echo "✅ Application is responding!"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        echo "❌ Application failed to start after $max_attempts attempts"
        echo "📋 Container logs:"
        docker logs myaigist-local
        docker rm -f myaigist-local
        exit 1
    fi
    
    echo "   Attempt $attempt/$max_attempts - waiting..."
    sleep 2
    ((attempt++))
done

echo ""
echo "🎉 Local testing environment ready!"
echo "🌐 Application: http://localhost:8000"
echo "📋 Version: $COMMIT_SHA"
echo "🐳 Container: myaigist-local"
echo ""
echo "🧪 Manual testing checklist:"
echo "  ✓ Upload single document"
echo "  ✓ Upload multiple documents"
echo "  ✓ Test audio generation"
echo "  ✓ Test Q&A functionality"
echo "  ✓ Test voice recording"
echo ""
echo "🛑 Stop container: docker rm -f myaigist-local"
echo "📊 View logs: docker logs -f myaigist-local"