# 🔍 Fake News Detector

A full-stack AI-powered fake news detection platform that combines **RoBERTa-based ML predictions** with **real-time source verification** to determine the authenticity of news articles.

> Paste any news text or URL → get an instant credibility score backed by ML analysis + cross-referencing with 50+ trusted news outlets.

---

## ✨ Features

- **Hybrid Detection Engine** — Combines ML model predictions with live source verification for higher accuracy
- **RoBERTa NLP Model** — Pre-trained transformer model fine-tuned on fake news datasets (swappable with other HuggingFace models)
- **3-Signal Source Verification** — Coverage Density, Trusted Source Ratio, and Content Relevance scoring
- **URL Analysis** — Paste any article URL to auto-extract and analyze the content
- **Live News Ticker** — Fetches trending headlines from Google News RSS
- **Community Fact-Checker** — Share and vote on fact-checked articles
- **Feedback Learning** — Users can correct predictions, improving future results
- **Confidence Scoring** — Multi-level confidence labels (High/Moderate/Low)
- **GPU Accelerated** — Supports CUDA + FP16 mixed precision for fast inference

---

## 🏗️ Architecture

```
┌─────────────────────┐         ┌──────────────────────────┐
│   React Frontend    │  REST   │    Django Backend         │
│   (Vite + Tailwind) │ ◄─────► │    (DRF API)             │
│                     │   API   │                          │
│  • Text/URL Input   │         │  ┌────────────────────┐  │
│  • Probability Gauge│         │  │  RoBERTa Model     │  │
│  • News Ticker      │         │  │  (HuggingFace)     │  │
│  • Community Board  │         │  └────────┬───────────┘  │
│  • Share & Vote     │         │           │              │
└─────────────────────┘         │  ┌────────▼───────────┐  │
                                │  │ Source Verifier     │  │
                                │  │ • Google News RSS   │  │
                                │  │ • Bing Search       │  │
                                │  │ • Google CSE (opt)  │  │
                                │  └────────┬───────────┘  │
                                │           │              │
                                │  ┌────────▼───────────┐  │
                                │  │ Score Combiner      │  │
                                │  │ ML (40%) + Src (60%)│  │
                                │  └────────────────────┘  │
                                └──────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, Vite, Tailwind CSS, React Router, Axios |
| **Backend** | Django, Django REST Framework, SQLite |
| **ML Model** | HuggingFace Transformers, PyTorch, RoBERTa (pre-trained) |
| **Source Verification** | Google News RSS, Bing Search, Google Custom Search API |
| **Web Scraping** | Trafilatura, BeautifulSoup4, Newspaper3k |

---

## 🚀 Getting Started

### Prerequisites

- **Python** 3.10+
- **Node.js** 18+
- **Git**
- (Optional) NVIDIA GPU with CUDA for faster inference

### 1. Clone the Repository

```bash
git clone https://github.com/Kshitij-Jindal-1/Fake-News-Detector.git
cd Fake-News-Detector
```

### 2. Backend Setup

```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

> **Note:** The first run will download the ML model (~500MB) from HuggingFace. This is cached locally in `blog/predictor/models/` for subsequent runs.

### 3. Run the Backend Server

```bash
python manage.py runserver
```

The Django API server will start at **http://127.0.0.1:8000**.

### 4. Frontend Setup

```bash
cd TruthChecker/client

# Install Node.js dependencies
npm install

# Start the development server
npm run dev
```

The React frontend will start at **http://localhost:5173**.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/predict/` | Analyze text for fake news |
| `POST` | `/api/predict/url/` | Analyze a URL's article content |
| `GET` | `/api/health/` | Health check (model status) |
| `GET` | `/api/news/` | Fetch trending news headlines |
| `POST` | `/api/feedback/correct/` | Correct a wrong prediction |
| `DELETE` | `/api/feedback/clear/` | Clear all stored predictions |
| `GET` | `/api/community/` | List community fact-check posts |
| `POST` | `/api/community/create/` | Share a prediction with community |
| `POST` | `/api/community/<id>/vote/` | Vote on a community post |

### Example: Analyze Text

```bash
curl -X POST http://127.0.0.1:8000/api/predict/ \
  -H "Content-Type: application/json" \
  -d '{"text": "Breaking: Scientists discover water on Mars"}'
```

### Example Response

```json
{
  "prediction": "True",
  "probability": 0.8721,
  "trueness_probability": 87.21,
  "confidence_level": "High",
  "confidence_label": "High confidence TRUE",
  "ml_score": 0.8721,
  "source_score": 0.6543,
  "trusted_count": 3,
  "trusted_sources": ["reuters.com", "bbc.com", "ndtv.com"],
  "verification_enabled": true
}
```

---

## 📂 Project Structure

```
Fake-News-Detector/
├── blog/                          # Django project
│   ├── settings.py                # Configuration (model, API keys, trusted domains)
│   ├── urls.py                    # Root URL routing
│   └── predictor/                 # Main prediction app
│       ├── views.py               # API endpoints
│       ├── utils.py               # Model loader
│       ├── ml_predictor.py        # Transformer prediction logic (RoBERTa/BERT)
│       ├── scraper.py             # URL article extraction
│       ├── source_verifier.py     # 3-signal source verification
│       ├── feedback_store.py      # Feedback learning (SQLite)
│       ├── community_store.py     # Community fact-checker (SQLite)
│       └── news_api.py            # Google News RSS headlines
│
├── TruthChecker/
│   └── client/                    # React frontend (Vite)
│       ├── src/
│       │   ├── components/        # UI components (Navbar, Input, Gauge, etc.)
│       │   ├── pages/             # Page views (Home, FakeNews analysis)
│       │   ├── services/          # API service layer
│       │   └── context/           # React context providers
│       ├── package.json
│       └── tailwind.config.js
│
├── manage.py                      # Django management script
├── requirements.txt               # Python dependencies
└── .gitignore
```

---

## ⚙️ Configuration

Key settings in `blog/settings.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `MODEL_NAME` | `hamzab/roberta-fake-news-classification` | HuggingFace model to use |
| `USE_GPU` | `True` | Enable CUDA GPU acceleration |
| `USE_FP16` | `True` | Use FP16 mixed precision |
| `SOURCE_VERIFICATION_ENABLED` | `True` | Enable source cross-referencing |
| `ML_SCORE_WEIGHT` | `0.4` | ML model weight in final score |
| `SOURCE_SCORE_WEIGHT` | `0.6` | Source verification weight in final score |

### Switching Models

You can swap the ML model by changing `DISTILBERT_MODEL_NAME` in `settings.py`:

```python
# Option 1 (default): RoBERTa - good for political news
DISTILBERT_MODEL_NAME = 'hamzab/roberta-fake-news-classification'

# Option 2: BERT - 99.5% accuracy, diverse topics
DISTILBERT_MODEL_NAME = 'jy46604790/Fake-News-Bert-Detect'

# Option 3: BERT-tiny - smaller and faster
DISTILBERT_MODEL_NAME = 'mrm8488/bert-tiny-finetuned-fake-news-detection'
```

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is open source and available for educational and research purposes.

---

## 👤 Author

**Kshitij Jindal** — [@Kshitij-Jindal-1](https://github.com/Kshitij-Jindal-1)
