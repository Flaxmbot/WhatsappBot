#!/bin/bash

echo "🚀 WhatsApp Health Chatbot Deployment Script"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found!"
    echo "Please create .env file with all required variables."
    echo "Use .env.example as template."
    exit 1
fi

print_status "Found .env file"

# Load environment variables
set -a
source .env
set +a

# Check required environment variables
required_vars=("WHATSAPP_TOKEN" "WHATSAPP_PHONE_NUMBER_ID" "GEMINI_API_KEY" "GROQ_API_KEY" "PERPLEXITY_API_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    print_error "Missing required environment variables:"
    for var in "${missing_vars[@]}"; do
        echo "  - $var"
    done
    exit 1
fi

print_status "All required environment variables found"

# Check if git is initialized
if [ ! -d .git ]; then
    print_warning "Git repository not initialized. Initializing..."
    git init
    git add .
    git commit -m "Initial commit - WhatsApp Health Chatbot"
fi

# Check if requirements.txt exists
if [ ! -f requirements.txt ]; then
    print_error "requirements.txt not found!"
    exit 1
fi

print_status "Requirements file found"

# Install dependencies locally for testing
echo "📦 Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    print_error "Failed to install dependencies"
    exit 1
fi

print_status "Dependencies installed successfully"

# Test the application locally
echo "🧪 Testing application..."
python -c "
import app
try:
    app.init_db()
    print('✅ Database initialization successful')
except Exception as e:
    print(f'❌ Database initialization failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    print_error "Application test failed"
    exit 1
fi

print_status "Application test passed"

# Check if render.yaml exists
if [ ! -f render.yaml ]; then
    print_error "render.yaml not found!"
    echo "This file is required for Render.com deployment."
    exit 1
fi

print_status "Render configuration found"

# Git operations
echo "📝 Preparing git repository..."
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    print_warning "No changes to commit"
else
    git commit -m "Deploy: $(date '+%Y-%m-%d %H:%M:%S')"
    print_status "Changes committed"
fi

# Push to remote if origin exists
if git remote get-url origin >/dev/null 2>&1; then
    echo "🚀 Pushing to remote repository..."
    git push origin main || git push origin master
    print_status "Code pushed to remote repository"
else
    print_warning "No git remote 'origin' configured"
    echo "Please set up your GitHub repository and run:"
    echo "  git remote add origin https://github.com/yourusername/your-repo.git"
    echo "  git push -u origin main"
fi

echo ""
echo "🎉 Deployment preparation complete!"
echo ""
echo "Next steps:"
echo "1. 📱 Complete WhatsApp Business API setup (see facebook_setup_detailed.md)"
echo "2. 🔗 Connect your GitHub repo to Render.com"
echo "3. 🔧 Add environment variables in Render dashboard"
echo "4. 🚀 Deploy your service"
echo ""
echo "Useful commands:"
echo "  Local test: python app.py"
echo "  Check health: curl http://localhost:5000/health"
echo "  View logs: render logs --tail"
echo ""
echo "📚 For detailed setup instructions, see:"
echo "  - setup_guide.md"
echo "  - facebook_setup_detailed.md"
echo ""
print_status "Happy deploying! 🚀"