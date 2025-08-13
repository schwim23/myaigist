#!/bin/bash

# Full CI/CD Pipeline Script
# Usage: ./scripts/full-deploy.sh

set -e

echo "🚀 MyAIGist Full CI/CD Pipeline"
echo "==============================="

# Get current git status
if ! git diff --quiet HEAD; then
    echo "⚠️  You have uncommitted changes!"
    echo "📋 Please commit your changes before deploying"
    git status --short
    exit 1
fi

COMMIT_SHA=$(git rev-parse --short HEAD)
echo "📋 Current commit: $COMMIT_SHA"

# Step 1: Build and tag
echo ""
echo "🏗️  Step 1: Build and Tag"
echo "========================"
./scripts/build-and-tag.sh

# Step 2: Test locally
echo ""
echo "🧪 Step 2: Local Testing"
echo "======================="
./scripts/test-local.sh $COMMIT_SHA

echo ""
read -p "✅ Local testing passed? Continue to QA? (yes/no): " continue_qa

if [ "$continue_qa" != "yes" ]; then
    echo "❌ Pipeline stopped at local testing"
    docker rm -f myaigist-local 2>/dev/null || true
    exit 1
fi

# Cleanup local test
docker rm -f myaigist-local 2>/dev/null || true

# Step 3: Push to GitHub
echo ""
echo "📤 Step 3: Push to GitHub"
echo "========================"
echo "🔄 Pushing to GitHub..."
git push origin main

# Step 4: Deploy to QA
echo ""
echo "🧪 Step 4: Deploy to QA"
echo "======================"
./scripts/deploy-qa.sh $COMMIT_SHA

echo ""
read -p "✅ QA testing passed? Continue to Production? (yes/no): " continue_prod

if [ "$continue_prod" != "yes" ]; then
    echo "❌ Pipeline stopped at QA testing"
    echo "🧪 QA environment remains available for further testing"
    exit 1
fi

# Step 5: Deploy to Production
echo ""
echo "🚀 Step 5: Deploy to Production"
echo "==============================="
./scripts/deploy-prod.sh $COMMIT_SHA

echo ""
echo "🎉 FULL DEPLOYMENT COMPLETED!"
echo "=============================="
echo "📋 Version: $COMMIT_SHA"
echo "🧪 QA: Available for testing"
echo "🌐 Production: https://myaigist.ai"
echo ""
echo "📊 Monitor deployment:"
echo "  - Production: https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/myaigist-cluster"
echo "  - QA: https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/myaigist-qa-cluster"