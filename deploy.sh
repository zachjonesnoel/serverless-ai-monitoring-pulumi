#!/bin/bash

# Main deployment script for the restructured application
# This script deploys both infrastructure and applications

set -e

echo "🚀 Deploying AI Lambda Pulumi Application"
echo "=========================================="

# Function to print colored output
print_status() {
    echo -e "\033[1;34m$1\033[0m"
}

print_success() {
    echo -e "\033[1;32m$1\033[0m"
}

print_error() {
    echo -e "\033[1;31m$1\033[0m"
}

# Check if infrastructure deployment is needed
DEPLOY_INFRA=${1:-"true"}
DEPLOY_FRONTEND=${2:-"true"}

if [ "$DEPLOY_INFRA" = "true" ]; then
    print_status "📦 Deploying infrastructure with Pulumi..."
    cd infrastructure

    # Check if virtual environment exists
    if [ ! -d ".venv" ]; then
        print_error "Virtual environment not found. Please set up the infrastructure environment first."
        exit 1
    fi

    # Deploy infrastructure
    PULUMI_PYTHON_CMD=.venv/bin/python pulumi up --yes

    if [ $? -ne 0 ]; then
        print_error "Infrastructure deployment failed!"
        exit 1
    fi

    print_success "✅ Infrastructure deployment completed!"
    cd ..
fi

if [ "$DEPLOY_FRONTEND" = "true" ]; then
    print_status "🌐 Building and deploying frontend..."

    # Get infrastructure outputs
    cd infrastructure
    BUCKET_NAME=$(PULUMI_PYTHON_CMD=.venv/bin/python pulumi stack output bucket_name 2>/dev/null || echo "")
    CLOUDFRONT_ID=$(PULUMI_PYTHON_CMD=.venv/bin/python pulumi stack output cloudfront_distribution_id 2>/dev/null || echo "")
    FUNCTION_URL=$(PULUMI_PYTHON_CMD=.venv/bin/python pulumi stack output function_url 2>/dev/null || echo "")
    cd ..

    if [ -z "$BUCKET_NAME" ]; then
        print_error "Could not get bucket name from Pulumi outputs"
        print_error "Make sure the infrastructure deployment completed successfully"
        exit 1
    fi

    if [ -z "$FUNCTION_URL" ]; then
        print_error "Could not get function URL from Pulumi outputs"
        print_error "Make sure the infrastructure deployment completed successfully"
        exit 1
    fi

    print_status "📝 Configuration:"
    echo "   Bucket: $BUCKET_NAME"
    echo "   CloudFront ID: $CLOUDFRONT_ID"
    echo "   API Endpoint: $FUNCTION_URL"

    # Update frontend configuration
    cd apps/frontend
    echo "REACT_APP_API_ENDPOINT=$FUNCTION_URL" > .env
    print_status "   Updated .env with API endpoint"

    # Build React app
    print_status "🔨 Building React application..."
    npm run build

    if [ $? -ne 0 ]; then
        print_error "Frontend build failed!"
        exit 1
    fi

    # Upload to S3
    print_status "☁️ Uploading to S3..."

    # Sync build directory to S3 with proper content types
    aws s3 sync build/ s3://$BUCKET_NAME --delete \
        --cache-control "public, max-age=31536000" \
        --exclude "*.html" \
        --exclude "*.json"

    # Upload HTML and JSON files with shorter cache control
    aws s3 sync build/ s3://$BUCKET_NAME --delete \
        --cache-control "public, max-age=0, must-revalidate" \
        --include "*.html" \
        --include "*.json"

    # Set proper content types for specific file types
    aws s3 cp build/index.html s3://$BUCKET_NAME/index.html \
        --content-type "text/html" \
        --cache-control "public, max-age=0, must-revalidate"

    # Invalidate CloudFront cache if distribution ID is available
    if [ -n "$CLOUDFRONT_ID" ]; then
        print_status "🔄 Invalidating CloudFront cache..."
        aws cloudfront create-invalidation \
            --distribution-id $CLOUDFRONT_ID \
            --paths "/*" > /dev/null
        print_status "   CloudFront invalidation initiated"
    fi

    cd ../..
    print_success "✅ Frontend deployment completed!"
fi

print_success "🎉 Deployment completed successfully!"
echo ""
echo "📋 Summary:"
if [ "$DEPLOY_INFRA" = "true" ]; then
    cd infrastructure
    echo "   🔗 CloudFront URL: https://$(PULUMI_PYTHON_CMD=.venv/bin/python pulumi stack output cloudfront_url 2>/dev/null)"
    echo "   🔗 API URL: $(PULUMI_PYTHON_CMD=.venv/bin/python pulumi stack output function_url 2>/dev/null)"
    cd ..
fi
echo ""
echo "Your application should be available shortly!"