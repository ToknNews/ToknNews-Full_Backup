import os
import time
import json
import requests
from dotenv import load_dotenv
from update_heartbeat import update_field

# Load .env into environment
load_dotenv("/opt/toknnews/.env")

# Static bearer (you can switch back to os.getenv if reusing .env dynamically)
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAAPf5gEAAAAASGluCqNLP02RBDuaEsFP4AI3Yi8=tl0RgXZVhYbKUhVKLqKoB3fSdlwGBtnqMCYrDD1EvlwBKLVlLX"

HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "User-Agent": "ToknNewsBot/1.0"
}
print(f"[DEBUG] BEARER_TOKEN: {BEARER_TOKEN}")
print("[DEBUG] HEADERS:", HEADERS)

URL = "https://api.twitter.com/2/tweets/search/recent"
QUERY = "bitcoin OR ethereum OR solana -is:retweet lang:en"
PARAMS = {
    "query": QUERY,
    "max_results": 100,
    "tweet.fields": "id,text,author_id,created_at"
}

OUTFILE = "/opt/toknnews/data/raw/twitter_latest.json"

def fetch_tweets(max_retries=5, backoff_factor=5):
    for attempt in range(max_retries):
        try:
            response = requests.get(URL, headers=HEADERS, params=PARAMS)
            if response.status_code == 200:
                tweets = response.json()
                os.makedirs(os.path.dirname(OUTFILE), exist_ok=True)
                with open(OUTFILE, "w") as f:
                    json.dump(tweets, f, indent=2)

                print(f"[Twitter] ✅ Collected {len(tweets.get('data', []))} tweets → {OUTFILE}")
                update_field("twitter", "ok")
                return

            elif response.status_code == 429:
                wait_time = backoff_factor * (2 ** attempt)
                print(f"[Twitter] ⚠️ Rate limit hit. Sleeping for {wait_time} seconds...")
                time.sleep(wait_time)
                continue  # Retry

            else:
                print(f"[Twitter] ❌ HTTP error {response.status_code}: {response.text}")
                update_field("twitter", "fail")
                return

        except Exception as e:
            print(f"[Twitter] ❌ Exception: {e}")
            update_field("twitter", "fail")
            return

    print("[Twitter] ❌ Max retries exceeded.")
    update_field("twitter", "fail")

if __name__ == "__main__":
    fetch_tweets()
