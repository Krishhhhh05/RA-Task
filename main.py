import streamlit as st
from streamlit_tags import st_tags
import requests
import pandas as pd
import nltk
nltk.download("vader_lexicon")
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from bs4 import BeautifulSoup
from wordcloud import WordCloud
from PIL import Image
import plotly.express as px
import io
import os
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

st.set_page_config(page_title="News Aggregator", page_icon="📰", layout="wide")
st.title("📰 Multi-Topic News Aggregator with Sentiment Analysis")
tab_news, tab_chatbot = st.tabs(["News Aggregator", "Chatbot"])

if "topics" not in st.session_state:
    st.session_state.topics = []
if "articles_cache" not in st.session_state:
    st.session_state.articles_cache = {}

SENTIMENT_ICONS = {"Positive": "😊", "Negative": "😠", "Neutral": "😐"}

# API_KEY = "AIzaSyBZnwrh5s7s3TMoQ0fkxE6fbkX-AlGaHdw"  
# CX = "d5efb0c0edff34023"  

# Get API keys from environment variables
API_KEY = os.getenv("GOOGLE_API_KEY")
CX = os.getenv("GOOGLE_CX")

def extract_best_text(item):
    """
    Given a Google CSE item, attempt:
      1) use og:description or twitter:description from pagemap.metatags
      2) scrape the link and collect visible <p> text (first few paragraphs)
      3) fallback to snippet
    Returns tuple: (text, source_name, image_url, favicon_url, author, published_date)
    """
    pagemap = item.get("pagemap", {})
    metatags = (pagemap.get("metatags") or [{}])[0]

    source_name = metatags.get("og:site_name") or item.get("displayLink") or "Unknown Source"

    image = metatags.get("og:image") or metatags.get("twitter:image")
    if not image:
        
        image = (pagemap.get("cse_image") or [{}])[0].get("src") or (pagemap.get("cse_thumbnail") or [{}])[0].get("src")

    meta_desc = metatags.get("og:description") or metatags.get("twitter:description")

    link = item.get("link")
    scraped_text = None
    if link:
        try:
            r = requests.get(link, timeout=6, headers={"User-Agent": "news-aggregator-bot/1.0"})
            if r.status_code == 200 and "text/html" in r.headers.get("Content-Type", ""):
                soup = BeautifulSoup(r.text, "html.parser")
                paragraphs = [p.get_text().strip() for p in soup.find_all("p") if p.get_text().strip()]
                if paragraphs:
                    scraped_text = " ".join(paragraphs[:6])
        except Exception:
            scraped_text = None
    
    text = scraped_text or meta_desc or item.get("snippet", "")

    display_link = item.get("displayLink") or ""
    favicon = f"https://www.google.com/s2/favicons?sz=64&domain={display_link}" if display_link else None

    author = metatags.get("author") or metatags.get("article:author") or item.get("displayLink")
    published_date = (metatags.get("article:published_time") or metatags.get("og:updated_time") or None)

    return text, source_name, image, favicon, author, published_date


def fetch_articles(query: str, limit=10) -> list:
    """Fetch results from Google Custom Search (news), extract best text, compute sentiment."""
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": CX,
        "q": f"{query} site:news.google.com",
        "num": limit,
    }
    try:
        resp = requests.get(url, params=params, timeout=8)
        resp.raise_for_status()  # Raise exception for 4XX/5XX status codes
        data = resp.json()
        
        if "error" in data:
            st.error(f"API Error: {data['error'].get('message', 'Unknown error')}")
            return []
        
        if not data.get("items"):
            st.warning(f"No results found for '{query}'")
            return []
            
    except requests.exceptions.Timeout:
        st.error(f"Search request timed out. Please try again later.")
        return []
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP Error: {e}")
        return []
    except Exception as e:
        st.error(f"Search request failed: {e}")
        return []

    items = data.get("items", [])
    articles = []
    sia = SentimentIntensityAnalyzer()

    for it in items:
        text, source, image, favicon, author, published_date = extract_best_text(it)
        preview_text = (text or "").strip()
        if len(preview_text) > 1000:
            preview_text = preview_text[:1000].rsplit(" ", 1)[0]

        # sentiment
        sentiment = {"scores": None, "label": "N/A"}
        if preview_text:
            scores = sia.polarity_scores(preview_text)
            if scores["compound"] >= 0.05:
                label = "Positive"
            elif scores["compound"] <= -0.05:
                label = "Negative"
            else:
                label = "Neutral"
            sentiment = {"scores": scores, "label": label}

        article = {
            "title": it.get("title") or "Untitled",
            "url": it.get("link"),
            "description": preview_text,
            "source": source,
            "image": image,
            "favicon": favicon,
            "author": author,
            "published_date": published_date,
            "sentiment": sentiment,
        }
        articles.append(article)

    return articles


def truncate(text, n=300):
    if not text:
        return ""
    text = text.strip()
    return text if len(text) <= n else text[:n].rsplit(" ", 1)[0] + "..."

def render_article_card(article):
    """Render a clean article card: title, source, description, sentiment, small image."""
    title = article.get("title", "Untitled")
    source = article.get("source", "Unknown Source")
    description = article.get("description", "No description available")
    description_short = truncate(description, 300)
    sentiment_label = article.get("sentiment", {}).get("label", "N/A")
    sentiment_scores = article.get("sentiment", {}).get("scores")
    sentiment_score = sentiment_scores["compound"] if sentiment_scores else 0.0
    emoji = SENTIMENT_ICONS.get(sentiment_label, "❓")

    favicon = article.get("favicon") or "https://via.placeholder.com/16"
    image = article.get("image") or "https://via.placeholder.com/120x80?text=No+Image"
    url = article.get("url", "#")
    card_html = f"""
    <div style="
            display: flex; 
            flex-direction: row; 
            border: 1px solid #e6e6e6; 
            border-radius: 12px; 
            padding: 14px; 
            margin-bottom: 14px;
            box-shadow: 1px 1px 6px rgba(0,0,0,0.04);
      ">
        <div style="display: flex; flex-direction: row; flex: 6;">
            <div style="display: flex; flex-direction: column; flex: 1; margin-right: 12px;">
                <div style="margin-bottom: 6px;">
                    <a href="{url}" target="_blank" style="
                        font-size: 18px;
                        font-weight: bold;
                        color: #1a73e8;
                        text-decoration: none;
                        border-bottom: 1px solid transparent;
                        transition: border-color 0.2s ease;
                        overflow-wrap: break-word;
                    " onmouseover="this.style.borderBottom='1px solid #1a73e8'" 
                       onmouseout="this.style.borderBottom='1px solid transparent'">
                        {title}
                    </a>
                </div>
                <div>
                    <p style="margin:6px 0 8px 0; font-size:14px;">{description_short}</p>
                </div>
                <div>
                    <p style="color:#6b6b6b; font-size:13px; margin:0 0 8px 0;">
                        <img src="{favicon}" style="width:16px; height:16px; vertical-align:middle; margin-right:6px; border-radius:3px;">
                        <strong style="vertical-align:middle;">{source}</strong>
                    </p>
                </div>
            </div>
            <div style="flex-shrink:0; margin-left: 10px;">
                <img src="{image}" style="width:140px; height:90px; object-fit:cover; border-radius:8px;">
            </div>
        </div>
        <div style="display: flex; flex-direction: column; flex: 1; margin-left: 15px; border-left: 1px solid #e6e6e6; padding-left: 15px;">
            <div>
                Sentiment Analysis
            </div>
            <div style="font-size: 50px; text-align: center; margin: 5px 0;">
                {emoji}
            </div>
            <div style="text-align: center;">
                <p style="font-size:13px; margin:0;">
                    <b>{sentiment_label}</b> ({sentiment_score:.2f})
                </p>
            </div>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_articles(articles):
    """Render expander for the rest (keeps UI compact)."""
    for article in articles:
        render_article_card(article)

def display_article_results(mid_col, all_articles, empty_topics):
    """Display article results in the middle column."""
    with mid_col:
        if not all_articles and not empty_topics:
            st.info("No articles found for selected topics.")
        else:
            # First display topics with articles
            for topic in all_articles.keys():
                articles = all_articles.get(topic, [])
                with st.expander(f"📰 Articles for {topic}", expanded=True):
                    render_articles(articles)
            
            # Then display empty topics with a message and a warning sign
            for topic in empty_topics:
                with st.expander(f"⚠️ Articles for {topic} (Empty)", expanded=False):
                    st.warning(f"No articles found for '{topic}'. Try a different search term.")

def display_statistics(left_col, right_col, all_articles, sentiment_summary, empty_topics):
    """Display statistical visualizations in the side columns."""
    if not sentiment_summary:
        return
        
    df_summary = pd.DataFrame(sentiment_summary)

    # Left column - Histogram and WordClouds
    with left_col:
        st.subheader("Topic Analysis")
        hist_fig = px.histogram(
            df_summary,
            x="topic",
            color="sentiment",
            barmode="group",
            title="Sentiment Distribution Across Topics",
            text_auto=True,
        )
        st.plotly_chart(hist_fig, use_container_width=True)

        # Generate word cloud for all text combined
        all_text = " ".join([a.get("description", "") for articles in all_articles.values() for a in articles if a.get("description")])
        if all_text.strip():
            st.subheader("Overall Word Cloud")
            wc = WordCloud(width=600, height=300, background_color="white").generate(all_text)
            wc_img = wc.to_image()
            st.image(wc_img, use_container_width=True)
            
            # Generate word cloud for each topic separately
            st.subheader("Word Clouds by Topic")
            
            # First show word clouds for topics with articles
            for topic, articles in all_articles.items():
                topic_text = " ".join([a.get("description", "") for a in articles if a.get("description")])
                if topic_text.strip():
                    with st.expander(f"Word Cloud: {topic}", expanded=False):
                        wc_topic = WordCloud(width=600, height=250, background_color="white").generate(topic_text)
                        wc_topic_img = wc_topic.to_image()
                        st.image(wc_topic_img, use_container_width=True)
            
            # Then show warnings for empty topics
            for topic in empty_topics:
                with st.expander(f"⚠️ Word Cloud: {topic} (No Data)", expanded=False):
                    st.warning(f"No text data available for '{topic}'. Try a different search term.")

    # Right column - Bubble chart and Pie chart
    with right_col:
        st.subheader("Sentiment Overview")
        bubble_rows = []
        
        for topic, articles in all_articles.items():
            scores = [a.get("sentiment", {}).get("scores", {}).get("compound", 0.0) for a in articles if a.get("sentiment")]
            avg_score = sum(scores) / len(scores) if scores else 0.0
            dominant = None
            counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
            for a in articles:
                lbl = a.get("sentiment", {}).get("label")
                if lbl in counts:
                    counts[lbl] += 1
            dominant = max(counts, key=lambda k: counts[k]) if articles else "Neutral"
            bubble_rows.append({"topic": topic, "avg_score": avg_score, "count": len(articles), "dominant_sentiment": dominant})
        df_bubble = pd.DataFrame(bubble_rows)

        bubble_fig = px.scatter(
            df_bubble,
            x="topic",
            y="avg_score",
            size="count",
            color="dominant_sentiment",
            size_max=60,
            title="Avg Sentiment Score per Topic (bubble size = #articles)",
        )
        
        st.plotly_chart(bubble_fig, use_container_width=True)
        
        # Add a new boxplot for article sentiment scores distribution
        scatter_rows = []
        for topic, articles in all_articles.items():
            for i, article in enumerate(articles):
                score = article.get("sentiment", {}).get("scores", {}).get("compound", 0.0)
                sentiment_label = article.get("sentiment", {}).get("label", "Neutral")
                title = article.get("title", "Untitled")
                scatter_rows.append({
                    "topic": topic,
                    "article_index": i + 1,
                    "sentiment_score": score,
                    "sentiment_label": sentiment_label,
                    "title": title[:30] + "..." if len(title) > 30 else title
                })
        
        if scatter_rows:
            df_scatter = pd.DataFrame(scatter_rows)
            box_fig = px.box(
            df_scatter,
            x="topic",
            y="sentiment_score",
            color="topic",
            hover_name="title",
            title="Sentiment Score Distribution per Topic",
            labels={"sentiment_score": "Sentiment Score", "topic": "Topic"},
            points="all"  # Show all points on the boxplot
            )
            box_fig.update_layout(
            height=500,  # Increased height from 400 to 500
            yaxis=dict(
            dtick=0.05,  # Set tick increment to 0.05
            tickformat=".2f"  # Format to show two decimal places
            )
            )
            st.plotly_chart(box_fig, use_container_width=True)

        sentiment_counts = df_summary["sentiment"].value_counts().reset_index()
        sentiment_counts.columns = ["sentiment", "count"]
        pie_fig = px.pie(
            sentiment_counts,
            names="sentiment",
            values="count",
            title="Overall Sentiment Share",
            color="sentiment",
            color_discrete_map={"Positive": "green", "Neutral": "gray", "Negative": "red"},
        )
        st.plotly_chart(pie_fig, use_container_width=True)

def search_and_display_news(topics_list,limit=10):
    """Common function to search and display news for a list of topics"""
    if not topics_list:
        st.warning("Please enter at least one topic.")
        return

    all_articles = {}
    sentiment_summary = []  
    empty_topics = []  # Track topics with no articles
    
    # Phase 1: Collect data
    for topic in topics_list:
        if topic not in st.session_state.articles_cache:
            with st.spinner(f"Searching: {topic}"):
                articles = fetch_articles(topic,limit)
                st.session_state.articles_cache[topic] = articles
        articles = st.session_state.articles_cache.get(topic, [])
        
        if articles:
            all_articles[topic] = articles[:limit]
            for a in articles:
                lbl = a.get("sentiment", {}).get("label")
                if lbl:
                    sentiment_summary.append({"topic": topic, "sentiment": lbl})
        else:
            empty_topics.append(topic)  # Add to empty topics list

    # Create columns layout - always keep this structure
    left_col, mid_col, right_col = st.columns([1, 2, 1])
    
    # Initialize session state if not already present
    if 'show_stats' not in st.session_state:
        st.session_state.show_stats = False
    
   
    
    # Phase 3: Display content based on toggle state
    
    # Always display articles in middle column
    display_article_results(mid_col, all_articles, empty_topics)
    
    # Conditionally display statistics in side columns
    if st.session_state.show_stats and sentiment_summary:
        display_statistics(left_col, right_col, all_articles, sentiment_summary, empty_topics)
    else:
        # Show a simple message when stats are turned off
        left_col.info("Charts are hidden. Enable 'Stats for Nerds' and Search Again to view visualization charts.")
        right_col.info("Charts are hidden. Enable 'Stats for Nerds' and Search Again to view visualization charts.")

    return all_articles
        
with tab_news:
    topics = st_tags(
        label="Enter topics (up to 3):",
        text="Press enter to add a topic",
        value=st.session_state.topics,
        suggestions=[],
        maxtags=3,
        key="topics_input",
    )
    st.session_state.topics = topics[:3]  
    # Phase 2: Add a toggle for stats visibility
    st.session_state.show_stats = st.toggle("📊 Stats for Nerds", value=False, 
                            help="Toggle visualization charts on/off for search results.",key="tab_news_toggle")
    if st.button("Search"):
        search_and_display_news(st.session_state.topics)

with tab_chatbot:
    st.subheader("News Aggregator Chatbot")
    
    # Display a helper message
    st.markdown("Ask the chatbot to find news on any topic")
    
    # Use chat_input instead of text_input for a more chat-like interface
    user_query = st.chat_input(
        placeholder="Find news for...",
        key="chat_query_input"
    )
    st.session_state.show_stats = st.toggle("📊 Stats for Nerds", value=False, 
                            help="Toggle visualization charts on/off",key="chat_bot_toggle")
    # Process the chat input when submitted
    if user_query:
        # Display the user query
        with st.chat_message("user"):
            st.write(f"{user_query}")
        
        # Process and show response
        with st.chat_message("assistant"):
            if "find news" in user_query.lower():
                topic = user_query.lower().strip()
                if topic:
                    st.write(f"🔍 Searching for news about **{topic}**...")
                    all_articles = search_and_display_news([topic],limit=3)
                else:
                    st.warning("Please specify a topic to search for news.")
            else:
                # Treat the input directly as a topic if it doesn't contain "find news"
                st.write(f"🔍 Searching for news about **{user_query}**...")
                all_articles = search_and_display_news([user_query],limit=3)