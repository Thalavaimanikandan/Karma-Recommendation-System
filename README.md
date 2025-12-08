Recommendation System

A production-ready recommendation system combining **Category-based** and **Gorse-based** collaborative filtering approaches.

## Features

- **Category-Based Recommendations**: Uses LLaMA and spaCy for intelligent tag extraction and content categorization
- **Gorse Collaborative Filtering**: Leverages user interactions and feedback for personalized recommendations
- **Content Moderation**: Built-in NSFW detection for text and images
- **Hybrid Approach**: Combine both methods for optimal results
- **RESTful API**: Clean Flask-based API with comprehensive endpoints
- **Docker Support**: Fully containerized deployment

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Flask API Server (Port 5000)                │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐│
│  │   Category       │  │   Gorse          │  │  Content   ││
│  │   Recommender    │  │   Recommender    │  │  Moderator ││
│  │                  │  │                  │  │            ││
│  │  - LLaMA API     │  │  - Collaborative │  │  - NSFW    ││
│  │  - spaCy NLP     │  │    Filtering     │  │  - Toxicity││
│  │  - Tag Extract   │  │  - User/Item     │  │            ││
│  └──────────────────┘  └──────────────────┘  └────────────┘│
│                                                               │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
    ┌───▼────┐  ┌──────┐  ┌──────────┐ │
    │ Gorse  │  │ Redis│  │ MongoDB  │ │
    │ Engine │  │      │  │          │ │
    └────────┘  └──────┘  └──────────┘ │
```

## Installation

### Option 1: Local Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd unified-recommendation-system
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Run the server**
```bash
python app.py
```

### Option 2: Docker Setup

```bash
docker-compose up -d
```

## API Endpoints

### Category-Based

- `POST /api/category/extract-tags` - Extract tags from text
- `POST /api/category/recommend` - Get category-based recommendations

### Gorse-Based

- `GET /api/gorse/recommend/<user_id>` - Get personalized recommendations
- `POST /api/gorse/user` - Add/update user
- `POST /api/gorse/item` - Add/update item
- `POST /api/gorse/feedback` - Submit user feedback
- `GET /api/gorse/popular` - Get popular items
- `GET /api/gorse/latest` - Get latest items
- `GET /api/gorse/similar/<item_id>` - Get similar items

### Content Moderation

- `POST /api/moderate/content` - Moderate text/image content

### Hybrid

- `POST /api/hybrid/recommend` - Get hybrid recommendations

## Usage Examples

See `client_examples.py` for detailed usage examples.

### Quick Start

```python
from client_examples import RecommendationClient

client = RecommendationClient("http://localhost:5000")

# Category-based
result = client.extract_tags("ajith")
print(result)

# Gorse-based
client.add_user("user_123", labels=["action", "thriller"])
client.add_item("movie_thunivu", labels=["action", "ajith"])
client.add_feedback("user_123", "movie_thunivu", "like")
recommendations = client.get_gorse_recommendations("user_123")
```

## Output Format

### Category Tag Extraction

```json
{
  "success": true,
  "tags": {
    "original_sentence": "ajith",
    "spell_corrected": "ACTH",
    "core_categories": ["sports", "actor", "statement"],
    "spacy_keywords": ["acth"],
    "final_tags": ["sports", "actor", "statement", "acth"]
  }
}
```

### Content Moderation

```json
{
  "success": true,
  "result": {
    "analysis_type": ["text", "media"],
    "text_analysis": {
      "corrected_text": "this is Thalavai Manikandan from ChainScript",
      "all_scores": {
        "toxicity": 0.0018,
        "severe_toxicity": 0.0001,
        "obscene": 0.0003,
        "threat": 0.0001,
        "insult": 0.0002,
        "identity_attack": 0.0001
      },
      "violations": [],
      "severity": "SAFE",
      "status": "Safe"
    },
    "media_analysis": {
      "all_predictions": [
        {"label": "normal", "score": 0.9997},
        {"label": "nsfw", "score": 0.0003}
      ],
      "normal_score": 0.9997,
      "nsfw_score": 0.0003,
      "threshold": 0.35,
      "severity": "SAFE",
      "status": "Safe"
    },
    "overall_status": "Safe"
  }
}
```

## Production Deployment

### Using Gunicorn

```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 app:app
```

### Environment Variables

Set these in production:
- `FLASK_ENV=production`
- `DEBUG=False`
- `SECRET_KEY=<strong-random-key>`
- Configure all service URLs

## Testing

```bash
pytest tests/
```

## License

MIT License

## Author

Thalavai Manikandan - ChainScript