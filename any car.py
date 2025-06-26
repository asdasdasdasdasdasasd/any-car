import time
import requests
from bs4 import BeautifulSoup
import telegram

# == CONFIG ==
MOBILE_BG_URL = "https://www.mobile.bg/obiavi/avtomobili-dzhipove/namira-se-v-balgariya"
TELEGRAM_TOKEN = "<YOUR_BOT_TOKEN>"
CHAT_ID = -4939922320
CHECK_INTERVAL = 300  # seconds (5 minutes)
# == /CONFIG ==

bot = telegram.Bot(token=TELEGRAM_TOKEN)
seen_ads = set()

def fetch_listings():
    resp = requests.get(MOBILE_BG_URL, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    # Each ad block has data-adid attribute
    ads = []
    for ad in soup.select("div[class*='list-item']"):
        adid = ad.get("data-ad-id")
        if not adid:
            continue
        title = ad.select_one("h3") or ad.select_one("a")
        title_text = title.get_text(strip=True) if title else "No title"
        link_el = ad.select_one("a[href*='/obiavi/']")
        link = "https://www.mobile.bg" + link_el["href"] if link_el else MOBILE_BG_URL
        price_el = ad.select_one("span[class*='price']")
        price = price_el.get_text(strip=True) if price_el else "No price"
        ads.append((adid, title_text, price, link))
    return ads

def main():
    print("🚀 Bot started, monitoring:", MOBILE_BG_URL)
    while True:
        try:
            ads = fetch_listings()
            for adid, title, price, link in ads:
                if adid not in seen_ads:
                    seen_ads.add(adid)
                    msg = f"🚗 *New listing spotted!*\n*{title}*\n💰 {price}\n🔗 {link}"
                    bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode=telegram.ParseMode.MARKDOWN)
            time.sleep(CHECK_INTERVAL)
        except Exception as e:
            print("Error:", e)
            time.sleep(60)

if __name__ == "__main__":
    main()
