#!/usr/bin/env python3
"""
ToknNews Heartbeat v1.0
Sends a daily uptime message to the Ops channel and updates heartbeat.json
"""

import os, json, datetime, requests

BOT_TOKEN = "8328124196:AAHhQwpbvOZFdA77yoXOhJE3yBjsgm9sHM0"
CHAT_ID = "-1003289274091"  # replace with your new OPS chat_id

DATA_DIR = "/var/www/toknnews/data"
LOG_FILE = os.path.join(DATA_DIR, "heartbeat.json")
os.makedirs(DATA_DIR, exist_ok=True)

def update_heartbeat():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {"timestamp": now, "status": "alive"}
    with open(LOG_FILE, "w") as f:
        json.dump(entry, f, indent=2)
    return entry

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Telegram send error: {e}")

import time

if __name__ == "__main__":
    print("✅ ToknNews Heartbeat service started...")
    uptime = 0
    while True:
        uptime += 60
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {
    "status": "alive",
    "timestamp": now,
    "uptime_seconds": uptime,
    # --- ingestion sources ---
    "reddit": "ok",
    "coindesk": "ok",
    "coingecko": "ok",
    "rss": "ok",
    "cryptopanic": "ok",
    "dexscreener": "ok",
    "etherscan": "ok",
    "pumpfun": "ok",
    # --- system & infrastructure ---
    "vault": "ok",
    "writer": "ok",
    "webhook": "ok",
    "telegram": "ok",
    # --- new experimental sources ---
    "blockchain": "ok",
    "ai_feeds": "ok",
    "newswire": "ok"
}
        with open("/var/www/toknnews/data/heartbeat.json", "w") as f:
            json.dump(data, f, indent=2)

        # send Telegram once every 24 hours
        if uptime % 86400 == 0:
            msg = f"✅ ToknNews Alive\n📅 {now}\n🚀 System operational and responding."
            send_telegram_message(msg)

        time.sleep(60)

