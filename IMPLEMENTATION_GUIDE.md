# AI Tool Finder - Complete Implementation Guide

## ✅ Completed Files (Already in Repository)

1. `backend/requirements.txt` - All Python dependencies
2. `backend/crawler.py` - Web crawler with robots.txt compliance
3. `backend/models.py` - SQLAlchemy database models
4. `backend/database.py` - Database setup with FTS5

## 🚀 Remaining Files to Implement

### Step 1: Create `backend/search.py`

Create file: `backend/search.py`

```python
"""Search implementations: Full-text (FTS5) and Semantic search."""

from sqlalchemy.orm import Session
from sqlalchemy import text
from models import Tool
from sentence_transformers import SentenceTransformer
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Load sentence transformer model for semantic search
model = SentenceTransformer('all-MiniLM-L6-v2')

def full_text_search(db: Session, query: str, limit: int = 20):
    """Full-text search using SQLite FTS5."""
    try:
        # Search in FTS5 virtual table
        sql = text("""
            SELECT tools.id, tools.name, tools.description, tools.url, 
                   tools.pricing, tools.rating, rank
            FROM tools_fts
            JOIN tools ON tools_fts.rowid = tools.id
            WHERE tools_fts MATCH :query
            ORDER BY rank
            LIMIT :limit
        """)
        
        result = db.execute(sql, {"query": query, "limit": limit})
        tools = []
        for row in result:
            tool = db.query(Tool).filter(Tool.id == row[0]).first()
            if tool:
                tools.append(tool)
        
        return tools
    except Exception as e:
        logger.error(f"FTS search error: {e}")
        return []

def semantic_search(db: Session, query: str, limit: int = 20):
    """Semantic search using sentence transformers."""
    try:
        # Get all tools from database
        all_tools = db.query(Tool).all()
        
        if not all_tools:
            return []
        
        # Encode query
        query_embedding = model.encode([query])[0]
        
        # Encode all tool descriptions
        tool_texts = [f"{tool.name}. {tool.description or ''}" for tool in all_tools]
        tool_embeddings = model.encode(tool_texts)
        
        # Calculate cosine similarity
        similarities = np.dot(tool_embeddings, query_embedding) / (
            np.linalg.norm(tool_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Get top results
        top_indices = np.argsort(similarities)[::-1][:limit]
        results = [all_tools[i] for i in top_indices]
        
        return results
    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        return []

def hybrid_search(db: Session, query: str, limit: int = 20):
    """Combine full-text and semantic search results."""
    fts_results = full_text_search(db, query, limit)
    semantic_results = semantic_search(db, query, limit)
    
    # Combine and deduplicate
    seen_ids = set()
    combined = []
    
    for tool in fts_results + semantic_results:
        if tool.id not in seen_ids:
            seen_ids.add(tool.id)
            combined.append(tool)
            if len(combined) >= limit:
                break
    
    return combined
```

### Step 2: Create `backend/main.py` (FastAPI Application)

Create file: `backend/main.py`

```python
"""FastAPI application with REST endpoints."""

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from database import get_db, init_db
from models import Tool, Category
import search
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Tool Finder API",
    description="REST API for AI Tool discovery",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ToolResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    url: str
    pricing: Optional[str]
    rating: Optional[float]
    categories: List[str]

    class Config:
        from_attributes = True

class CategoryResponse(BaseModel):
    id: int
    name: str
    tool_count: int

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database...")
    init_db()

@app.get("/")
async def root():
    return {
        "message": "AI Tool Finder API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/api/tools", response_model=List[ToolResponse])
async def get_tools(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all tools with pagination."""
    query = db.query(Tool)
    
    if category:
        query = query.join(Tool.categories).filter(Category.name == category)
    
    tools = query.offset(skip).limit(limit).all()
    return [
        ToolResponse(
            id=tool.id,
            name=tool.name,
            description=tool.description,
            url=tool.url,
            pricing=tool.pricing,
            rating=tool.rating,
            categories=[cat.name for cat in tool.categories]
        )
        for tool in tools
    ]

@app.get("/api/tools/{tool_id}", response_model=ToolResponse)
async def get_tool(tool_id: int, db: Session = Depends(get_db)):
    """Get tool by ID."""
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    return ToolResponse(
        id=tool.id,
        name=tool.name,
        description=tool.description,
        url=tool.url,
        pricing=tool.pricing,
        rating=tool.rating,
        categories=[cat.name for cat in tool.categories]
    )

@app.get("/api/search", response_model=List[ToolResponse])
async def search_tools(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Full-text search."""
    tools = search.full_text_search(db, q, limit)
    return [
        ToolResponse(
            id=tool.id,
            name=tool.name,
            description=tool.description,
            url=tool.url,
            pricing=tool.pricing,
            rating=tool.rating,
            categories=[cat.name for cat in tool.categories]
        )
        for tool in tools
    ]

@app.get("/api/semantic-search", response_model=List[ToolResponse])
async def semantic_search_tools(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Semantic search."""
    tools = search.semantic_search(db, q, limit)
    return [
        ToolResponse(
            id=tool.id,
            name=tool.name,
            description=tool.description,
            url=tool.url,
            pricing=tool.pricing,
            rating=tool.rating,
            categories=[cat.name for cat in tool.categories]
        )
        for tool in tools
    ]

@app.get("/api/categories", response_model=List[CategoryResponse])
async def get_categories(db: Session = Depends(get_db)):
    """Get all categories."""
    categories = db.query(Category).all()
    return [
        CategoryResponse(
            id=cat.id,
            name=cat.name,
            tool_count=len(cat.tools)
        )
        for cat in categories
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Step 3: Create `backend/.env.example`

```env
DATABASE_URL=sqlite:///./tools.db
CRAWL_DELAY=5
MAX_TOOLS=1000
```

### Step 4: Create `backend/tests/test_api.py`

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "AI Tool Finder API" in response.json()["message"]

def test_get_tools():
    response = client.get("/api/tools")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_search():
    response = client.get("/api/search?q=chatgpt")
    assert response.status_code == 200
```

## 📦 Next Steps

1. **Add these files to your repository**
2. **Run the crawler**: `python backend/crawler.py`
3. **Start the API**: `uvicorn backend.main:app --reload`
4. **Test the API**: Visit http://localhost:8000/docs

## 🎯 For Complete Project

See the repository README.md for:
- Frontend setup (React + Vite)
- Docker deployment
- GitHub Actions CI/CD
- Production deployment options

---
**Repository**: https://github.com/amalsp220/ai-tool-finder
