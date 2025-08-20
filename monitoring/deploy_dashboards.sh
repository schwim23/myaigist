#!/bin/bash

# Deploy CloudWatch Dashboards for MyAIGist
# This script creates comprehensive monitoring dashboards for user behavior and infrastructure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📊 Deploying MyAIGist CloudWatch Dashboards${NC}"
echo -e "${BLUE}=============================================${NC}"

# Configuration
REGION="us-east-1"
USER_BEHAVIOR_DASHBOARD="MyAIGist-User-Behavior"
INFRASTRUCTURE_DASHBOARD="MyAIGist-Infrastructure"

# Function to create dashboard
create_dashboard() {
    local dashboard_name=$1
    local dashboard_file=$2
    
    echo -e "${YELLOW}🔧 Creating dashboard: ${dashboard_name}${NC}"
    
    # Read the dashboard JSON and create the dashboard
    aws cloudwatch put-dashboard \
        --dashboard-name "$dashboard_name" \
        --dashboard-body "file://$dashboard_file" \
        --region "$REGION"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Successfully created dashboard: ${dashboard_name}${NC}"
    else
        echo -e "${RED}❌ Failed to create dashboard: ${dashboard_name}${NC}"
        exit 1
    fi
}

# Function to verify dashboard exists
verify_dashboard() {
    local dashboard_name=$1
    
    echo -e "${YELLOW}🔍 Verifying dashboard: ${dashboard_name}${NC}"
    
    aws cloudwatch get-dashboard \
        --dashboard-name "$dashboard_name" \
        --region "$REGION" > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Dashboard verified: ${dashboard_name}${NC}"
        
        # Get the dashboard URL
        local dashboard_url="https://console.aws.amazon.com/cloudwatch/home?region=${REGION}#dashboards:name=${dashboard_name}"
        echo -e "${BLUE}🔗 Dashboard URL: ${dashboard_url}${NC}"
    else
        echo -e "${RED}❌ Dashboard verification failed: ${dashboard_name}${NC}"
    fi
}

# Main deployment
echo -e "${YELLOW}📈 Deploying User Behavior Dashboard...${NC}"
create_dashboard "$USER_BEHAVIOR_DASHBOARD" "dashboard_user_behavior.json"
verify_dashboard "$USER_BEHAVIOR_DASHBOARD"

echo ""
echo -e "${YELLOW}🖥️ Deploying Infrastructure Dashboard...${NC}"
create_dashboard "$INFRASTRUCTURE_DASHBOARD" "dashboard_infrastructure.json"
verify_dashboard "$INFRASTRUCTURE_DASHBOARD"

echo ""
echo -e "${GREEN}🎉 Dashboard deployment completed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Dashboard Summary:${NC}"
echo -e "${BLUE}===================${NC}"
echo -e "1. User Behavior Dashboard:"
echo -e "   - Content processing analytics by type (text, file, URL, media)"
echo -e "   - Q&A system usage and response times"
echo -e "   - Voice feature utilization"
echo -e "   - Processing time metrics"
echo -e "   - Error tracking"
echo ""
echo -e "2. Infrastructure Dashboard:"
echo -e "   - ECS Fargate CPU and memory utilization"
echo -e "   - EFS storage usage and performance"
echo -e "   - Load balancer metrics"
echo -e "   - HTTP response codes"
echo -e "   - Active connections"
echo ""
echo -e "${YELLOW}💡 Note: Custom application metrics will appear after the application${NC}"
echo -e "${YELLOW}    starts sending data with the integrated CloudWatch metrics service.${NC}"