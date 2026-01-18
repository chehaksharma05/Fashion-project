# app.py
# run with: streamlit run app.py

import streamlit as st
import pandas as pd
from pytrends.request import TrendReq

st.set_page_config(page_title="Trends + EcoScores", layout="wide")

st.title("Fashion Trends + Sustainability")
st.write(
    "I pick a keyword, pull Google Trends data, and match it with eco-score info "
    "from our EcoScores dataset."
)

# File paths
KEYWORDS_PATH = "keywords - Sheet1.csv"
ECOSCORES_PATH = "EcoScores_v2_ALL.csv"

# Load keywords
@st.cache_data
def load_keywords(path: str) -> pd.DataFrame:
    # my keywords file has 2 columns
    # col0 = category, col1 = keyword
    df = pd.read_csv(path, header=None)
    df.columns = ["category", "keyword"]
    df["keyword"] = df["keyword"].astype(str).str.strip()
    df = df.dropna()
    df = df[df["keyword"] != ""]
    df = df.drop_duplicates(subset=["keyword"])
    return df

# Load eco scores
@st.cache_data
def load_ecoscores(path: str) -> pd.DataFrame:
    # in file, row 1 is like a title row, and row 2 is the header row
    df = pd.read_csv(path, skiprows=1)

    # drop blank "Unnamed" columns if they exist
    df = df.loc[:, ~df.columns.astype(str).str.contains("^Unnamed")]

    # make column names easier to work with
    df.columns = [c.strip() for c in df.columns.astype(str)]

    # create a lowercase searchable version of all text columns
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype(str).str.strip()

    return df

# Pull Google Trends time series
@st.cache_data(show_spinner=False)
def pull_interest_over_time(keyword: str, timeframe: str, geo: str) -> pd.DataFrame:
    pytrends = TrendReq(hl="en-US", tz=360)
    pytrends.build_payload([keyword], timeframe=timeframe, geo=geo)
    df = pytrends.interest_over_time()

    if df is None or df.empty:
        return pd.DataFrame()

    if "isPartial" in df.columns:
        df = df.drop(columns=["isPartial"])

    df = df.reset_index()
    df.rename(columns={keyword: "trend_score"}, inplace=True)
    df["keyword"] = keyword
    df["date"] = pd.to_datetime(df["date"]).dt.date.astype(str)
    df["trend_score"] = pd.to_numeric(df["trend_score"], errors="coerce")

    return df[["keyword", "date", "trend_score"]]

# Eco-score matching
def find_ecoscore_rows(eco_df: pd.DataFrame, keyword: str) -> pd.DataFrame:
    """
    Beginner-simple matching:
    1) Exact match anywhere in the row (case-insensitive)
    2) If nothing, "contains" match on text columns (keyword inside cell)
    """
    kw = keyword.strip().lower()

    text_cols = [c for c in eco_df.columns if eco_df[c].dtype == "object"]
    if not text_cols:
        return pd.DataFrame()

    # Exact match (any text column equals keyword)
    exact_mask = False
    for c in text_cols:
        exact_mask = exact_mask | (eco_df[c].astype(str).str.lower() == kw)

    exact = eco_df[exact_mask].copy()
    if not exact.empty:
        exact["match_type"] = "exact"
        return exact

    # Contains match (keyword appears inside any text column)
    contains_mask = False
    for c in text_cols:
        contains_mask = contains_mask | (eco_df[c].astype(str).str.lower().str.contains(kw, na=False))

    contains = eco_df[contains_mask].copy()
    if not contains.empty:
        contains["match_type"] = "contains"
        return contains

    return pd.DataFrame()

# Load data (with errors)
try:
    kw_df = load_keywords(KEYWORDS_PATH)
except Exception as e:
    st.error(f"I couldn't load the keywords file.")
    st.stop()

try:
    eco_df = load_ecoscores(ECOSCORES_PATH)
except Exception as e:
    st.error(f"I couldn't load the EcoScores file.")
    st.stop()

# Sidebar controls
st.sidebar.header("Controls")

category_options = ["All"] + sorted(kw_df["category"].astype(str).unique().tolist())
picked_category = st.sidebar.selectbox("Category", category_options)

if picked_category == "All":
    filtered_kw = kw_df.copy()
else:
    filtered_kw = kw_df[kw_df["category"].astype(str) == picked_category].copy()

keyword_options = filtered_kw["keyword"].tolist()
picked_keyword = st.sidebar.selectbox("Keyword", keyword_options)

geo = st.sidebar.selectbox("Geo", ["CA", "US", "IN", "Global"], index=0)
geo_code = "" if geo == "Global" else geo

timeframe = st.sidebar.selectbox("Time range", ["today 12-m", "today 5-y"], index=0)

# Pull + Display
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Google Trends (interest over time)")

with col2:
    st.subheader("Eco-score lookup")

if st.sidebar.button("Pull data"):
    # Trends
    with st.spinner("Pulling trend data from Google Trends..."):
        trend_df = pull_interest_over_time(picked_keyword, timeframe, geo_code)

    if trend_df.empty:
        st.warning("No trend data came back. Try a different keyword, or switch geo/time range.")
    else:
        # Date filter
        trend_df["date_dt"] = pd.to_datetime(trend_df["date"])
        min_d = trend_df["date_dt"].min().date()
        max_d = trend_df["date_dt"].max().date()

        st.sidebar.markdown("---")
        st.sidebar.write("Date filter (optional)")
        start_date, end_date = st.sidebar.date_input(
            "Pick date range",
            value=(min_d, max_d),
            min_value=min_d,
            max_value=max_d
        )

        mask = (trend_df["date_dt"].dt.date >= start_date) & (trend_df["date_dt"].dt.date <= end_date)
        filtered_trend = trend_df.loc[mask].copy()

        # Chart
        chart_df = filtered_trend[["date_dt", "trend_score"]].set_index("date_dt")
        st.line_chart(chart_df)

        # Clean data table
        st.write("Clean data table (this is what the backend/API can serve):")
        st.dataframe(filtered_trend[["keyword", "date", "trend_score"]], use_container_width=True)

        # Download
        csv_bytes = filtered_trend[["keyword", "date", "trend_score"]].to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download trends CSV",
            data=csv_bytes,
            file_name=f"trends_{picked_keyword.replace(' ', '_')}.csv",
            mime="text/csv"
        )

    # Eco score
    eco_matches = find_ecoscore_rows(eco_df, picked_keyword)

    with col2:
        if eco_matches.empty:
            st.info("No eco-score match found for this keyword.")
        else:
            st.write(f"Found {len(eco_matches)} match(es).")
            st.dataframe(eco_matches.head(20), use_container_width=True)

            # If your dataset has a column that looks like the score, try to display it clearly:
            possible_score_cols = [c for c in eco_matches.columns if "score" in c.lower()]
            if possible_score_cols:
                st.write("Score-related columns I found:")
                st.write(possible_score_cols)

else:
    st.info("Pick your keyword on the left, then click **Pull data**.")

# To run (in the terminal) - streamlit run app.py 