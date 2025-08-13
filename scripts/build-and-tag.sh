#!/bin/bash

# Build and Tag Script
# Usage: ./scripts/build-and-tag.sh

set -e

# Get the current git commit SHA
COMMIT_SHA=$(git rev-parse HEAD)
SHORT_SHA=$(git rev-parse --short HEAD)

echo "🔄 Building MyAIGist Docker image for commit $SHORT_SHA"

# Build the Docker image with commit SHA tag
docker build -t myaigist:$SHORT_SHA .
docker tag myaigist:$SHORT_SHA myaigist:latest

echo "✅ Successfully built and tagged myaigist:$SHORT_SHA"
echo "🏷️  Also tagged as myaigist:latest"

# Show built images
echo "📦 Available images:"
docker images myaigist --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedSince}}\t{{.Size}}"

echo ""
echo "🚀 Next steps:"
echo "  - Test locally: docker run -p 8000:8000 --env-file .env myaigist:$SHORT_SHA"
echo "  - Deploy to QA: ./scripts/deploy-qa.sh $SHORT_SHA"
echo "  - Deploy to Prod: ./scripts/deploy-prod.sh $SHORT_SHA"