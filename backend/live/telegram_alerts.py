#!/usr/bin/env python3
"""
TOKNNews Telegram Alert System
Sends live status or error alerts to your monitoring channel.
"""

import os, json, requests, time

BOT_TOKEN = "8328124196:AAHhQwpbvOZFdA77yoXOhJE3yBjsgm9sHM0"
CHAT_ID = "-4951469407"
DATA_DIR = "/var/www/toknnews/data"
HEARTBEAT_PATH = os.path.join(DATA_DIR, "heartbeat.json")

def send_alert(message: str):
    """Send a text message to Telegram."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=payload, timeout=10)
        if r.status_code == 200:
            print("[Telegram] ✅ Alert sent.")
        else:
            print(f"[Telegram] ⚠️ Failed ({r.status_code}): {r.text}")
    except Exception as e:
        print("[Telegram] ❌ Error:", e)

def alert_from_heartbeat():
    """Read heartbeat.json and push status to Telegram."""
    if not os.path.exists(HEARTBEAT_PATH):
        send_alert("⚠️ No heartbeat file found on ToknNews system.")
        return
    try:
        hb = json.load(open(HEARTBEAT_PATH))
        ts = hb.get("timestamp", "")
        status = hb.get("status", "")
        headline = hb.get("last_headline", "")
        sentiment = hb.get("sentiment", "")
        runtime = hb.get("runtime_seconds", "")
        msg = (
            f"🩺 <b>TOKNNews Heartbeat</b>\n"
            f"⏰ {ts}\n"
            f"📰 <b>{headline}</b>\n"
            f"🎭 Sentiment: {sentiment}\n"
            f"⏱ Runtime: {runtime}s\n"
            f"📈 Status: {status}\n"
        )
        if status != "success":
            msg += f"❌ Error: {hb.get('last_error','')}"
        send_alert(msg)
    except Exception as e:
        send_alert(f"❌ Failed to read heartbeat: {e}")

if __name__ == "__main__":
    alert_from_heartbeat()
