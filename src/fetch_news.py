import os
import json
import requests
from datetime import datetime

API_KEY = os.environ.get("NEWSDATA_API_KEY")
BASE_URL = "https://newsdata.io/api/1/news"

# Three separate topic queries so each category has its own feed
TOPICS = [
    {
        "name": "Artificial Intelligence",
        "file": "ai.json",
        "query": '"artificial intelligence" OR "AI" OR "machine learning" OR "neural network"'
    },
    {
        "name": "Pre-history",
        "file": "prehistory.json",
        "query": '"archaeology" OR "prehistoric" OR "paleolithic" OR "neolithic" OR "paleontology"'
    },
    {
        "name": "UAP",
        "file": "uap.json",
        "query": '"UAP" OR "UFO" OR "unidentified aerial phenomenon" OR "unidentified anomalous phenomenon" OR "alien spacecraft"'
    },
]

DATA_DIR = "data"


def fetch_news(query):
    """Fetch articles from NewsData.io for a single query."""
    if not API_KEY:
        raise RuntimeError("NEWSDATA_API_KEY not set")

    params = {
        "apikey": API_KEY,
        "q": query,
        "language": "en",
    }

    res = requests.get(BASE_URL, params=params, timeout=30)
    if res.status_code != 200:
        raise RuntimeError(f"NewsData.io error {res.status_code}: {res.text}")

    data = res.json()
    raw_articles = data.get("results", []) or []

    normalized = []
    for item in raw_articles:
        normalized.append(
            {
                "title": item.get("title"),
                "link": item.get("link"),
                "description": item.get("description"),
                "source_id": item.get("source_id"),
                "pubDate": item.get("pubDate"),
            }
        )
    return normalized


def merge_with_existing(path, new_items):
    """Merge new articles with existing, avoiding duplicates by link, keep latest 300."""
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                existing = json.load(f)
                if not isinstance(existing, list):
                    existing = []
        except Exception:
            existing = []
    else:
        existing = []

    seen = {item.get("link") for item in existing if isinstance(item, dict)}
    for item in new_items:
        link = item.get("link")
        if link and link not in seen:
            existing.append(item)
            seen.add(link)

    # Keep only the 300 most recent by pubDate order (fallback to append order)
    existing.sort(key=lambda x: x.get("pubDate") or "", reverse=True)
    return existing[:300]


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    print(f"Running fetch at {timestamp} UTC")

    for topic in TOPICS:
        name = topic["name"]
        filename = topic["file"]
        query = topic["query"]

        print(f"\n=== Fetching {name} ===")
        articles = fetch_news(query)
        print(f"Fetched {len(articles)} raw articles for {name}")

        out_path = os.path.join(DATA_DIR, filename)
        merged = merge_with_existing(out_path, articles)
        print(f"After merge, {len(merged)} total articles for {name}")

        with open(out_path, "w") as f:
            json.dump(merged, f, indent=2)

        # Optional per-topic history file for debugging
        history_name = f"{filename.rstrip('.json')}_{timestamp}.json"
        history_path = os.path.join(DATA_DIR, history_name)
        with open(history_path, "w") as f:
            json.dump(articles, f, indent=2)
        print(f"Wrote latest batch ({len(articles)}) to {history_path}")


if __name__ == "__main__":
    main()
