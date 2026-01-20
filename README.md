### Step 1: Install Dependencies

```bash
# Install backend dependencies
python3 -m pip install -r backend/requirements.txt

# Install scripts dependencies
python3 -m pip install -r scripts/requirements.txt

**Or install all at once:**
pip install fastapi uvicorn pandas pytrends python-multipart
```

### Step 2: Run Data Pipeline 

```bash
# First make a data folder 
mkdir -p data && ls -la data
# Pull Google Trends data. This may take a while! 
python scripts/pull_trends.py

# This file is in the gitignore hence it will not be pushed to github! Please ensure that it doesnt get removed from gitignore as it is an autogenerted file and will be different per person!
```

**What this does:**
- Reads keywords from `keywords - Sheet1.csv`
- Fetches Google Trends data for each keyword
- Saves results to `data/trends_cache.json`

**Expected runtime:** 5-10 minutes (due to Google rate limiting)

**Output:** `data/trends_cache.json` with trend data

### Step 3: Start Backend API 

```bash
# Start the FastAPI server
python3 -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

**Backend runs on:** http://127.0.0.1:8000

**Interactive API docs:** http://127.0.0.1:8000/docs

**Get all Keywords:** http://127.0.0.1:8000/trends?keyword=organic%20cotton

---

### Step 4: Test the API

**Browser:** Visit http://127.0.0.1:8000/docs

**Command line:**
```bash
# Health check
curl http://127.0.0.1:8000/

# Get all keywords
curl http://127.0.0.1:8000/keywords

# Get trends for a keyword
curl "http://127.0.0.1:8000/trends?keyword=organic%20cotton"

# Get summary
curl http://127.0.0.1:8000/trends/summary

## 🐛 Troubleshooting

### "No trends file found"
```bash
# Run the data pipeline first
python scripts/pull_trends.py
```

### "Port 8000 already in use"
```bash
# Find and kill the process
lsof -i :8000
kill -9 <PID>
```

### Backend won't start
```bash
# Check dependencies installed
pip install -r backend/requirements.txt

# Check if data folder exists
mkdir -p data
```