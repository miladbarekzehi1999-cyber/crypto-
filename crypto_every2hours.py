# crypto_every2hours.py
import os
import requests
from datetime import datetime
import pytz
import jdatetime
import time
from telegram import Bot

# --- CONFIG ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise SystemExit("BOT_TOKEN and CHAT_ID must be set.")

bot = Bot(token=BOT_TOKEN)

# Coin list with premium emojis
COINS = [
    ("bitcoin", "BTC", "🅱️"),
    ("ethereum", "ETH", "✨"),
    ("tether", "USDT", "💵"),
    ("binancecoin", "BNB", "🔶"),
    ("solana", "SOL", "🟣"),
    ("ripple", "XRP", "🚀"),
    ("usd-coin", "USDC", "🪙"),
    ("cardano", "ADA", "🔷"),
    ("avalanche-2", "AVAX", "🔺"),
    ("dogecoin", "DOGE", "🐶"),
    ("toncoin", "TON", "💎"),
    ("tron", "TRX", "📐"),
]

COINGECKO_SIMPLE_PRICE = "https://api.coingecko.com/api/v3/simple/price"
KABUL = pytz.timezone("Asia/Kabul")

DARI_WEEKDAY = [
    "دوشنبه","سه‌شنبه","چهارشنبه","پنجشنبه",
    "جمعه","شنبه","یکشنبه"
]

TITLE = "📌 *قیمت ارز دیجیتال (به افغانی)*"

# --- Helpers ---
def jalali_date():
    now = datetime.now(KABUL)
    j = jdatetime.datetime.fromgregorian(datetime=now)
    weekday = DARI_WEEKDAY[now.weekday()]
    return f"{j.year}/{j.month:02d}/{j.day:02d} — {weekday}"

def fmt(v):
    try:
        v = float(v)
        if v >= 100:
            return f"{int(v):,}"
        return f"{v:,.2f}"
    except:
        return "—"

def fetch_prices():
    ids = ",".join(c[0] for c in COINS)
    params = {"ids": ids, "vs_currencies": "afn"}

    for attempt in range(3):
        try:
            r = requests.get(COINGECKO_SIMPLE_PRICE, params=params, timeout=10)
            if r.status_code == 200:
                return r.json()
            elif r.status_code in (429,502,503,504):
                time.sleep(2 ** attempt)
                continue
            r.raise_for_status()
        except:
            time.sleep(2 ** attempt)

    return {}

def build_message(include_header=True):
    prices = fetch_prices()
    lines = []

    if include_header:
        lines.append("بسم الله الرحمن الرحیم\n")
        lines.append(f"📅 تاریخ امروز: {jalali_date()}\n")

    lines.append(TITLE + "\n")

    for cid, sym, emo in COINS:
        afn = prices.get(cid, {}).get("afn")
        lines.append(f"{emo} *{sym}*")
        lines.append(f"قیمت: {fmt(afn)} AFN\n")

    return "\n".join(lines)

# --- Schedule check ---
def is_send_time():
    now = datetime.now(KABUL)
    hour = now.hour
    minute = now.minute

    allowed_hours = [7, 9, 11, 13, 15, 17, 19, 21]

    if hour in allowed_hours and minute == 0:
        include_header = (hour == 7)
        return True, include_header

    return False, False

# --- Telegram send ---
def send(text):
    bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")

# --- Main ---
def main():
    should_send, header = is_send_time()
    if not should_send:
        print("Not a scheduled send time.")
        return

    msg = build_message(include_header=header)
    send(msg)
    print("Crypto update sent.")

if __name__ == "__main__":
    main()
