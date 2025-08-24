
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


st.set_page_config(page_title="News Aggregator", page_icon="📰", layout="wide")
st.title("📰 Multi-Topic News Aggregator with Sentiment Analysis")
tab_news, tab_chatbot = st.tabs(["News Aggregator", "Chatbot"])

if "topics" not in st.session_state:
    st.session_state.topics = []
if "articles_cache" not in st.session_state:
    st.session_state.articles_cache = {}



SENTIMENT_ICONS = {"Positive": "😊", "Negative": "😠", "Neutral": "😐"}


API_KEY = "AIzaSyBZnwrh5s7s3TMoQ0fkxE6fbkX-AlGaHdw"  
CX = "d5efb0c0edff34023"  


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


def fetch_articles(query: str) -> list:
    """Fetch results from Google Custom Search (news), extract best text, compute sentiment."""
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": CX,
        "q": f"{query} site:news.google.com",
        "num": 10,
    }
    try:
        resp = requests.get(url, params=params, timeout=8)
        data = resp.json()
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
            preview_text = preview_text[:1000].rsplit(" ", 1)[0] + "..."

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
    <a href="{url}" target="_blank" style="text-decoration:none; color:inherit;">
      <div style="
            display:flex; justify-content:space-between; align-items:flex-start;
            border:1px solid #e6e6e6; border-radius:12px; padding:14px; margin-bottom:14px;
            box-shadow: 1px 1px 6px rgba(0,0,0,0.04);
      ">
        <div style="flex:1; margin-right:12px;">
          <h4 style="margin:2px 0 6px 0; font-size:16px; line-height:1.25;">{title}</h4>
          <p style="color:#6b6b6b; font-size:13px; margin:0 0 8px 0;">
            <img src="{favicon}" style="width:16px; height:16px; vertical-align:middle; margin-right:6px; border-radius:3px;">
            <strong style="vertical-align:middle;">{source}</strong>
          </p>
          <p style="margin:6px 0 8px 0; color:#333; font-size:14px;">{description_short}</p>
          <p style="color:#666; font-size:13px; margin:0;">
            Sentiment: {emoji} <b>{sentiment_label}</b> ({sentiment_score:.2f})
          </p>
        </div>
        <div style="flex-shrink:0;">
          <img src="{image}" style="width:140px; height:90px; object-fit:cover; border-radius:8px;">
        </div>
      </div>
    </a>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_articles(articles):
    """Render up to first 3 inline then expander for the rest (keeps UI compact)."""
    for article in articles[:3]:
        render_article_card(article)
    if len(articles) > 3:
        with st.expander("Show more articles"):
            for article in articles[3:]:
                render_article_card(article)
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


    if st.button("Search"):
        if not st.session_state.topics:
            st.warning("Please enter at least one topic (max 3).")
        else:
          
            all_articles = {}
            sentiment_summary = []  
            for topic in st.session_state.topics:
                if topic not in st.session_state.articles_cache:
                    with st.spinner(f"Searching: {topic}"):
                        articles = fetch_articles(topic)
                        st.session_state.articles_cache[topic] = articles
                articles = st.session_state.articles_cache.get(topic, [])
                if articles:
                    all_articles[topic] = articles
                    for a in articles:
                        lbl = a.get("sentiment", {}).get("label")
                        if lbl:
                            sentiment_summary.append({"topic": topic, "sentiment": lbl})

            left_col, mid_col, right_col = st.columns([1, 2, 1])

            if sentiment_summary:
                df_summary = pd.DataFrame(sentiment_summary)

                hist_fig = px.histogram(
                    df_summary,
                    x="topic",
                    color="sentiment",
                    barmode="group",
                    title="Sentiment Distribution Across Topics",
                    text_auto=True,
                )
                left_col.plotly_chart(hist_fig, use_container_width=True, key="hist_left_v1")

                all_text = " ".join([a.get("description", "") for articles in all_articles.values() for a in articles if a.get("description")])
                if all_text.strip():
                    wc = WordCloud(width=600, height=360, background_color="white").generate(all_text)
                    wc_img = wc.to_image()
                    left_col.image(wc_img, use_column_width=True)

            if sentiment_summary:
          
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
                right_col.plotly_chart(bubble_fig, use_container_width=True, key="bubble_right_v1")

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
                right_col.plotly_chart(pie_fig, use_container_width=True, key="pie_right_v1")

            st.markdown('<div class="scrollable-articles">', unsafe_allow_html=True)

            with mid_col:
                if not all_articles:
                    st.info("No articles found for selected topics.")
                else:
                    
                    for topic in st.session_state.topics:
                        articles = all_articles.get(topic, [])
                        if articles:
                            st.subheader(f"📰 Articles for {topic}")
                            render_articles(articles)
with tab_chatbot:
    st.subheader("Smart News Chatbot")
    user_query = st.text_input(
        "Ask me to find news (e.g., 'Find news on Intel stock price')",
        key="chat_query"
    )

    if st.button("Send", key="chat_send_btn") and user_query:
        query_lower = user_query.lower()
        if "find news" in query_lower:
            topic = query_lower.replace("find news on", "").strip()
            if topic:
             
                chatbot_articles = fetch_articles(topic)[:3]
                if chatbot_articles:
                    st.success(f"Here are some articles on '{topic}':")
                    for i, a in enumerate(chatbot_articles, 1):
                       
                        st.markdown(f"{i}. [{a['title']}]({a['url']}) - {a['source']}")
                    st.info("Hope this helps! 😊")
                else:
                    st.warning(f"No news found for '{topic}'")
            else:
                st.warning("Please specify a topic to search for news.")
        else:
            st.info("This chatbot currently only responds to 'Find news on ...' queries.")