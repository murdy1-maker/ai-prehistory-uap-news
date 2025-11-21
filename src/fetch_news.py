import os
import json
import requests
from datetime import datetime

API_KEY = os.environ.get("NEWSDATA_API_KEY")
BASE_URL = "https://newsdata.io/api/1/news"

# Three focused topics. Each will return up to 5 specific articles.
TOPICS = [
    {
        "name": "Artificial Intelligence",
        "file": "ai.json",
        # Short, title-focused AI query
        "qintitle": 'AI OR "artificial intelligence" OR "machine learning"'
    },
    {
        "name": "Pre-history",
        "file": "prehistory.json",
        # Title must clearly mention archaeology / fossils / ancient
        "qintitle": 'archaeology OR fossil OR "ancient" OR paleontology'
    },
    {
        "name": "UAP",
        "file": "uap.json",
        # Tight UAP query, kept well under length limits
        "qintitle": 'UAP OR UFO OR "alien craft"'
    },
]

DATA_DIR = "data"
MAX_PER_TOPIC = 5  # top N per topic per cycle


def fetch_news_for_topic(qintitle: str):
    """
    Fetch articles from NewsData.io for a single topic,
    using qInTitle for higher relevance.
    """
    if not API_KEY:
        raise RuntimeError("NEWSDATA_API_KEY not set")

    params = {
        "apikey": API_KEY,
        "language": "en",
        "qInTitle": qintitle,
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

    # Newest first, in case API isn’t already sorted
    normalized.sort(key=lambda x: x.get("pubDate") or "", reverse=True)
    return normalized


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    print(f"Running fetch at {timestamp} UTC")

    # Prevent the same URL showing up in multiple topics this cycle
    used_links = set()

    for topic in TOPICS:
        name = topic["name"]
        filename = topic["file"]
        qintitle = topic["qintitle"]

        print(f"\n=== Fetching {name} ===")
        try:
            articles = fetch_news_for_topic(qintitle)
            print(f"Fetched {len(articles)} raw articles for {name}")
        except Exception as e:
            print(f"Error fetching {name}: {e}")
            out_path = os.path.join(DATA_DIR, filename)
            with open(out_path, "w") as f:
                json.dump([], f, indent=2)
            continue

        selected = []
        for item in articles:
            link = item.get("link")
            if not link:
                continue
            if link in used_links:
                continue
            used_links.add(link)
            selected.append(item)
            if len(selected) >= MAX_PER_TOPIC:
                break

        print(f"Selected {len(selected)} unique articles for {name}")

        # Overwrite topic file with this run's top N
        out_path = os.path.join(DATA_DIR, filename)
        with open(out_path, "w") as f:
            json.dump(selected, f, indent=2)

        # Optional per-topic history file (handy for debugging)
        history_name = f"{filename.rstrip('.json')}_{timestamp}.json"
        history_path = os.path.join(DATA_DIR, history_name)
        with open(history_path, "w") as f:
            json.dump(selected, f, indent=2)

        print(f"Wrote {len(selected)} articles to {out_path} and {history_path}")


if __name__ == "__main__":
    main()
