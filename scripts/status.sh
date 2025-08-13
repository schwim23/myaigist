#!/bin/bash

# Environment Status Script
# Usage: ./scripts/status.sh

set -e

echo "🔍 MyAIGist Environment Status"
echo "==============================="

# Production Status
echo ""
echo "🚀 PRODUCTION"
echo "============="
PROD_STATUS=$(aws ecs describe-services --cluster myaigist-cluster --services myaigist-service --region us-east-1 --query 'services[0].deployments[0].rolloutState' --output text 2>/dev/null || echo "ERROR")
PROD_RUNNING=$(aws ecs describe-services --cluster myaigist-cluster --services myaigist-service --region us-east-1 --query 'services[0].runningCount' --output text 2>/dev/null || echo "0")
PROD_DESIRED=$(aws ecs describe-services --cluster myaigist-cluster --services myaigist-service --region us-east-1 --query 'services[0].desiredCount' --output text 2>/dev/null || echo "0")

echo "Status: $PROD_STATUS"
echo "Tasks: $PROD_RUNNING/$PROD_DESIRED running"
echo "URL: https://myaigist.ai"

# Test production health
if curl -s -o /dev/null -w "%{http_code}" https://myaigist.ai | grep -q "200"; then
    echo "Health: ✅ Responding"
else
    echo "Health: ❌ Not responding"
fi

# QA Status
echo ""
echo "🧪 QA ENVIRONMENT"
echo "================="
QA_STATUS=$(aws ecs describe-services --cluster myaigist-qa-cluster --services myaigist-qa-service --region us-east-1 --query 'services[0].deployments[0].rolloutState' --output text 2>/dev/null || echo "ERROR")
QA_RUNNING=$(aws ecs describe-services --cluster myaigist-qa-cluster --services myaigist-qa-service --region us-east-1 --query 'services[0].runningCount' --output text 2>/dev/null || echo "0")
QA_DESIRED=$(aws ecs describe-services --cluster myaigist-qa-cluster --services myaigist-qa-service --region us-east-1 --query 'services[0].desiredCount' --output text 2>/dev/null || echo "0")

echo "Status: $QA_STATUS"
echo "Tasks: $QA_RUNNING/$QA_DESIRED running"

# Get QA IP if running
if [ "$QA_RUNNING" -gt 0 ]; then
    TASK_ARN=$(aws ecs list-tasks --cluster myaigist-qa-cluster --service-name myaigist-qa-service --region us-east-1 --query 'taskArns[0]' --output text 2>/dev/null || echo "")
    if [ "$TASK_ARN" != "" ] && [ "$TASK_ARN" != "None" ]; then
        ENI_ID=$(aws ecs describe-tasks --cluster myaigist-qa-cluster --tasks $TASK_ARN --region us-east-1 --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text 2>/dev/null || echo "")
        if [ "$ENI_ID" != "" ]; then
            QA_IP=$(aws ec2 describe-network-interfaces --network-interface-ids $ENI_ID --region us-east-1 --query 'NetworkInterfaces[0].Association.PublicIp' --output text 2>/dev/null || echo "")
            echo "URL: http://$QA_IP:8000"
            
            # Test QA health
            if curl -s -o /dev/null -w "%{http_code}" "http://$QA_IP:8000" --max-time 10 | grep -q "200"; then
                echo "Health: ✅ Responding"
            else
                echo "Health: ❌ Not responding"
            fi
        fi
    fi
else
    echo "URL: Not available (no running tasks)"
    echo "Health: ❌ Not running"
fi

# Git Status
echo ""
echo "📋 GIT STATUS"
echo "============="
CURRENT_SHA=$(git rev-parse --short HEAD)
echo "Current commit: $CURRENT_SHA"

if ! git diff --quiet HEAD; then
    echo "Working directory: ⚠️  Uncommitted changes"
    echo "Files changed:"
    git status --short | head -5
    [ $(git status --short | wc -l) -gt 5 ] && echo "... and more"
else
    echo "Working directory: ✅ Clean"
fi

# Docker Images
echo ""
echo "🐳 LOCAL DOCKER IMAGES"
echo "======================"
if docker images myaigist --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedSince}}" | grep -v REPOSITORY; then
    docker images myaigist --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedSince}}"
else
    echo "No local MyAIGist images found"
fi

# Running containers
echo ""
echo "🏃 RUNNING CONTAINERS"
echo "===================="
if docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" | grep myaigist; then
    echo "Local containers:"
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" | head -1
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" | grep myaigist
else
    echo "No local MyAIGist containers running"
fi