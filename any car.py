import requests
from bs4 import BeautifulSoup
import time
import os

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = "7696676472:AAE6xFtU4v-QTaYOZBND21VEThls17ssoQc"
TELEGRAM_CHAT_ID = "-4939922320"
MOBILE_BG_URL = "https://www.mobile.bg/"
CHECK_INTERVAL = 120  # seconds

SEEN_IDS_FILE = "seen_ids.txt"

def get_seen_ids():
    if not os.path.exists(SEEN_IDS_FILE):
        return set()
    with open(SEEN_IDS_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f.readlines())

def save_seen_ids(seen_ids):
    with open(SEEN_IDS_FILE, "w", encoding="utf-8") as f:
        for id in seen_ids:
            f.write(f"{id}\n")

def get_latest_listings():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(MOBILE_BG_URL, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    listings = []
    for a in soup.select('a.link-offer-title[href^="/obiava-"]'):
        title = a.text.strip()
        url = "https://www.mobile.bg" + a['href']
        try:
            listing_id = a['href'].split('obiava-')[1].split('-')[0]
        except Exception:
            continue
        offer_div = a.find_parent('div.offer')
        price_tag = offer_div.find('div', class_='offer-price') if offer_div else None
        price = price_tag.text.strip() if price_tag else "No price"
        location_tag = offer_div.find('div', class_='offer-location') if offer_div else None
        location = location_tag.text.strip() if location_tag else "Unknown location"
        img_tag = offer_div.find('img', src=True) if offer_div else None
        img_url = img_tag['src'] if img_tag else None

        listings.append({
            "id": listing_id,
            "title": title,
            "url": url,
            "price": price,
            "location": location,
            "img_url": img_url
        })
    return listings

def send_telegram_message(bot_token, chat_id, text, img_url=None):
    if img_url:
        url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
        data = {
            "chat_id": chat_id,
            "caption": text,
            "parse_mode": "Markdown"
        }
        try:
            img_resp = requests.get(img_url, stream=True, timeout=10)
            files = {"photo": img_resp.raw}
            requests.post(url, data=data, files=files, timeout=20)
        except Exception as e:
            print(f"Failed to send photo: {e} - Sending text only.")
            requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                data={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
            )
    else:
        requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        )

def main():
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
                try:
                    send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, text, img_url=car['img_url'])
                except Exception as e:
                    print(f"Failed to send listing: {e}")
                print(f"Sent new listing: {car['title']} ({car['id']})")
                seen_ids.add(car["id"])
                new_found = True

        if new_found:
            save_seen_ids(seen_ids)
        else:
            print("No new listings found.")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
