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
    
    if response.status_code == 200:
        data = response.json()
        articles = data.get('results', [])
        
        if articles:
            # Ensure directory exists
            os.makedirs('data', exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"data/news_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(articles, f, indent=2)
            print(f"Saved {len(articles)} articles to {filename}")
        else:
            print("No articles found.")
    else:
        print(f"Failed to fetch news: {response.status_code} - {response.text}")

if __name__ == "__main__":
    fetch_news()
