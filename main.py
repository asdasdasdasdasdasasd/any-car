from flask import Flask
import threading
import requests
from bs4 import BeautifulSoup
import time
import os

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = "7696676472:AAE6xFtU4v-QTaYOZBND21VEThls17ssoQc"
TELEGRAM_CHAT_ID = "-4939922320"
CARS_BG_URL = "https://www.cars.bg/cars?order=newest"
CHECK_INTERVAL = 10  # seconds

SEEN_IDS_FILE = "seen_ids_cars_bg.txt"

# Flask app
app = Flask(__name__)

@app.route("/")
def index():
    return "Bot is running!", 200

def get_seen_ids():
    ...

def save_seen_ids(seen_ids):
    ...

def get_latest_listings():
    ...

def send_telegram_message(bot_token, chat_id, text, img_url=None):
    ...

def run_bot():
    seen_ids = get_seen_ids()
    print(f"Loaded {len(seen_ids)} seen listings.")

    while True:
        print("Checking for new listings...")
        try:
            listings = get_latest_listings()
        except Exception as e:
            print(f"Failed to scrape: {e}")
            time.sleep(CHECK_INTERVAL)
            continue

        new_found = False
        for car in listings:
            if car["id"] not in seen_ids:
                text = (
                    f"🚗 *{car['title']}*\n"
                    f"💶 {car['price']}\n"
                    f"📍 {car['location']}\n"
                    f"🔗 [Link]({car['url']})"
                )
                send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, text, img_url=car['img_url'])
                seen_ids.add(car["id"])
                new_found = True

        if new_found:
            save_seen_ids(seen_ids)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    # Start bot in separate thread
    threading.Thread(target=run_bot, daemon=True).start()
    # Start Flask server on default port 5000
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
