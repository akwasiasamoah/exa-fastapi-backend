# 🚀 Quick Start Guide - Exa FastAPI Backend

This is your **production-ready FastAPI backend** for Exa AI integration!

## ⚡ Get Started in 3 Minutes

### Step 1: Install Dependencies
```bash
cd exa-fastapi-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Configure API Key
```bash
cp .env.example .env
# Edit .env and add your Exa API key:
# EXA_API_KEY=your_actual_key_here
```

### Step 3: Run the Server
```bash
python main.py
```

That's it! Your API is now running at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs 👈 Try this first!
- **Alternative Docs**: http://localhost:8000/redoc

## 🧪 Test It Out

### Option 1: Interactive Docs (Easiest)
1. Go to http://localhost:8000/docs
2. Click on any endpoint (e.g., `/api/v1/search`)
3. Click "Try it out"
4. Fill in the parameters
5. Click "Execute"

### Option 2: Run Test Script
```bash
python test_api.py
```

### Option 3: Use Example Client
```bash
python example_client.py
```

### Option 4: cURL
```bash
# Health check
curl http://localhost:8000/health

# Search
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "FastAPI tutorials", "num_results": 5}'
```

## 📦 What's Included

### Core Files
- `main.py` - FastAPI application with all endpoints
- `config.py` - Configuration management
- `models.py` - Request/response validation models
- `exa_service.py` - Exa API integration layer

### Documentation
- `README.md` - Complete documentation
- `QUICKSTART.md` - This file

### Testing & Examples
- `test_api.py` - Automated test suite
- `example_client.py` - Python client examples

### Deployment
- `Dockerfile` - Docker container configuration
- `docker-compose.yml` - Docker Compose setup
- `.env.example` - Environment variables template

## 🎯 Available Endpoints

### 1. Search
```bash
POST /api/v1/search
```
Search the web with Exa's neural or keyword search.

### 2. Get Contents
```bash
POST /api/v1/contents
```
Get full webpage content, highlights, and summaries.

### 3. Find Similar
```bash
POST /api/v1/find-similar
```
Find content similar to any URL.

### 4. Batch Search
```bash
POST /api/v1/batch-search
```
Search multiple queries at once.

### 5. Health Check
```bash
GET /health
```
Check API and Exa connectivity status.

## 🐳 Docker Quick Start

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or with Docker directly
docker build -t exa-backend .
docker run -p 8000:8000 --env-file .env exa-backend
```

## 💡 Common Use Cases

### Use Case 1: AI Research Assistant
```python
from example_client import ExaAPIClient

client = ExaAPIClient()
results = client.search(
    query="latest AI research papers",
    search_type="neural",
    include_domains=["arxiv.org"],
    num_results=10
)
```

### Use Case 2: Content Aggregator
```python
# Search for content
results = client.search(query="machine learning tutorials")

# Get full content
urls = [r['url'] for r in results['results'][:5]]
contents = client.get_contents(urls=urls, text=True, summary=True)
```

### Use Case 3: Recommendation Engine
```python
# Find similar content to a given URL
similar = client.find_similar(
    url="https://example.com/article",
    num_results=10,
    exclude_source_domain=True
)
```

## 🔧 Configuration Options

Edit `.env` to customize:

```env
# Required
EXA_API_KEY=your_key

# Optional
DEBUG=True                                    # Enable debug mode
PORT=8000                                     # Change port
CORS_ORIGINS=http://localhost:3000          # Frontend URLs
```

## 📊 Next Steps

1. **Explore the Docs**: http://localhost:8000/docs
2. **Read Full README**: See `README.md` for comprehensive documentation
3. **Run Examples**: Execute `example_client.py` to see all features
4. **Deploy**: Use Docker or your preferred hosting platform

## 🆘 Need Help?

### Common Issues

**Can't connect to API?**
- Make sure server is running: `python main.py`
- Check correct port: http://localhost:8000

**"EXA_API_KEY not found"?**
- Create `.env` file from `.env.example`
- Add your actual Exa API key

**Import errors?**
- Activate virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

## 🎓 Learn More

- [Exa AI Documentation](https://docs.exa.ai)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- Full README in this folder

---

**Built with ❤️ for developers**
