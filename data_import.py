from pytrends.request import TrendReq
import pandas as pd

# Load data
df = pd.read_csv("data/keywords.csv")
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

# Use clothing items as search terms
keywords = df['clothing_item'].unique().tolist()

# Setup pytrends
pytrends = TrendReq(hl='en-US', tz=360)

def batch_keywords(lst, n=5):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

all_popularity = pd.DataFrame()

for batch in batch_keywords(keywords, 5):
    pytrends.build_payload(batch, cat=67, timeframe='today 12-m', geo='CA')
    data = pytrends.interest_over_time()

    if not data.empty:
        data = data.drop(columns=['isPartial'])
        avg_pop = data.mean().reset_index()
        avg_pop.columns = ['clothing_item', 'popularity_score']
        all_popularity = pd.concat([all_popularity, avg_pop], ignore_index=True)

# Merge back
df = df.merge(all_popularity, on='clothing_item', how='left')

print(df.head())

df.to_csv("data/keywords_with_trends.csv", index=False)
print("Saved keywords_with_trends.csv")

