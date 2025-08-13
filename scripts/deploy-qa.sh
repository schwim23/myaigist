#!/bin/bash

# Deploy to QA Environment Script
# Usage: ./scripts/deploy-qa.sh [commit_sha]

set -e

# Get commit SHA from parameter or current git
if [ "$1" ]; then
    COMMIT_SHA="$1"
else
    COMMIT_SHA=$(git rev-parse --short HEAD)
fi

echo "🔄 Deploying MyAIGist $COMMIT_SHA to QA environment"

# ECR configuration
QA_ECR_REPO="039357025951.dkr.ecr.us-east-1.amazonaws.com/myaigist-qa"
AWS_REGION="us-east-1"

# Login to ECR
echo "🔐 Logging into AWS ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin 039357025951.dkr.ecr.us-east-1.amazonaws.com

# Tag and push to QA ECR
echo "📦 Tagging and pushing to QA ECR repository..."
docker tag myaigist:$COMMIT_SHA $QA_ECR_REPO:$COMMIT_SHA
docker push $QA_ECR_REPO:$COMMIT_SHA

# Update QA task definition
echo "🔧 Updating QA task definition..."
sed "s|039357025951.dkr.ecr.us-east-1.amazonaws.com/myaigist-qa:.*|039357025951.dkr.ecr.us-east-1.amazonaws.com/myaigist-qa:$COMMIT_SHA\",|" qa-task-definition.json > qa-task-definition-$COMMIT_SHA.json

# Register new task definition
NEW_TASK_DEF=$(aws ecs register-task-definition --cli-input-json file://qa-task-definition-$COMMIT_SHA.json --region $AWS_REGION --query 'taskDefinition.taskDefinitionArn' --output text)
echo "✅ Registered new task definition: $NEW_TASK_DEF"

# Update QA service
echo "🚀 Updating QA service..."
aws ecs update-service \
  --cluster myaigist-qa-cluster \
  --service myaigist-qa-service \
  --task-definition $NEW_TASK_DEF \
  --region $AWS_REGION \
  --no-cli-pager

# Wait for deployment
echo "⏳ Waiting for QA deployment to complete..."
aws ecs wait services-stable \
  --cluster myaigist-qa-cluster \
  --services myaigist-qa-service \
  --region $AWS_REGION

# Get QA instance IP
echo "🔍 Getting QA instance details..."
TASK_ARN=$(aws ecs list-tasks --cluster myaigist-qa-cluster --service-name myaigist-qa-service --region $AWS_REGION --query 'taskArns[0]' --output text)
ENI_ID=$(aws ecs describe-tasks --cluster myaigist-qa-cluster --tasks $TASK_ARN --region $AWS_REGION --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text)
QA_IP=$(aws ec2 describe-network-interfaces --network-interface-ids $ENI_ID --region $AWS_REGION --query 'NetworkInterfaces[0].Association.PublicIp' --output text)

echo "✅ QA deployment completed!"
echo "🌐 QA Environment: http://$QA_IP:8000"
echo "📋 Version: $COMMIT_SHA"
echo ""
echo "🧪 Test the QA environment thoroughly before promoting to production"
echo "🚀 When ready: ./scripts/deploy-prod.sh $COMMIT_SHA"

# Cleanup
rm -f qa-task-definition-$COMMIT_SHA.json