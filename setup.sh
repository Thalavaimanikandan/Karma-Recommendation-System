#!/bin/bash

# setup.sh - Complete Recommendation System Setup
# Usage: bash setup.sh

set -e  # Exit on error

echo "=============================================="
echo "🚀 Recommendation System Setup"
echo "=============================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 found${NC}"

# Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found${NC}"
    echo "Install: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✅ Docker found${NC}"

# Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not found${NC}"
    echo "Install: https://docs.docker.com/compose/install/"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose found${NC}"

echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo ""
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Create necessary directories
echo ""
echo "📁 Creating directories..."
mkdir -p data logs
touch data/.gitkeep
touch logs/.gitkeep
echo -e "${GREEN}✅ Directories created${NC}"

# Copy .env if not exists
echo ""
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cat > .env << 'EOF'
# MongoDB
MONGO_URI=mongodb://localhost:27017/
MONGO_DB=recommendation_db

# Gorse
GORSE_API_URL=http://localhost:8087
GORSE_API_KEY=

# LLaMA/Ollama
LLAMA_API_URL=http://localhost:11434
LLAMA_MODEL=llama3.2

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Flask
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=True

# Logging
LOG_LEVEL=INFO
EOF
    echo -e "${GREEN}✅ .env file created${NC}"
else
    echo -e "${YELLOW}⚠️  .env file already exists${NC}"
fi

# Start Docker services
echo ""
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to start (30 seconds)..."
sleep 30

# Check service health
echo ""
echo "🏥 Checking service health..."

# MongoDB
if curl -s http://localhost:27017 > /dev/null 2>&1 || nc -z localhost 27017 2>&1; then
    echo -e "${GREEN}✅ MongoDB is running${NC}"
else
    echo -e "${RED}❌ MongoDB failed to start${NC}"
fi

# Gorse
if curl -s http://localhost:8087/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Gorse is running${NC}"
else
    echo -e "${YELLOW}⚠️  Gorse may need more time to start${NC}"
fi

# Qdrant
if curl -s http://localhost:6333/dashboard > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Qdrant is running${NC}"
else
    echo -e "${RED}❌ Qdrant failed to start${NC}"
fi

# Setup database
echo ""
echo "🗄️  Setting up MongoDB..."
python scripts/setup_db.py
echo -e "${GREEN}✅ Database initialized${NC}"

# Seed data
echo ""
echo "🌱 Seeding sample data..."
python scripts/seed_data.py
echo -e "${GREEN}✅ Sample data created${NC}"

# Check Ollama
echo ""
echo "🦙 Checking Ollama (LLaMA)..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Ollama is running${NC}"
    
    # Train categories
    echo ""
    echo "🤖 Training categories with LLaMA..."
    python scripts/train_categories.py
    echo -e "${GREEN}✅ Categories trained${NC}"
else
    echo -e "${YELLOW}⚠️  Ollama not running${NC}"
    echo ""
    echo "To start Ollama:"
    echo "  1. Install: curl -fsSL https://ollama.com/install.sh | sh"
    echo "  2. Pull model: ollama pull llama3.2"
    echo "  3. Start server: ollama serve"
    echo "  4. Train categories: python scripts/train_categories.py"
fi

# Summary
echo ""
echo "=============================================="
echo "✅ Setup Complete!"
echo "=============================================="
echo ""
echo "📊 Services Status:"
echo "  - MongoDB:    http://localhost:27017"
echo "  - Gorse:      http://localhost:8087"
echo "  - Qdrant:     http://localhost:6333/dashboard"
echo "  - Ollama:     http://localhost:11434"
echo ""
echo "🚀 Next Steps:"
echo ""
echo "1. Start Flask API:"
echo "   python app.py"
echo ""
echo "2. Test API (in another terminal):"
echo "   python test_api.py"
echo ""
echo "3. View logs:"
echo "   docker-compose logs -f"
echo ""
echo "4. Stop services:"
echo "   docker-compose down"
echo ""
echo "=============================================="