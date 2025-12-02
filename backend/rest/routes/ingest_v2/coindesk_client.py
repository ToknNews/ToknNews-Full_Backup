# coindesk_client.py
import requests
from backend.rest.routes.ingest_v2.api_rate_limiter import can_call, register_call, register_failure
from backend.runtime.vault_loader import load_secrets

# Load secrets to get the CoinDesk API key (if available)
secrets = load_secrets()
COINDESK_KEY = secrets.get("coindesk_api_key", "")

# Base URL for CoinDesk News API (returns latest articles in English)
BASE_URL = "https://data-api.coindesk.com/news/v1/article/list"
# Use a recognizable User-Agent to avoid request blocking
HEADERS = {"User-Agent": "Mozilla/5.0 (ToknNews Ingest Bot)"}

def fetch_coindesk_articles(limit=10):
    """Fetch the latest CoinDesk articles (default limit=10). Returns a list of article dicts."""
    # Respect rate limiting: check if we can call the CoinDesk source now
    if not can_call("coindesk"):
        return []
    # Prepare query parameters
    params = {"lang": "EN", "limit": limit}
    if COINDESK_KEY:
        params["api_key"] = COINDESK_KEY  # Include API key if available
    try:
        # Make the GET request to CoinDesk API
        response = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=10)
        if response.status_code == 200:
            register_call("coindesk")  # log successful call for rate limiting
            data = response.json()
            # The API returns articles under a key, which could be "Data" or "articles"
            articles = data.get("Data") or data.get("articles") or []
            return articles
        else:
            # Log non-200 responses for debugging
            print(f"[Coindesk] API error: {response.status_code} - {response.text[:200]}")
            register_failure("coindesk")
            return []
    except Exception as e:
        # Handle request exceptions (network issues, timeouts, etc.)
        print(f"[Coindesk] Request failed: {e}")
        register_failure("coindesk")
        return []

def fetch_all_coindesk(max_pages=3, per_page=10):
    """
    Fetch multiple pages of CoinDesk articles for broader ingestion.
    max_pages: number of pages to fetch
    per_page: articles per page (limit per request)
    Returns a combined list of articles (deduplicated by title).
    """
    all_articles = []
    page = 1
    while page <= max_pages:
        # Prepare parameters for this page
        params = {"lang": "EN", "limit": per_page, "page": page}
        if COINDESK_KEY:
            params["api_key"] = COINDESK_KEY
        try:
            response = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=10)
            if response.status_code != 200:
                print(f"[Coindesk] Page {page} fetch failed ({response.status_code}). Stopping pagination.")
                break  # stop if any page fails to load
            data = response.json()
            page_articles = data.get("Data") or data.get("articles") or []
            if not page_articles:
                break  # no articles on this page, end of list
            all_articles.extend(page_articles)
            # If we received fewer articles than requested, it's the last page
            if len(page_articles) < per_page:
                break
            page += 1  # move to next page
        except Exception as e:
            print(f"[Coindesk] Exception on page {page}: {e}")
            break

    # Deduplicate articles by title (to avoid repeats across pages)
    seen_titles = set()
    unique_articles = []
    for art in all_articles:
        title = art.get("TITLE") or art.get("title")
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_articles.append(art)
    return unique_articles
