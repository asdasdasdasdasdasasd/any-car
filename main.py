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
    response = requests.get(CARS_BG_URL, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    listings = []
    for row in soup.select("div.offer_list_item"):
        link_tag = row.find("a", class_="offer_title", href=True)
        if not link_tag:
            continue
        title = link_tag.text.strip()
        url = "https://www.cars.bg" + link_tag['href']
        # Listing ID is in the href: /offer/cars/id/12345678
        try:
            listing_id = link_tag['href'].split('/')[-1]
        except Exception:
            continue
        price_tag = row.find("div", class_="offer_price")
        price = price_tag.text.strip() if price_tag else "No price"
        location_tag = row.find("div", class_="offer_location")
        location = location_tag.text.strip() if location_tag else "Unknown location"
        img_tag = row.find("img", class_="offer_photo", src=True)
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
