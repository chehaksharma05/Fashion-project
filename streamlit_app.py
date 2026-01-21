import streamlit as st
import pandas as pd

import requests  

API_BASE = "http://127.0.0.1:8000"  

st.markdown(
    """
    <style>
    /* Main app background */
    .stApp {
        background-color: white;
        color: black;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: black;
    }

    section[data-testid="stSidebar"] * {
        color: white;
    }

    </style>
    """,
    unsafe_allow_html=True
)

st.set_page_config(
    page_title="Sustainable Fashion Recommender",
    layout="wide"
)

st.markdown(
    """
    <div style="
        background-color: black;
        color: white;
        padding: 1.5rem;
        text-align: center;
        border-radius: 0px 0px 10px 10px;
        margin: -1rem -1rem 2rem -1rem;
    ">
        <h1 style="margin:0; font-size:2.5rem;">🌱 Sustainable Fashion Recommender</h1>
    </div>
    """,
    unsafe_allow_html=True
)


@st.cache_data(ttl=300)
def load_data():
    """Fetch trend data from backend API"""
    try:
        # Check if backend is running
        health_check = requests.get(f"{API_BASE}/", timeout=3)
        if not health_check.ok:
            st.error("⚠️ Backend API is not responding")
            return pd.DataFrame()
        
        # Get all keywords from backend
        keywords_response = requests.get(f"{API_BASE}/keywords", timeout=5)
        
        if not keywords_response.ok:
            st.error("❌ Cannot fetch keywords from backend")
            return pd.DataFrame()
        
        keywords_data = keywords_response.json()
        all_keywords = keywords_data.get('keywords', [])
        
        # Fetch trend data for each keyword
        all_data = []
        
        for keyword in all_keywords:
            try:
                trend_response = requests.get(
                    f"{API_BASE}/trends",
                    params={"keyword": keyword},
                    timeout=5
                )
                
                if trend_response.ok:
                    trend_data = trend_response.json()
                    
                    if trend_data:
                        df_temp = pd.DataFrame(trend_data)
                        avg_score = df_temp['trend_score'].mean()
                        category = df_temp['category'].iloc[0] if 'category' in df_temp.columns else 'Other'
                        
                        all_data.append({
                            'keyword': category,
                            'clothing_item': keyword,
                            'popularity_score': avg_score
                        })
                        
            except Exception as e:
                continue
        
        if not all_data:
            st.warning("No trend data available from backend")
            return pd.DataFrame()
        
        return pd.DataFrame(all_data)
    
    except requests.exceptions.ConnectionError:
        st.error("🔴 Cannot connect to backend API")
        st.info("💡 Make sure backend is running: `uvicorn backend.main:app --reload`")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()
df = load_data()

if df.empty:
    st.error("⚠️ No data loaded from backend!")
    st.info("Check: 1) Backend is running 2) data/trends_cache.json exists")
    st.stop()


st.sidebar.header("Filters")

categories = df['keyword'].unique()
selected_category = st.sidebar.selectbox(
    "Category",
    categories
)

filtered_df = df[df['keyword'] == selected_category]

st.markdown(
    f"""
    <h2 style="
        margin-bottom: 0.8rem;
        font-weight: 600;
    ">
        Top 5 Trending Clothing Items — <em>{selected_category}</em>
    </h2>
    """,
    unsafe_allow_html=True
)

items = filtered_df['clothing_item'].unique()
selected_item = st.sidebar.multiselect(
    "Filter by clothing item (optional)",
    items
)

if selected_item:
    filtered_df = filtered_df[
        filtered_df['clothing_item'].isin(selected_item)
    ]



top_5 = (
    filtered_df
    .sort_values("popularity_score", ascending=False)
    .head(5)
)
display_df = top_5[['clothing_item', 'popularity_score']].copy()

st.dataframe(display_df.head())
display_df = display_df.dropna()


st.markdown(
    """
    <h2 style="margin-bottom: 0;">TRENDING THIS WEEK</h2>
    <p style="color: gray; margin-top: 4px;">brands</p>
    """,
    unsafe_allow_html=True
)

import math

num_items = len(display_df)
num_rows = math.ceil(num_items / 2)

rank = 1

for i in range(num_rows):
    col1, col2 = st.columns(2)

    # ---- LEFT CARD ----
    if rank <= num_items:
        row = display_df.iloc[rank - 1]
        with col1:
            st.markdown(
                f"""
                <div style="
                    border: 1px solid #e6e6e6;
                    border-radius: 12px;
                    padding: 14px;
                    margin-bottom: 12px;
                ">
                    <h4 style="margin: 0;">#{rank}</h4>
                    <h3 style="margin: 6px 0;">{row['clothing_item']}</h3>
                    <p style="color: gray; margin: 0;">
                        Trend score: {row['popularity_score']:.2f}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        rank += 1

    # ---- RIGHT CARD ----
    if rank <= num_items:
        row = display_df.iloc[rank - 1]
        with col2:
            st.markdown(
                f"""
                <div style="
                    border: 1px solid #e6e6e6;
                    border-radius: 12px;
                    padding: 14px;
                    margin-bottom: 12px;
                ">
                    <h4 style="margin: 0;">#{rank}</h4>
                    <h3 style="margin: 6px 0;">{row['clothing_item']}</h3>
                    <p style="color: gray; margin: 0;">
                        Trend score: {row['popularity_score']:.2f}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        rank += 1

import matplotlib.pyplot as plt

st.markdown(
    "<h3 style='margin-top:1rem;'>Trend Score Comparison</h3>",
    unsafe_allow_html=True
)

fig, ax = plt.subplots(figsize=(2, 1))

ax.barh(
    display_df['clothing_item'],
    display_df['popularity_score']
)

ax.invert_yaxis()  # highest score at top
ax.set_xlabel("Trend Score")
ax.set_ylabel("")


st.markdown(
    "<h3 style='margin-top:1rem;'>Average Trend Score by Category</h3>",
    unsafe_allow_html=True
)

category_avg = (
    df.groupby('keyword')['popularity_score']
    .mean()
    .sort_values(ascending=False)
)

fig2, ax2 = plt.subplots(figsize=(3, 1))

ax2.bar(
    category_avg.index,
    category_avg.values
)

ax2.set_ylabel("Average Trend Score")
ax2.set_xticklabels(category_avg.index, rotation=45, ha='right')

col1, col2 = st.columns(2)

with col1:
    st.pyplot(fig)

with col2:
    st.pyplot(fig2)