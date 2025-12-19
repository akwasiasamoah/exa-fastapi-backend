# 🎯 Exa AI Entity Resolution API

**AI-powered entity search with intelligent disambiguation and profile generation**

Solves the classic "Emmanuel the Software Engineer vs Emmanuel the Dentist" problem using Exa's semantic search and optional Claude AI for clustering.

---

## ✨ Features

### 🔍 **Entity Search with Disambiguation**
- Search for people by name with optional "anchor" data (role, company, location)
- Automatic clustering of results into distinct entities
- Confidence scoring for each cluster
- Auto-selection when confidence is high

### 📋 **AI Profile Generation**
- Generate comprehensive professional profiles
- AI-powered summaries using Exa's summary API
- Structured sections (background, expertise, achievements)
- Citation links to all sources

### 🔗 **Similar Entity Discovery**
- Find similar people or organizations
- Semantic similarity matching
- Optional AI summaries for each result

### 🎯 **Standard Search Features**
- Neural (semantic) and keyword search
- Advanced filtering (domains, dates, categories)
- Batch search operations
- Content extraction with highlights

---

## 🏗️ Architecture

Based on the three-stage Entity Resolution pipeline:

```
┌─────────────┐
│  1. FETCHER │  Search broadly with Exa
│             │  (Gets URLs + content + highlights in one call)
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ 2. EVALUATOR│  Disambiguate results
│             │  - Anchor Method: Filter by known facts
│             │  - Clustering Method: Group by distinct entities
└──────┬──────┘
       │
       ↓
┌─────────────┐
│3. SUMMARIZER│  Generate comprehensive profile
│             │  (AI-powered summary from Exa)
└─────────────┘
```

---

## 🚀 Quick Start

### **1. Install Dependencies**

```bash
pip install -r requirements.txt
```

### **2. Configure Environment**

```bash
cp .env.example .env
```

Edit `.env`:
```env
EXA_API_KEY=your_exa_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here  # Optional
CORS_ORIGINS=*
DEBUG=False
```

### **3. Run the API**

```bash
# Development
uvicorn main:app --reload --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### **4. Test the API**

Visit: http://localhost:8000/docs

---

## 📖 API Endpoints

### **Entity Resolution Endpoints**

#### **1. Entity Search with Disambiguation**
```http
POST /api/v1/entity-search
```

**With Anchor (High Precision):**
```json
{
  "name": "Emmanuel Asamoah",
  "anchor": {
    "role": "Software Engineer",
    "company": "Hubtel",
    "location": "Ghana"
  },
  "num_results": 20,
  "auto_select": true
}
```

**Without Anchor (Discovery Mode):**
```json
{
  "name": "Emmanuel Asamoah",
  "num_results": 20
}
```

**Response:**
```json
{
  "query": "Emmanuel Asamoah Software Engineer Hubtel Ghana",
  "has_anchor": true,
  "needs_disambiguation": false,
  "clusters": [
    {
      "cluster_id": "anchor_match",
      "person_name": "Emmanuel Asamoah",
      "description": "Software Engineer at Hubtel, Ghana",
      "confidence": "high",
      "key_facts": ["Software Engineer", "Hubtel", "Ghana"],
      "candidates": [
        {
          "id": "...",
          "title": "Emmanuel Asamoah - Lead Backend Engineer | LinkedIn",
          "url": "https://linkedin.com/in/...",
          "domain": "linkedin.com",
          "highlights": [
            "Lead Backend Engineer at Hubtel",
            "Specialized in payment processing systems"
          ],
          "score": 0.95
        }
      ],
      "total_results": 5
    }
  ],
  "total_candidates": 15,
  "auto_selected": "anchor_match"
}
```

#### **2. Generate Profile**
```http
POST /api/v1/generate-profile
```

```json
{
  "cluster_id": "anchor_match",
  "result_ids": ["id1", "id2", "id3"],
  "focus_areas": [
    "professional_background",
    "expertise",
    "achievements",
    "education"
  ]
}
```

**Response:**
```json
{
  "cluster_id": "anchor_match",
  "profile": {
    "name": "Emmanuel Asamoah",
    "headline": "Lead Backend Engineer",
    "summary": "Emmanuel Asamoah is an experienced software engineer...",
    "sections": [
      {
        "title": "Professional Summary",
        "content": "Comprehensive professional background..."
      }
    ],
    "links": [
      {"title": "LinkedIn Profile", "url": "..."},
      {"title": "GitHub", "url": "..."}
    ],
    "metadata": {
      "cluster_id": "anchor_match",
      "sources": 3
    },
    "generated_at": "2025-12-18T10:30:00Z"
  },
  "sources_used": 3
}
```

#### **3. Find Similar Entities**
```http
POST /api/v1/find-similar-entities
```

```json
{
  "url": "https://linkedin.com/in/emmanuel-asamoah",
  "num_results": 10,
  "include_summary": true
}
```

---

### **Standard Search Endpoints**

#### **Search**
```http
POST /api/v1/search
```

#### **Get Contents**
```http
POST /api/v1/contents
```

#### **Find Similar**
```http
POST /api/v1/find-similar
```

#### **Batch Search**
```http
POST /api/v1/batch-search
```

---

## 💡 Use Cases

### **1. Sales & Business Development**
```python
# Research a prospect before a meeting
response = requests.post("http://localhost:8000/api/v1/entity-search", json={
    "name": "John Smith",
    "anchor": {
        "company": "TechCorp",
        "role": "CTO"
    }
})

# Generate profile/dossier
profile = requests.post("http://localhost:8000/api/v1/generate-profile", json={
    "cluster_id": response.json()["auto_selected"],
    "result_ids": [c["id"] for c in response.json()["clusters"][0]["candidates"]]
})
```

### **2. Recruitment & Hiring**
```python
# Background check on a candidate
response = requests.post("http://localhost:8000/api/v1/entity-search", json={
    "name": "Jane Doe",
    "anchor": {
        "role": "Data Scientist",
        "location": "San Francisco"
    },
    "include_domains": ["linkedin.com", "github.com"]
})
```

### **3. Journalism & Research**
```python
# Research a source
response = requests.post("http://localhost:8000/api/v1/entity-search", json={
    "name": "Dr. Sarah Johnson",
    "num_results": 30
})

# User selects correct cluster, then generate profile
profile = requests.post("http://localhost:8000/api/v1/generate-profile", ...)
```

### **4. Competitive Intelligence**
```python
# Find competitors to a company
similar = requests.post("http://localhost:8000/api/v1/find-similar-entities", json={
    "url": "https://company.com",
    "num_results": 20
})
```

---

## 🧠 How Disambiguation Works

### **The "Anchor" Method (High Precision)**

When user provides anchor data:
1. Build semantic query: `"Name + Role + Company + Location"`
2. Exa's neural search finds semantically relevant results
3. Filter results that mention anchor facts in highlights
4. Return single high-confidence cluster

**Example:**
- Query: "Emmanuel Asamoah Software Engineer Hubtel Ghana"
- Exa automatically excludes footballers, politicians, doctors
- Returns only tech-related results

### **The "Clustering" Method (Discovery Mode)**

When user provides only a name:
1. Broad search gets 20+ results
2. Extract highlights (role, company, location) via Exa
3. Use Claude AI to intelligently cluster into distinct people
4. Present clusters to user for selection

**Optional: LLM-Based Clustering**

If `ANTHROPIC_API_KEY` is set:
- Uses Claude 3.5 Sonnet for intelligent clustering
- Analyzes highlights to detect distinct identities
- Handles edge cases and ambiguous data

If not set:
- Falls back to simple domain-based clustering
- Still effective for most cases

---

## 🎯 Key Advantages of Using Exa

| **Traditional Approach** | **With Exa** |
|-------------------------|--------------|
| SerpApi → URLs | ✅ Exa → URLs + content + highlights (one call) |
| BeautifulSoup scraping | ✅ Pre-scraped, cleaned content |
| Manual extraction | ✅ Highlights pre-extracted |
| Keyword matching | ✅ Semantic/neural search |
| Build RAG pipeline | ✅ Built-in summary API |
| Multiple API calls | ✅ Consolidated operations |

---

## 🔧 Configuration Options

### **Environment Variables**

| Variable | Required | Description |
|----------|----------|-------------|
| `EXA_API_KEY` | ✅ Yes | Your Exa API key |
| `ANTHROPIC_API_KEY` | ❌ Optional | For advanced LLM clustering |
| `CORS_ORIGINS` | ❌ Optional | Comma-separated allowed origins |
| `DEBUG` | ❌ Optional | Enable debug mode |

### **Search Parameters**

- **num_results**: 1-100 (default: 20)
- **include_domains**: Filter by specific domains
- **exclude_domains**: Exclude specific domains
- **auto_select**: Auto-select best match if high confidence

---

## 📊 Response Confidence Levels

- **High**: 3+ matching results, strong semantic alignment
- **Medium**: 1-2 matching results or moderate alignment
- **Low**: Uncertain or insufficient data

---

## 🐛 Troubleshooting

### **Issue: "Entity service not initialized"**
- Check that `EXA_API_KEY` is set in `.env`
- Restart the server

### **Issue: Clustering returns single cluster**
- Set `ANTHROPIC_API_KEY` for intelligent clustering
- Or provide anchor data for better precision

### **Issue: No results found**
- Try broader search (remove anchor constraints)
- Check if name spelling is correct
- Increase `num_results`

### **Issue: Wrong person in results**
- Provide more specific anchor data
- Use `include_domains` to filter sources
- Add location or company information

---

## 🚀 Deployment

### **Deploy to Render.com**

1. Push code to GitHub
2. Create new Web Service on Render
3. Set environment variables:
   - `EXA_API_KEY`
   - `ANTHROPIC_API_KEY` (optional)
   - `CORS_ORIGINS`
4. Deploy!

See main README for detailed deployment instructions.

---

## 📚 Additional Resources

- **Exa API Docs**: https://docs.exa.ai
- **Anthropic API Docs**: https://docs.anthropic.com
- **FastAPI Docs**: https://fastapi.tiangolo.com

---

## 🤝 Contributing

This is a production-ready implementation. Feel free to:
- Add more sophisticated clustering algorithms
- Enhance profile generation with structured data
- Add export functionality (PDF, JSON, etc.)
- Implement caching for frequent searches

---

## 📄 License

Open source - use freely!

---

**Built with ❤️ using Exa AI, FastAPI, and Claude**
