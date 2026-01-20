"""
Fashion Sustainability API Backend
Serves trend data via REST API with placeholder for eco-score integration

Run: uvicorn backend.main:app --reload
Access: http://127.0.0.1:8000
Docs: http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import json
import pandas as pd
from typing import Optional, List, Dict
import os

app = FastAPI(
    title="Fashion Sustainability Trends API",
    description="Backend API for sustainable fashion trend data",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global data storage
trends_data = []

def load_data():
    """Load trends data from JSON file"""
    global trends_data
    
    trends_path = "data/trends_cache.json"
    if os.path.exists(trends_path):
        with open(trends_path) as f:
            trends_data = json.load(f)
        print(f"✅ Loaded {len(trends_data)} trend records")
    else:
        print(f"⚠️  Trends file not found: {trends_path}")
        print(f"   Run: python scripts/pull_trends.py")

@app.on_event("startup")
async def startup_event():
    """Load data when server starts"""
    print("=" * 60)
    print("🚀 Starting Fashion Sustainability API")
    print("=" * 60)
    load_data()
    print("=" * 60)

def get_unique_keywords() -> List[str]:
    """Get list of unique keywords from trend data"""
    return sorted(list(set([t['keyword'] for t in trends_data])))

def calculate_trend_direction(scores: List[float]) -> str:
    """Calculate if trend is going up, down, or stable"""
    if len(scores) < 2:
        return "stable"
    
    trend_change = scores[-1] - scores[0]
    if trend_change > 5:
        return "up"
    elif trend_change < -5:
        return "down"
    else:
        return "stable"

# ========================================
# ECO-SCORE INTEGRATION PLACEHOLDER
# ========================================
def get_eco_score(keyword: str) -> Optional[int]:
    """
    PLACEHOLDER FOR ECO-SCORE CODE
    
    This function should:
    1. Take a keyword as input
    2. Match it against EcoScores_v2_ALL.csv
    3. Return the eco score (1-10 scale, where 1=best, 10=worst)
    
    Current implementation returns None (placeholder)
    
    TODO: Replace this with eco-score matching logic
    """
    
    return None  # Placeholder - returns None for now

# API ENDPOINTS

@app.get("/")
def root():
    """API health check and information"""
    return {
        "status": "running",
        "message": "Fashion Sustainability Trends API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/",
            "keywords": "/keywords",
            "brands": "/brands",
            "trends": "/trends?keyword=<keyword>&brand=<brand>",
            "summary": "/trends/summary",
            "reload": "POST /reload",
            "docs": "/docs"
        },
        "data_stats": {
            "trends_count": len(trends_data),
            "keywords_count": len(get_unique_keywords()),
            "eco_score_integration": "pending"
        }
    }

@app.get("/keywords")
def get_keywords():
    """
    Get list of all available keywords
    Returns keywords grouped by category
    """
    keywords = get_unique_keywords()
    
    categorized = {}
    for t in trends_data:
        keyword = t['keyword']
        category = t.get('category', 'Other')
        if category not in categorized:
            categorized[category] = []
        if keyword not in categorized[category]:
            categorized[category].append(keyword)
    
    return {
        "keywords": keywords,
        "count": len(keywords),
        "by_category": categorized
    }

@app.get("/brands")
def get_brands():
    """
    Get list of available brands
    Currently returns placeholder data - will be populated from eco-scores
    """
    # TODO: Extract real brands from eco-score data when integrated
    return {
        "brands": ["Patagonia", "Everlane", "Reformation"],
        "count": 3,
        "note": "Placeholder brands - will update when eco-score data is integrated"
    }

@app.get("/trends")
def get_trends(
    keyword: str = Query(..., description="Keyword to get trends for"),
    brand: Optional[str] = Query(None, description="Optional brand filter")
):
    """
    Get trend data for a specific keyword
    Optionally filter by brand
    Includes eco-score if available
    """
    filtered = [t for t in trends_data if t['keyword'].lower() == keyword.lower()]
    
    if not filtered:
        raise HTTPException(
            status_code=404, 
            detail=f"No trend data found for keyword: {keyword}"
        )
    
    # Get eco-score (will be None until eco-score code is integrated)
    eco_score = get_eco_score(keyword)
    
    # Enrich each record with eco-score and brand
    result = []
    for record in filtered:
        enriched = record.copy()
        enriched['eco_score'] = eco_score
        enriched['brand'] = brand if brand else "Generic"
        result.append(enriched)
    
    return result

@app.get("/trends/summary")
def get_trends_summary():
    """
    Get summary statistics for all trends
    Includes average scores, current scores, and trend direction
    """
    keywords = get_unique_keywords()
    brands = ["Patagonia", "Everlane", "Reformation"]  # Placeholder
    
    summary = {}
    
    for keyword in keywords:
        summary[keyword] = {}
        
        keyword_data = [t for t in trends_data if t['keyword'] == keyword]
        
        if not keyword_data:
            continue
        
        df = pd.DataFrame(keyword_data)
        df['trend_score'] = pd.to_numeric(df['trend_score'], errors='coerce')
        
        # Get eco-score (placeholder for now)
        eco_score = get_eco_score(keyword)
        if eco_score is None:
            eco_score = 5  # Default middle value if no eco-score
        
        # Calculate metrics
        trend_scores = df['trend_score'].tolist()
        direction = calculate_trend_direction(trend_scores)
        
        # Create summary for each brand
        for brand in brands:
            summary[keyword][brand] = {
                "average_trend": round(float(df['trend_score'].mean()), 1),
                "current_trend": int(df['trend_score'].iloc[-1]),
                "average_eco": float(eco_score),
                "current_eco": int(eco_score),
                "trend_direction": direction,
                "data_points": len(df)
            }
    
    return summary

@app.post("/reload")
def reload_data():
    """
    Reload data from files
    Useful after running pull_trends.py to refresh data
    """
    load_data()
    return {
        "status": "success",
        "message": "Data reloaded successfully",
        "stats": {
            "trends_count": len(trends_data),
            "keywords_count": len(get_unique_keywords())
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)