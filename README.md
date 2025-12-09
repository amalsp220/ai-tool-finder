# AI Tool Finder

Production-ready AI Tool Finder that crawls toolify.ai, stores structured tool data, and provides full-text + semantic search capabilities through a REST API and responsive React frontend.

## 🚀 Live Deployment

- **GitHub Repository**: https://github.com/amalsp220/ai-tool-finder
- **Live Demo**: Deploy using the instructions below

## ✨ Features

- 🔍 **Web Crawler**: Respects robots.txt, implements 5s crawl delay
- 💾 **Data Storage**: SQLite database with FTS5 full-text search
- 🤖 **Semantic Search**: Sentence transformers for semantic similarity
- 🔌 **REST API**: FastAPI-based endpoints for search and Q&A
- ⚛️ **React Frontend**: Modern UI with filters and comparison views
- ✅ **Testing**: Pytest suite included
- 🚢 **CI/CD**: GitHub Actions workflow

## 📋 Requirements

- Python 3.9+
- Node.js 16+
- pip & npm

## 🛠️ Local Setup

### Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Run crawler (respects robots.txt)
python crawler.py

# Start API server
python api.py
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## 🌐 Deployment Options

### Option 1: Replit (Recommended for Quick Deploy)

1. Fork this repository
2. Import to Replit from GitHub
3. Configure environment variables
4. Run and get instant HTTPS URL

### Option 2: Vercel + Railway

**Frontend (Vercel)**:
```bash
vercel --prod
```

**Backend (Railway)**:
- Connect GitHub repository
- Set root directory to `/backend`
- Deploy automatically

### Option 3: Docker

```bash
docker-compose up -d
```

## 📊 API Endpoints

- `GET /api/tools` - List all tools
- `GET /api/search?q=query` - Full-text search
- `GET /api/semantic-search?q=query` - Semantic search
- `GET /api/ask?q=question` - Natural language Q&A

## 🏗️ Project Structure

```
ai-tool-finder/
├── backend/
│   ├── crawler.py          # Web scraper
│   ├── database.py         # Data storage
│   ├── api.py             # REST API
│   └── requirements.txt
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
├── .github/workflows/     # CI/CD
├── IMPLEMENTATION_GUIDE.md
├── REPORT.md
└── README.md
```

## 📝 Implementation Details

See [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) for detailed technical documentation.

See [REPORT.md](./REPORT.md) for crawl statistics and compliance details.

## 🧪 Testing

```bash
cd backend
pytest
```

## 📜 License

MIT License - See [LICENSE](./LICENSE)

## 🤝 Contributing

Contributions welcome! Please read IMPLEMENTATION_GUIDE.md first.

## 📧 Contact

Created by @amalsp220
