import requests
import feedparser

def get_crypto_rss():
    url = "https://cryptopanic.com/api/developer/v2/posts/?auth_token=YOUR_KEY_HERE&currencies=BTC,ETH&filter=rising&format=rss&public=true"
    feed = feedparser.parse(url)

    stories = []
    for entry in feed.entries:
        stories.append({
            "headline": entry.title,
            "source": "CryptoPanic-RSS"
        })

    return stories
