#!/bin/bash

# Deploy to Production Environment Script
# Usage: ./scripts/deploy-prod.sh [commit_sha]

set -e

# Get commit SHA from parameter or current git
if [ "$1" ]; then
    COMMIT_SHA="$1"
else
    COMMIT_SHA=$(git rev-parse --short HEAD)
fi

echo "🚨 PRODUCTION DEPLOYMENT: MyAIGist $COMMIT_SHA"
echo "⚠️  This will update the live production environment"
read -p "Are you sure you want to proceed? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

# ECR configuration
PROD_ECR_REPO="039357025951.dkr.ecr.us-east-1.amazonaws.com/myaigist"
QA_ECR_REPO="039357025951.dkr.ecr.us-east-1.amazonaws.com/myaigist-qa"
AWS_REGION="us-east-1"

# Login to ECR
echo "🔐 Logging into AWS ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin 039357025951.dkr.ecr.us-east-1.amazonaws.com

# Pull from QA ECR (this ensures we're deploying exactly what was tested)
echo "📦 Pulling tested image from QA ECR..."
docker pull $QA_ECR_REPO:$COMMIT_SHA

# Tag and push to Production ECR
echo "🚀 Tagging and pushing to Production ECR..."
docker tag $QA_ECR_REPO:$COMMIT_SHA $PROD_ECR_REPO:$COMMIT_SHA
docker push $PROD_ECR_REPO:$COMMIT_SHA

# Also tag as latest for backward compatibility
docker tag $QA_ECR_REPO:$COMMIT_SHA $PROD_ECR_REPO:latest
docker push $PROD_ECR_REPO:latest

# Create production task definition (using existing production template)
echo "🔧 Creating production task definition..."
cat > prod-task-definition-$COMMIT_SHA.json << EOF
{
    "family": "myaigist-task",
    "taskRoleArn": "arn:aws:iam::039357025951:role/ecsTaskRole",
    "executionRoleArn": "arn:aws:iam::039357025951:role/ecsTaskExecutionRole",
    "networkMode": "awsvpc",
    "requiresCompatibilities": [
        "FARGATE"
    ],
    "cpu": "1024",
    "memory": "2048",
    "containerDefinitions": [
        {
            "name": "myaigist",
            "image": "$PROD_ECR_REPO:$COMMIT_SHA",
            "cpu": 0,
            "portMappings": [
                {
                    "containerPort": 8000,
                    "hostPort": 8000,
                    "protocol": "tcp"
                }
            ],
            "essential": true,
            "environment": [
                {
                    "name": "OPENAI_EMBED_MODEL",
                    "value": "text-embedding-3-small"
                },
                {
                    "name": "FLASK_ENV",
                    "value": "production"
                },
                {
                    "name": "OPENAI_TTS_MODEL",
                    "value": "tts-1"
                },
                {
                    "name": "OPENAI_WHISPER_MODEL",
                    "value": "whisper-1"
                }
            ],
            "mountPoints": [
                {
                    "sourceVolume": "efs-volume",
                    "containerPath": "/app/data"
                },
                {
                    "sourceVolume": "efs-volume",
                    "containerPath": "/app/static/audio"
                }
            ],
            "volumesFrom": [],
            "secrets": [
                {
                    "name": "OPENAI_API_KEY",
                    "valueFrom": "arn:aws:ssm:us-east-1:039357025951:parameter/myaigist/openai-api-key"
                },
                {
                    "name": "OPENAI_MODEL",
                    "valueFrom": "arn:aws:ssm:us-east-1:039357025951:parameter/myaigist/openai-model"
                },
                {
                    "name": "GA_MEASUREMENT_ID",
                    "valueFrom": "arn:aws:ssm:us-east-1:039357025951:parameter/myaigist/ga-measurement-id"
                }
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/myaigist",
                    "awslogs-region": "us-east-1",
                    "awslogs-stream-prefix": "ecs"
                }
            },
            "systemControls": []
        }
    ],
    "volumes": [
        {
            "name": "efs-volume",
            "efsVolumeConfiguration": {
                "fileSystemId": "fs-0cd336ba0439e9836",
                "rootDirectory": "/",
                "transitEncryption": "ENABLED"
            }
        }
    ]
}
EOF

# Register new task definition
NEW_TASK_DEF=$(aws ecs register-task-definition --cli-input-json file://prod-task-definition-$COMMIT_SHA.json --region $AWS_REGION --query 'taskDefinition.taskDefinitionArn' --output text)
echo "✅ Registered new task definition: $NEW_TASK_DEF"

# Update Production service
echo "🚀 Updating Production service..."
aws ecs update-service \
  --cluster myaigist-cluster \
  --service myaigist-service \
  --task-definition $NEW_TASK_DEF \
  --region $AWS_REGION \
  --no-cli-pager

# Wait for deployment
echo "⏳ Waiting for Production deployment to complete..."
aws ecs wait services-stable \
  --cluster myaigist-cluster \
  --services myaigist-service \
  --region $AWS_REGION

echo "✅ PRODUCTION DEPLOYMENT COMPLETED!"
echo "🌐 Production: https://myaigist.ai"
echo "📋 Version: $COMMIT_SHA"
echo "🏷️  Image: $PROD_ECR_REPO:$COMMIT_SHA"

# Cleanup
rm -f prod-task-definition-$COMMIT_SHA.json

echo ""
echo "🎉 Deployment successful!"
echo "📊 Monitor at: https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/myaigist-cluster/services/myaigist-service"