# Exa FastAPI Backend

A production-ready FastAPI backend application that integrates with Exa AI's powerful search API. Built with best practices for scalability, maintainability, and developer experience.

## 🚀 Features

- **Neural & Keyword Search**: Leverage Exa's semantic and keyword-based search capabilities
- **Content Retrieval**: Get full webpage content, highlights, and AI-generated summaries
- **Similarity Search**: Find content similar to any URL
- **Batch Operations**: Process multiple search queries in a single request
- **Comprehensive API Documentation**: Auto-generated OpenAPI docs
- **CORS Support**: Configurable cross-origin resource sharing
- **Health Checks**: Monitor API and Exa connectivity status
- **Production-Ready**: Proper error handling, logging, and configuration management

## 📋 Prerequisites

- Python 3.9 or higher
- Exa API key (get one at [exa.ai](https://exa.ai))
- pip or conda for package management

## 🛠️ Installation

### 1. Clone or Download the Project

```bash
cd exa-fastapi-backend
```

### 2. Create Virtual Environment

```bash
# Using venv
python -m venv venv

# Activate on Linux/Mac
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your Exa API key
# EXA_API_KEY=your_actual_api_key_here
```

**Required Environment Variables:**
- `EXA_API_KEY`: Your Exa API key (required)

**Optional Environment Variables:**
- `APP_NAME`: Application name (default: "Exa FastAPI Backend")
- `APP_VERSION`: Application version (default: "1.0.0")
- `DEBUG`: Enable debug mode (default: False)
- `HOST`: Server host (default: "0.0.0.0")
- `PORT`: Server port (default: 8000)
- `CORS_ORIGINS`: Comma-separated CORS origins (default: "http://localhost:3000")

## 🚦 Running the Application

### Development Mode (with auto-reload)

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📚 API Endpoints

### Health Check

```bash
GET /health
```

Check API health and Exa connectivity.

**Response:**
```json
{
  "status": "healthy",
  "app_name": "Exa FastAPI Backend",
  "version": "1.0.0",
  "exa_api_connected": true,
  "timestamp": "2025-12-18T10:30:00.000000"
}
```

### Search

```bash
POST /api/v1/search
```

Search the web using Exa's neural or keyword search.

**Request Body:**
```json
{
  "query": "latest AI developments in Ghana",
  "num_results": 10,
  "search_type": "auto",
  "include_domains": ["techcrunch.com", "wired.com"],
  "start_published_date": "2025-01-01"
}
```

**Response:**
```json
{
  "results": [
    {
      "title": "AI Revolution in Ghana",
      "url": "https://example.com/article",
      "published_date": "2025-12-01",
      "author": "John Doe",
      "score": 0.95,
      "id": "abc123"
    }
  ],
  "autoprompt_string": null,
  "request_id": "req_xyz789"
}
```

### Get Contents

```bash
POST /api/v1/contents
```

Get full content for URLs or result IDs.

**Request Body:**
```json
{
  "urls": ["https://example.com/article1", "https://example.com/article2"],
  "text": true,
  "highlights": true,
  "summary": false
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "abc123",
      "url": "https://example.com/article1",
      "title": "Article Title",
      "text": "Full article text content...",
      "highlights": ["Key point 1", "Key point 2"],
      "summary": null,
      "author": "John Doe",
      "published_date": "2025-12-01"
    }
  ],
  "request_id": "req_xyz789"
}
```

### Find Similar

```bash
POST /api/v1/find-similar
```

Find content similar to a given URL.

**Request Body:**
```json
{
  "url": "https://example.com/article",
  "num_results": 10,
  "exclude_source_domain": true,
  "category": "technology"
}
```

### Batch Search

```bash
POST /api/v1/batch-search
```

Perform multiple searches in a single request (max 10 queries).

**Request Body:**
```json
{
  "queries": [
    "artificial intelligence",
    "machine learning",
    "neural networks"
  ],
  "num_results": 5
}
```

## 🧪 Testing the API

### Using cURL

```bash
# Health check
curl http://localhost:8000/health

# Search
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "FastAPI backend development",
    "num_results": 5,
    "search_type": "auto"
  }'

# Get contents
curl -X POST http://localhost:8000/api/v1/contents \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://fastapi.tiangolo.com"],
    "text": true
  }'
```

### Using Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Search
response = requests.post(
    f"{BASE_URL}/api/v1/search",
    json={
        "query": "Python FastAPI tutorials",
        "num_results": 10,
        "search_type": "neural"
    }
)
print(response.json())

# Get contents
response = requests.post(
    f"{BASE_URL}/api/v1/contents",
    json={
        "urls": ["https://example.com"],
        "text": True,
        "highlights": True
    }
)
print(response.json())
```

### Using HTTPie

```bash
# Search
http POST :8000/api/v1/search \
  query="machine learning papers" \
  num_results:=5 \
  search_type=neural

# Find similar
http POST :8000/api/v1/find-similar \
  url=https://example.com/article \
  num_results:=10
```

## 📁 Project Structure

```
exa-fastapi-backend/
├── main.py              # FastAPI application and endpoints
├── config.py            # Configuration and settings management
├── models.py            # Pydantic models for validation
├── exa_service.py       # Exa API service layer
├── requirements.txt     # Python dependencies
├── .env.example         # Example environment variables
├── .env                 # Your actual env variables (gitignored)
└── README.md           # This file
```

## 🔧 Advanced Configuration

### CORS Configuration

Edit `.env` to configure CORS origins:

```env
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com,https://app.yourdomain.com
```

### Logging

Logging is configured automatically based on the `DEBUG` setting:
- `DEBUG=True`: INFO level logging
- `DEBUG=False`: WARNING level logging

### Production Deployment

For production deployment, consider:

1. **Use a production ASGI server**:
   ```bash
   gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

2. **Set environment variables**:
   ```env
   DEBUG=False
   CORS_ORIGINS=https://yourdomain.com
   ```

3. **Use a reverse proxy** (Nginx, Caddy)

4. **Enable HTTPS**

5. **Add rate limiting** (set `RATE_LIMIT_ENABLED=True`)

## 🐛 Troubleshooting

### Common Issues

**1. "EXA_API_KEY not found" error**
- Ensure your `.env` file exists and contains `EXA_API_KEY=your_key`
- Check that you're running the app from the correct directory

**2. CORS errors in browser**
- Add your frontend URL to `CORS_ORIGINS` in `.env`
- Restart the server after changing environment variables

**3. "Module not found" errors**
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again

**4. Exa API connection fails**
- Verify your API key is correct
- Check your internet connection
- Visit https://exa.ai to verify API status

## 📖 Additional Resources

- [Exa API Documentation](https://docs.exa.ai)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Pydantic Documentation](https://docs.pydantic.dev)

## 🤝 Contributing

Feel free to fork and improve this backend! Suggestions for enhancements:

- Add authentication/API keys
- Implement caching (Redis)
- Add rate limiting per client
- Create Docker container
- Add comprehensive tests
- Implement WebSocket support for streaming results

## 📝 License

This project is open source and available for use and modification.

## 👨‍💻 Author

Built with ❤️ for developers integrating Exa AI into their applications.
