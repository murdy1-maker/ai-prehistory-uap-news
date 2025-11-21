import os
import json
from datetime import datetime
from pathlib import Path
import requests

API_KEY = os.environ.get("NEWSDATA_API_KEY")
BASE_URL = "https://newsdata.io/api/1/latest"

TOPICS = {
    "ai": "artificial intelligence OR AI OR machine learning",
    "prehistory": "prehistory OR paleolithic OR neolithic OR archaeology",
    "uap": "UAP OR UFO OR unidentified anomalous phenomena",
}

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

def fetch_topic(topic_key: str, query: str):
    params = {
        "apikey": API_KEY,
        "q": query,
        "language": "en",
        "full_content": 0,
    }
    resp = requests.get(BASE_URL, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    
    normalized = []
    for item in results:
        normalized.append({
            "title": item.get("title"),
            "description": item.get("description"),
            "link": item.get("link"),
            "source_id": item.get("source_id"),
            "pubDate": item.get("pubDate"),
            "category": item.get("category"),
            "image_url": item.get("image_url"),
            "fetched_at": datetime.utcnow().isoformat() + "Z",
        })
    return normalized

def merge_with_existing(path: Path, new_items):
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            existing = json.load(f)
    else:
        existing = []

    seen = {item.get("link") for item in existing if item.get("link")}
    for item in new_items:
        link = item.get("link")
        if link and link not in seen:
            existing.append(item)
            seen.add(link)

    if len(existing) > 200:
        existing = existing[-200:]

    with path.open("w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

def main():
    if not API_KEY:
        raise RuntimeError("NEWSDATA_API_KEY not set")

    for key, query in TOPICS.items():
        print(f"Fetching {key}: {query}")
        items = fetch_topic(key, query)
        out_path = DATA_DIR / f"{key}.json"
        merge_with_existing(out_path, items)
        print(f"Saved {len(items)} articles to {out_path}")

if __name__ == "__main__":
    main()
