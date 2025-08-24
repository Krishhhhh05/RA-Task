import requests

API_KEY = "AIzaSyBZnwrh5s7s3TMoQ0fkxE6fbkX-AlGaHdw"
CX = "d5efb0c0edff34023"  # your custom search engine ID

def google_search(query, num=10):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": CX,
        "q": f"{query} site:news.google.com",
        "num": num   # number of results (max 10 per request)
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data.get("items", [])

# Example usage
results = google_search("trump")
for item in results:
    print(item["title"], "-", item["link"])
