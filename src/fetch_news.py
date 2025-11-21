import os
import json
import requests
from datetime import datetime

# Configuration
API_KEY = os.getenv("NEWSDATA_API_KEY")
BASE_URL = "https://newsdata.io/api/1/latest"
# Combined query to save API credits
QUERY = '"Artificial Intelligence" OR "UAP" OR "Archaeology" OR "Paleontology"'

def fetch_news():
    if not API_KEY:
        print("Error: NEWSDATA_API_KEY not set.")
        return

    params = {
        "apikey": API_KEY,
        "q": QUERY,
        "language": "en",
    }

    print(f"Fetching news for: {QUERY}")
    response = requests.get(BASE_URL, params=params)

    if response.status_code != 200:
        print(f"Failed to fetch news: {response.status_code} - {response.text}")
        return

    data = response.json()
    articles = data.get("results", [])

    if not articles:
        print("No articles found.")
        return

    # Normalize to the fields the front‑end expects
    normalized = []
    for item in articles:
        normalized.append({
            "title": item.get("title"),
            "link": item.get("link"),
            "description": item.get("description"),
            "source_id": item.get("source_id"),
            "pubDate": item.get("pubDate"),
        })

    # Ensure directory exists
    os.makedirs("data", exist_ok=True)

    # 1) Write combined file with timestamp (for history / debugging)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    history_filename = f"data/news_{timestamp}.json"
    with open(history_filename, "w") as f:
        json.dump(normalized, f, indent=2)
    print(f"Saved {len(normalized)} articles to {history_filename}")

    # 2) ALSO write to the three files the site already loads
    for name in ["ai.json", "prehistory.json", "uap.json"]:
        path = os.path.join("data", name)
        with open(path, "w") as f:
            json.dump(normalized, f, indent=2)
        print(f"Wrote {len(normalized)} articles to {path}")

if __name__ == "__main__":
    fetch_news()
