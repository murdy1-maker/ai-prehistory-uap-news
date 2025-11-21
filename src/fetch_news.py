import os
import json
import requests
from datetime import datetime

API_KEY = os.environ.get("NEWSDATA_API_KEY")
BASE_URL = "https://newsdata.io/api/1/news"

# Three separate topic queries so each category has its own focused feed
TOPICS = [
    {
        "name": "Artificial Intelligence",
        "file": "ai.json",
        # Focused AI terms
        "query": '"artificial intelligence" OR "AI model" OR "machine learning" OR "neural network"'
    },
    {
        "name": "Pre-history",
        "file": "prehistory.json",
        # Prehistory / archaeology / fossils
        "query": 'archaeology OR "ancient civilization" OR prehistoric OR fossil OR paleontology'
    },
    {
        "name": "UAP",
        "file": "uap.json",
        # Short UAP query (well under NewsData.io 100‑char q limit)
        "query": 'uap OR ufo OR "alien craft" OR "alien ship"'
    },
]

DATA_DIR = "data"
MAX_PER_TOPIC = 5  # top N per topic per run


def fetch_news(query: str):
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

    # Sort newest first by pubDate if available; API often sends newest first already
    normalized.sort(key=lambda x: x.get("pubDate") or "", reverse=True)
    return normalized


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    print(f"Running fetch at {timestamp} UTC")

    # Track links globally so the same article is not reused across topics this cycle
    used_links = set()

    for topic in TOPICS:
        name = topic["name"]
        filename = topic["file"]
        query = topic["query"]

        print(f"\n=== Fetching {name} ===")
        try:
            articles = fetch_news(query)
            print(f"Fetched {len(articles)} raw articles for {name}")
        except Exception as e:
            print(f"Error fetching {name}: {e}")
            # Write an empty list so front‑end shows 'no articles' instead of stale data
            out_path = os.path.join(DATA_DIR, filename)
            with open(out_path, "w") as f:
                json.dump([], f, indent=2)
            continue

        topic_articles = []
        for item in articles:
            link = item.get("link")
            if not link:
                continue
            if link in used_links:
                continue
            used_links.add(link)
            topic_articles.append(item)
            if len(topic_articles) >= MAX_PER_TOPIC:
                break

        print(f"Selected {len(topic_articles)} unique articles for {name}")

        # Overwrite the topic file with just this run's top N for that topic
        out_path = os.path.join(DATA_DIR, filename)
        with open(out_path, "w") as f:
            json.dump(topic_articles, f, indent=2)

        # Optional per‑topic history file for debugging
        history_name = f"{filename.rstrip('.json')}_{timestamp}.json"
        history_path = os.path.join(DATA_DIR, history_name)
        with open(history_path, "w") as f:
            json.dump(topic_articles, f, indent=2)
        print(f"Wrote {len(topic_articles)} articles to {out_path} and {history_path}")


if __name__ == "__main__":
    main()
