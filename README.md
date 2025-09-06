# News Aggregator with Sentiment Analysis
## Streamlit Hosted Site
https://krishhhhh05-ra-task-app-bq02cq.streamlit.app/
## Overview
This is a multi-topic news aggregator application built with Streamlit that fetches news articles from various sources using Google Custom Search API. The application performs sentiment analysis on news articles, visualizes sentiment distribution, and provides a chatbot interface for quick news queries.

## Features
- **Multi-topic News Search**: Search for news on up to 3 different topics
- **Sentiment Analysis**: Automatically analyzes the sentiment of news articles (Positive, Neutral, Negative)
- **Rich Visualizations**: View sentiment distribution, word clouds, and statistical charts
- **Chatbot Interface**: Quick search for news using natural language queries
- **Responsive UI**: Clean article cards with images, summaries, and sentiment indicators

##  Getting Started

### Prerequisites
- Requirements.txt mentioned in the github file


GOOGLE_API_KEY=your_google_api_key
GOOGLE_CX=your_custom_search_engine_id


### Running the Application

streamlit run main.py


##  Technologies Used
- **Streamlit**: For the web interface
- **NLTK VADER**: For sentiment analysis
- **BeautifulSoup**: For web scraping article content
- **WordCloud**: For generating word clouds
- **Plotly**: For interactive charts and visualizations
- **Google Custom Search API**: For fetching news articles

##  Available Visualizations
- Sentiment distribution across topics (histogram)
- Word clouds for each topic
- Overall sentiment share (pie chart)
- Average sentiment score per topic (bubble chart)
- Sentiment score distribution (box plot)

##  How It Works
1. User enters up to three topics or uses the chatbot to search for news
2. Application fetches news articles using Google Custom Search API
3. Each article's content is analyzed for sentiment using NLTK VADER
4. Results are displayed as article cards with sentiment indicators
5. Optional statistical visualizations show sentiment trends and patterns



