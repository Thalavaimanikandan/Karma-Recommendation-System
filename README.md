# 🎯 Recommendation System

Complete recommendation system combining **LLaMA category training**, **Gorse collaborative filtering**, **semantic search**, and **user interest profiling**.

---

## 🌟 Features

- ✅ **Category-based recommendations** (LLaMA trained on dataset)
- ✅ **User interest tracking** (separate table for each category)
- ✅ **New user onboarding** (3 interests → personalized feed)
- ✅ **Gorse integration** (collaborative filtering)
- ✅ **Semantic search** (Qdrant vector database)
- ✅ **Hybrid ranking** (multiple signals combined)
- ✅ **Popular like feed** (relevance-based)

---

## 🏗️ Architecture

```
┌─────────────┐
│   User      │
│  (3 interests)│
└──────┬──────┘
       │
       ↓
┌─────────────────────────────────────┐
│     Flask API (app.py)              │
└──────┬─────────────────────┬────────┘
       │                     │
       ↓                     ↓
┌──────────────┐    ┌────────────────┐
│ CategoryMgr  │    │ HybridRecmdr   │
│ (LLaMA)      │←───│ (Gorse+Qdrant) │
└──────────────┘    └────────────────┘
       │                     │
       ↓                     ↓
┌────────────────────────────────────┐
│         MongoDB                    │
│  - posts                           │
│  - users                           │
│  - user_interests                  │
│  - category_scores (trained)       │
│  - interactions                    │
└────────────────────────────────────┘
```

---

## 📁 Project Structure

```
Recommendation_System/
├── models/
│   ├── category_manager.py      # CLASS 1: LLaMA category training
│   ├── hybrid_recommender.py    # CLASS 2: Hybrid recommendations
│   └── user_manager.py          # User CRUD operations
│
├── services/
│   ├── mongodb_service.py       # MongoDB client
│   ├── gorse_service.py         # Gorse API client
│   ├── qdrant_service.py        # Qdrant vector DB
│   └── llama_service.py         # LLaMA/Ollama client
│
├── utils/
│   ├── embeddings.py            # Sentence transformers
│   └── logger.py                # Logging utilities
│
├── scripts/
│   ├── setup_db.py              # Initialize MongoDB
│   ├── seed_data.py             # Create sample posts
│   ├── train_categories.py      # Train LLaMA categories
│   └── setup_and_test.py        # Complete setup + test
│
├── tests/
│   ├── test_category_manager.py
│   └── test_recommender.py
│
├── data/
│   └── llama_dataset.json       # Training dataset
│
├── app.py                        # Main Flask API
├── config.py                     # Configuration
├── requirements.txt              # Python dependencies
├── docker-compose.yml            # Docker services
├── .env                          # Environment variables
└── test_api.py                   # API testing script
```

---

## 🚀 Quick Start

### 1. **Prerequisites**

- Python 3.9+
- Docker & Docker Compose
- Ollama (for LLaMA)

### 2. **Installation**

```bash
# Clone repository
git clone <your-repo>
cd Recommendation_System

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. **Setup Services**

```bash
# Start MongoDB, Gorse, Redis, Qdrant
docker-compose up -d

# Verify services
docker-compose ps
```

### 4. **Start Ollama (LLaMA)**

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull LLaMA model
ollama pull llama3.2

# Start Ollama server
ollama serve
```

### 5. **Setup Database**

```bash
# Initialize MongoDB collections
python scripts/setup_db.py

# Seed sample data (22 posts)
python scripts/seed_data.py

# Train categories with LLaMA
python scripts/train_categories.py
```

### 6. **Start Flask API**

```bash
python app.py
```

Server runs at: `http://localhost:5000`

### 7. **Test API**

```bash
# In another terminal
python test_api.py
```

---

## 📡 API Endpoints

### 🏥 Health Check
```bash
GET /health
```

### 👤 User Onboarding
```bash
POST /api/user/onboard
{
  "user_id": "user_123",
  "interests": ["movies", "sports", "technology"]
}
```

### 🎯 Get Recommendations
```bash
GET /api/recommend?user_id=user_123&query=best movies&limit=10

# OR

POST /api/recommend
{
  "user_id": "user_123",
  "query": "best action movies",
  "limit": 10
}
```

### 📊 Track Interaction
```bash
POST /api/track
{
  "user_id": "user_123",
  "post_id": "post_001",
  "action": "like"  # view, click, like, share
}
```

### 📈 Get User Interests
```bash
GET /api/user/user_123/interests
```

### 📁 Get Categories
```bash
GET /api/categories
```

### 🔍 Search
```bash
GET /api/search?q=cricket world cup&user_id=user_123&limit=10
```

---

## 🧪 Testing

### Run Unit Tests
```bash
pytest tests/ -v
```

### Run API Tests
```bash
python test_api.py
```

### Manual Testing with cURL

```bash
# Onboard new user
curl -X POST http://localhost:5000/api/user/onboard \
  -H "Content-Type: application/json" \
  -d '{"user_id": "alice", "interests": ["movies", "food", "travel"]}'

# Get recommendations
curl "http://localhost:5000/api/recommend?user_id=alice&query=best movies&limit=5"

# Track interaction
curl -X POST http://localhost:5000/api/track \
  -H "Content-Type: application/json" \
  -d '{"user_id": "alice", "post_id": "post_001", "action": "like"}'
```

---

## 🔧 Configuration

Edit `.env` file:

```bash
# MongoDB
MONGO_URI=mongodb://localhost:27017/
MONGO_DB=recommendation_db

# Gorse
GORSE_API_URL=http://localhost:8087

# LLaMA
LLAMA_API_URL=http://localhost:11434
LLAMA_MODEL=llama3.2

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Flask
FLASK_PORT=5000
FLASK_DEBUG=True
```

---

## 📊 How It Works

### 1. **Category Training (One-time)**

```python
# LLaMA analyzes each post and assigns relevance scores
# Stored in category_scores collection

Example:
{
  "post_id": "post_001",
  "category": "movies",
  "relevance_score": 0.92,  # High relevance
  "trained_at": "2024-12-10T..."
}
```

### 2. **User Onboarding**

```python
# User selects 3 interests
User: "movies", "sports", "technology"

# Stored in user_interests collection
{
  "user_id": "alice",
  "category": "movies",
  "score": 10.0,  # Initial score
  "interaction_count": 0
}
```

### 3. **Recommendation Flow**

```
Query: "best action movies"
         ↓
   Detect category: "movies"
         ↓
   ┌──────────────────┐
   │ New User?        │
   └────┬──────────┬──┘
        │          │
        ↓          ↓
   YES: Use       NO: Use
   interest-based  Gorse +
   high-score      Semantic +
   posts           Category
        │          │
        └────┬─────┘
             ↓
      Merge & Rank
             ↓
      Return Results
```

### 4. **Interest Updates**

```python
# User likes a "technology" post
action = "like"  # +3.0 score

# All interests decay by 0.95
movies: 10.0 → 9.5
sports: 8.0 → 7.6

# New interest added
technology: 0.0 + 3.0 = 3.0

# Result:
movies: 9.5
sports: 7.6
technology: 3.0  # New interest learned!
```

---

## 🎯 Problem Solved

### ❌ Before (Your Issue)

```
Query: "movies"
Results:
#1 Photography Tips      ❌ Wrong (Hobby)
#2 Music Fest 2025       ❌ Wrong (Music)
#3 Budget Smartphones    ❌ Wrong (Technology)
```

### ✅ After (Our Solution)

```
Query: "movies"
Results:
#1 Top 10 Action Movies    ✅ Correct (92% match)
#2 Romantic Comedies       ✅ Correct (88% match)
#3 Marvel Movies 2025      ✅ Correct (85% match)
```

**Why?**
1. LLaMA trained on dataset → category_scores table
2. Query "movies" → detects category → filters relevant posts
3. Hybrid ranking → semantic + category + user interests

---

## 🐛 Troubleshooting

### MongoDB Connection Error
```bash
# Check if MongoDB is running
docker-compose ps mongodb

# Restart if needed
docker-compose restart mongodb
```

### Gorse Not Responding
```bash
# Check Gorse services
docker-compose ps | grep gorse

# View logs
docker-compose logs gorse-server
```

### LLaMA/Ollama Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve
```

### Qdrant Connection Error
```bash
# Check Qdrant
docker-compose ps qdrant

# Access Qdrant dashboard
http://localhost:6333/dashboard
```

---

## 📚 Key Concepts

### CategoryManager
- Trains categories using LLaMA
- Stores relevance scores in MongoDB
- Detects categories from queries
- Returns high-score posts per category

### HybridRecommender
- Combines multiple signals:
  - Gorse (collaborative filtering)
  - Qdrant (semantic search)
  - Category scores (LLaMA trained)
  - User interests (personalization)
- Handles new vs. existing users differently
- Updates user interests based on interactions

### User Interests
- Stored separately per category
- Decays over time (0.95 factor)
- Grows with interactions
- Adapts to changing preferences

---

## 🚀 Production Deployment

### 1. Update .env for Production
```bash
FLASK_DEBUG=False
MONGO_URI=mongodb://your-prod-server:27017/
GORSE_API_URL=http://your-gorse-server:8087
```

### 2. Use Gunicorn
```bash
pip install gunicorn

gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 3. Add Nginx Reverse Proxy
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📞 Support

- GitHub Issues: [Your Repo]
- Email: your-email@example.com

---

## 📄 License

MIT License

---

## 🙏 Acknowledgments

- [Gorse](https://github.com/gorse-io/gorse) - Recommendation engine
- [Qdrant](https://qdrant.tech/) - Vector database
- [Ollama](https://ollama.com/) - Local LLM runtime
- [Sentence Transformers](https://www.sbert.net/) - Embeddings

---

**Built with ❤️ for accurate recommendations**# Recommendation-System
