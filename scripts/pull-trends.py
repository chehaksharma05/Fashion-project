"""
Google Trends Data Extraction Script
Pulls trend data for all keywords and saves to JSON

Run: python scripts/pull_trends.py
Output: data/trends_cache.json
"""

from pytrends.request import TrendReq
import pandas as pd
import json
import time
import os

# File paths
KEYWORDS_PATH = "keywords - Sheet1.csv"
OUTPUT_PATH = "data/trends_cache.json"

def load_keywords(path: str) -> pd.DataFrame:
    """Load keywords from CSV file"""
    df = pd.read_csv(path, header=None)
    df.columns = ["category", "keyword"]
    df["keyword"] = df["keyword"].astype(str).str.strip()
    df = df.dropna()
    df = df[df["keyword"] != ""]
    df = df.drop_duplicates(subset=["keyword"])
    return df

def pull_interest_over_time(keyword: str, timeframe: str = "today 3-m", geo: str = "CA") -> pd.DataFrame:
    """Pull Google Trends data for a single keyword"""
    try:
        pytrends = TrendReq(hl="en-US", tz=360)
        pytrends.build_payload([keyword], timeframe=timeframe, geo=geo)
        df = pytrends.interest_over_time()
        
        if df is None or df.empty:
            print(f"  ⚠️  No data for: {keyword}")
            return pd.DataFrame()
        
        if "isPartial" in df.columns:
            df = df.drop(columns=["isPartial"])
        
        df = df.reset_index()
        df.rename(columns={keyword: "trend_score"}, inplace=True)
        df["keyword"] = keyword
        df["date"] = pd.to_datetime(df["date"]).dt.date.astype(str)
        df["trend_score"] = pd.to_numeric(df["trend_score"], errors="coerce")
        
        return df[["keyword", "date", "trend_score"]]
        
    except Exception as e:
        print(f"  ❌ Error for {keyword}: {str(e)}")
        return pd.DataFrame()

def main():
    print("=" * 60)
    print("🔍 Google Trends Data Extraction")
    print("=" * 60)
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Load keywords
    print(f"\n📂 Loading keywords from: {KEYWORDS_PATH}")
    try:
        keywords_df = load_keywords(KEYWORDS_PATH)
        print(f"✅ Loaded {len(keywords_df)} keywords")
    except Exception as e:
        print(f"❌ Error loading keywords: {e}")
        return
    
    # Pull trends for each keyword
    all_trends = []
    total = len(keywords_df)
    
    print(f"\n🌐 Fetching Google Trends data...")
    print(f"   Time range: Last 3 months")
    print(f"   Geography: Canada (CA)")
    print("-" * 60)
    
    for idx, row in keywords_df.iterrows():
        keyword = row['keyword']
        category = row['category']
        
        print(f"[{idx+1}/{total}] {keyword} ({category})")
        
        trend_data = pull_interest_over_time(keyword, "today 3-m", "CA")
        
        if not trend_data.empty:
            records = trend_data.to_dict('records')
            # Add category to each record
            for record in records:
                record['category'] = category
            all_trends.extend(records)
            print(f"  ✅ Got {len(records)} data points")
        
        time.sleep(3)
    
    # Save to JSON
    print(f"\n💾 Saving data to: {OUTPUT_PATH}")
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(all_trends, f, indent=2)
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ EXTRACTION COMPLETE!")
    print("=" * 60)
    print(f"📊 Total records: {len(all_trends)}")
    print(f"🔑 Unique keywords: {len(set([t['keyword'] for t in all_trends]))}")
    if all_trends:
        print(f"📅 Date range: {min([t['date'] for t in all_trends])} to {max([t['date'] for t in all_trends])}")
    print(f"💾 Output file: {OUTPUT_PATH}")
    print("=" * 60)

if __name__ == "__main__":
    main()