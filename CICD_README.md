# MyAIGist CI/CD Pipeline

This document describes the CI/CD pipeline setup for MyAIGist with proper QA testing before production deployment.

## 🏗️ Infrastructure Overview

### Production Environment
- **Cluster**: `myaigist-cluster`
- **Service**: `myaigist-service` 
- **ECR**: `039357025951.dkr.ecr.us-east-1.amazonaws.com/myaigist`
- **URL**: https://myaigist.ai

### QA Environment  
- **Cluster**: `myaigist-qa-cluster`
- **Service**: `myaigist-qa-service`
- **ECR**: `039357025951.dkr.ecr.us-east-1.amazonaws.com/myaigist-qa`
- **Access**: Direct IP (changes with deployments)

## 🚀 Deployment Workflow

### Option 1: Full Automated Pipeline
```bash
./scripts/full-deploy.sh
```
This runs the complete workflow with interactive prompts:
1. Build & Tag → 2. Local Test → 3. GitHub Push → 4. QA Deploy → 5. Production Deploy

### Option 2: Manual Step-by-Step

#### 1. Build and Tag
```bash
./scripts/build-and-tag.sh
```
- Builds Docker image with current git commit SHA
- Tags as both `myaigist:$COMMIT_SHA` and `myaigist:latest`

#### 2. Test Locally (Optional but Recommended)
```bash
./scripts/test-local.sh [$commit_sha]
```
- Runs container locally on port 8000
- Performs health checks
- Provides testing checklist

#### 3. Deploy to QA
```bash
./scripts/deploy-qa.sh [$commit_sha]
```
- Pushes image to QA ECR repository
- Updates QA ECS service with new task definition
- Provides QA environment IP for testing

#### 4. Deploy to Production
```bash
./scripts/deploy-prod.sh [$commit_sha]
```
- Pulls tested image from QA ECR
- Pushes to Production ECR
- Updates Production ECS service
- Requires confirmation prompt

## 🔄 Version Tracking

### Docker Image Tagging Strategy
- **Commit SHA**: `myaigist:abc1234` (primary identifier)
- **Latest**: `myaigist:latest` (convenience tag)
- **Environment Specific**: Images are stored in separate ECR repos for QA vs Production

### Git Integration
- All deployments are tied to specific Git commit SHAs
- Scripts automatically detect current commit
- Can specify commit SHA manually if needed

## 🧪 Testing Phases

### 1. Local Testing
- Health checks and basic functionality
- Manual testing checklist provided
- Uses real environment variables from `.env`

### 2. QA Environment Testing
- Full AWS infrastructure (ECS + ECR)
- Same configuration as production (except FLASK_ENV=development)
- Isolated from production data and traffic

### 3. Production Deployment
- Only deploys images that have been tested in QA
- Pulls exact same image from QA ECR
- Requires explicit confirmation

## 📋 Prerequisites

### Environment Setup
```bash
# Required .env file for local testing
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBED_MODEL=text-embedding-3-small
OPENAI_TTS_MODEL=tts-1
OPENAI_WHISPER_MODEL=whisper-1
GA_MEASUREMENT_ID=G-XXXXXXXXX  # optional
```

### AWS Permissions
Ensure your AWS CLI has permissions for:
- ECS (clusters, services, tasks, task definitions)
- ECR (repositories, push/pull images)  
- EC2 (network interfaces for IP lookup)
- Logs (CloudWatch log groups)

## 🔍 Monitoring & Troubleshooting

### Check Deployment Status
```bash
# QA Environment
aws ecs describe-services --cluster myaigist-qa-cluster --services myaigist-qa-service --region us-east-1

# Production Environment  
aws ecs describe-services --cluster myaigist-cluster --services myaigist-service --region us-east-1
```

### View Logs
```bash
# QA Logs
aws logs tail /ecs/myaigist-qa --follow --region us-east-1

# Production Logs
aws logs tail /ecs/myaigist --follow --region us-east-1
```

### Get QA Environment IP
```bash
# Get current QA IP address
TASK_ARN=$(aws ecs list-tasks --cluster myaigist-qa-cluster --service-name myaigist-qa-service --region us-east-1 --query 'taskArns[0]' --output text)
ENI_ID=$(aws ecs describe-tasks --cluster myaigist-qa-cluster --tasks $TASK_ARN --region us-east-1 --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text)
aws ec2 describe-network-interfaces --network-interface-ids $ENI_ID --region us-east-1 --query 'NetworkInterfaces[0].Association.PublicIp' --output text
```

## ⚡ Quick Commands Reference

```bash
# Full pipeline
./scripts/full-deploy.sh

# Individual steps
./scripts/build-and-tag.sh
./scripts/test-local.sh
./scripts/deploy-qa.sh abc1234
./scripts/deploy-prod.sh abc1234

# Cleanup local test
docker rm -f myaigist-local

# Check what's running locally
docker ps | grep myaigist
```

## 🎯 Benefits of This Approach

1. **Version Traceability**: Every deployment tied to specific Git commits
2. **QA Validation**: No production deployments without QA testing
3. **Rollback Capability**: Easy to redeploy previous versions by commit SHA
4. **Environment Isolation**: QA and Production completely separated
5. **Automated Safety**: Scripts prevent common deployment mistakes
6. **Monitoring Ready**: CloudWatch logs and ECS metrics for both environments