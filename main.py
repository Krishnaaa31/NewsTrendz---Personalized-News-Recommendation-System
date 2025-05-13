import streamlit as st
import requests
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# API Keys

# API URLs


# Supported Categories
CATEGORIES = [
    "general", "business", "entertainment", "health", "science", "sports", "technology",
    "world"
]

# Initialize session state
if "read_history" not in st.session_state:
    st.session_state["read_history"] = []
if "show_trending" not in st.session_state:
    st.session_state["show_trending"] = False


# Function to fetch news from NewsAPI
def fetch_newsapi_news(category):
    params = {
        "category": category,
        "country": "in",
        "language": "en",
        "apiKey": NEWSAPI_KEY
    }
    response = requests.get(NEWSAPI_URL, params=params)
    data = response.json()
    return data.get("articles", [])


# Function to fetch news from GNews
def fetch_gnews_news(category):
    params = {
        "category": category,
        "country": "in",
        "lang": "en",
        "token": GNEWS_API_KEY
    }
    response = requests.get(GNEWS_URL, params=params)
    data = response.json()
    return data.get("articles", [])


# Function to fetch news from NewsData.io
def fetch_newsdataio_news(category):
    params = {
        "category": category,
        "country": "in",
        "language": "en",
        "apikey": NEWS_DATA_IO_API_KEY
    }
    response = requests.get(NEWS_DATA_IO_URL, params=params)
    data = response.json()

    if data.get("status") == "success" and data.get("results"):
        return [{"title": article.get("title"), "description": article.get("description"), "url": article.get("link")}
                for article in data["results"]]

    return []


# Function to get news from all sources
def fetch_news(category):
    articles = fetch_newsapi_news(category)
    if not articles:
        articles = fetch_gnews_news(category)
    if not articles and category in ["politics", "crime", "environment", "education", "lifestyle", "opinion",
                                     "weather"]:
        articles = fetch_newsdataio_news(category)
    return articles


# Function to fetch trending news
def fetch_trending_news():
    return fetch_newsapi_news("general") or fetch_gnews_news("general")


# Function to recommend similar articles
def recommend_news(selected_article, articles):
    df = pd.DataFrame(articles)
    if "title" not in df.columns or "description" not in df.columns:
        return []

    df.fillna("", inplace=True)
    df["combined_text"] = df["title"] + " " + df["description"]

    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(df["combined_text"])

    selected_idx = df[df["title"] == selected_article].index[0]
    similarity_scores = cosine_similarity(tfidf_matrix[selected_idx], tfidf_matrix).flatten()
    similar_indices = similarity_scores.argsort()[::-1][1:6]

    return df.iloc[similar_indices].to_dict(orient='records')


# Streamlit UI
st.title("📢 India News Recommendation System")

# User Login Simulation
username = st.text_input("Enter your username:", "")
if username:
    st.sidebar.header(f"👋 Welcome, {username}")
    category = st.sidebar.selectbox("🗂 Choose News Category", CATEGORIES)

    # Trending News Toggle Button
    if st.sidebar.button("🔥 Show Trending News"):
        st.session_state["show_trending"] = not st.session_state["show_trending"]

    # Display Trending News (Collapsible)
    if st.session_state["show_trending"]:
        with st.sidebar.expander("🔥 Trending News", expanded=True):
            trending_articles = fetch_trending_news()
            if trending_articles:
                for article in trending_articles[:5]:
                    st.markdown(f"- [{article['title']}]({article['url']})")
            else:
                st.write("No trending news available at the moment.")

    # Fetch and Display Category News
    articles = fetch_news(category)
    if articles:
        st.subheader(f"📰 Top {category.capitalize()} News")
        for i, article in enumerate(articles[:10]):
            if st.button(f"{i + 1}. {article['title']}"):
                st.write(f"### {article['title']}")
                st.write(article["description"])
                st.markdown(f"[Read More]({article['url']})")

                # Add to Read History (Prevent Duplicates)
                if article not in st.session_state["read_history"]:
                    st.session_state["read_history"].append(article)

                # Show Recommended News
                st.subheader("🔍 You May Also Like")
                recommendations = recommend_news(article["title"], articles)
                for rec in recommendations:
                    st.markdown(f"- [{rec['title']}]({rec['url']})")

    else:
        st.subheader(f"⚠ No news available for the {category.capitalize()} category.")

    # Read History Sidebar
    if st.session_state["read_history"]:
        st.sidebar.subheader("📜 Read History")
        for article in reversed(st.session_state["read_history"]):
            st.sidebar.markdown(f"- [{article['title']}]({article['url']})")
