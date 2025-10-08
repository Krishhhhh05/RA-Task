# News Aggregator with Sentiment Analysis
## Streamlit Hosted Site
https://krishhhhh05-ra-task-app-bq02cq.streamlit.app/
<img width="1778" height="472" alt="Screenshot 2025-10-08 103033" src="https://github.com/user-attachments/assets/06f9c287-edde-47aa-9dd4-b24353ed1d7b" />
<img width="1847" height="873" alt="ra2" src="https://github.com/user-attachments/assets/a908b57e-7e74-4ee1-8f83-bda0b43db498" />

## Overview
This is a multi-topic news aggregator application built with Streamlit that fetches news articles from various sources using Google Custom Search API. The application performs sentiment analysis on news articles, visualizes sentiment distribution, and provides a chatbot interface for quick news queries.

## Features
- **Multi-topic News Search**: Search for news on up to 3 different topics
<img width="1847" height="807" alt="ra3" src="https://github.com/user-attachments/assets/400a36b6-b180-4ddc-9e50-2d20f95b0ff3" />

- **Sentiment Analysis**: Automatically analyzes the sentiment of news articles (Positive, Neutral, Negative)
  <img width="441" height="631" alt="ra5" src="https://github.com/user-attachments/assets/b4c0587d-94a1-4dd9-a868-f4f372899a58" />

- **Rich Visualizations**: View sentiment distribution, word clouds, and statistical charts
<img width="511" height="806" alt="ra4" src="https://github.com/user-attachments/assets/fe35e5b9-bb49-445d-b0cf-04f9ccafef5e" />
<img width="441" height="631" alt="ra5" src="https://github.com/user-attachments/assets/3a5787ee-95de-4325-9b27-6ea8b9b66707" />
<img width="491" height="637" alt="ra6" src="https://github.com/user-attachments/assets/28f595a9-cdbe-4d17-b24e-fcd003d24a33" />

- **Chatbot Interface**: AI based Quick search for news using natural language queries
<img width="1777" height="815" alt="ra7" src="https://github.com/user-attachments/assets/96dd82bb-e047-44f1-a275-629df7906c4a" />
<img width="1778" height="472" alt="Screenshot 2025-10-08 103033" src="https://github.com/user-attachments/assets/97992025-fba5-426a-8d9e-f75b95c4242e" />


- **Responsive UI**: Clean article cards with images, summaries, and sentiment indicators



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

### Prerequisites
- Requirements.txt mentioned in the github file


GOOGLE_API_KEY=your_google_api_key
GOOGLE_CX=your_custom_search_engine_id


### Running the Application

streamlit run main.py


