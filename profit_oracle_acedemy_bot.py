"""
profit_oracle_bot_multiapi.py
Aggregates crypto news from five APIs and posts to Telegram channel.
Requirements:
  pip install python-telegram-bot==20.12 requests apscheduler
Environment variables:
  BOT_TOKEN           - Telegram bot token from BotFather
  CHANNEL_ID          - e.g. "@ProfitOracleAcademy"
  API_CRYPTONEWS      - Key for CryptoNews-API
  API_NEWSDATA        - Key for NewsData.io
  API_FMP            - Key for Financial Modeling Prep
  API_CRYPTOCONTROL   - Key for CryptoControl
  API_BENZINGA        - Key for Benzinga
  POLL_INTERVAL_MIN   - interval in minutes (default maybe 5)
"""

import os
import time
import argparse
import logging
import sqlite3
import requests
import asyncio
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot
from telegram.constants import ParseMode
from dotenv import load_dotenv

# Load .env file (if present) into environment before reading os.getenv
load_dotenv()

# Config env vars
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# API_CRYPTONEWS = os.getenv("API_CRYPTONEWS", "")
API_NEWSDATA   = os.getenv("API_NEWSDATA", "")
API_FMP        = os.getenv("API_FMP", "")
# API_CRYPTOCONTROL = os.getenv("API_CRYPTOCONTROL", "")
API_BENZINGA   = os.getenv("API_BENZINGA", "")

POLL_INTERVAL_MIN = int(os.getenv("POLL_INTERVAL_MIN", "60"))

# Simple DB for dedupe
DB_PATH = "posted_articles.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS posted (
  id TEXT PRIMARY KEY,
  source TEXT,
  title TEXT,
  posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# Defer creating the Telegram Bot until after we've ensured BOT_TOKEN is available.
# This avoids raising an error during import if BOT_TOKEN is missing.
bot = None

def already_posted(unique_id):
    c.execute("SELECT 1 FROM posted WHERE id = ?", (unique_id,))
    return c.fetchone() is not None

def mark_posted(unique_id, source, title):
    c.execute("INSERT OR IGNORE INTO posted (id, source, title) VALUES (?, ?, ?)", (unique_id, source, title))
    conn.commit()

async def send_to_channel_async(message, link=None, dry_run=False):
    """Send message to Telegram channel asynchronously.

    If dry_run is True, don't actually send — just log the payload.
    Returns True on success (or dry_run), False on failure.
    """
    text = f"{message}\n{link}" if link else message
    logging.debug("Prepared message for channel %s: %s", CHANNEL_ID, text)
    if dry_run:
        logging.info("Dry run enabled — not sending message to Telegram.")
        return True
    if bot is None:
        logging.error("Bot is not initialized. Cannot send message.")
        return False
    try:
        res = await bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode=ParseMode.HTML, disable_web_page_preview=False)
        logging.info("Telegram send_message returned: %s", getattr(res, 'message_id', res))
        return True
    except Exception as e:
        logging.exception("Error sending to Telegram:")
        return False

def send_to_channel(message, link=None, dry_run=False):
    """Send message to Telegram channel.

    If dry_run is True, don't actually send — just log the payload.
    Returns True on success (or dry_run), False on failure.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(send_to_channel_async(message, link, dry_run))
    finally:
        loop.close()

# Fetcher functions


def fetch_newsdata():
    items = []
    if not API_NEWSDATA:
        return items
    url = f"https://newsdata.io/api/1/news?apikey={API_NEWSDATA}&q=crypto&language=en"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        j = r.json()
        for a in j.get("results", [])[:10]:
            uid = "ndio_" + a.get("link", "")
            items.append({
                "id": uid,
                "title": a.get("title"),
                "link": a.get("link"),
                "source": a.get("source_id"),
                "published": a.get("pubDate"),
                "type": "newsdata"
            })
    except Exception as e:
        print("newsdata fetch error:", e)
    return items

def fetch_fmp():
    items = []
    if not API_FMP:
        return items
    # Updated endpoint for crypto news
    url = f"https://financialmodelingprep.com/api/v3/fmp/articles?page=0&size=20&apikey={API_FMP}"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        j = r.json()
        for a in j.get("content", []):
            uid = "fmp_" + str(a.get("id", ""))
            items.append({
                "id": uid,
                "title": a.get("title"),
                "link": a.get("url"),
                "source": a.get("author"),
                "published": a.get("date"),
                "type": "fmp"
            })
    except Exception as e:
        print("fmp fetch error:", e)
    return items


def fetch_benzinga():
    items = []
    if not API_BENZINGA:
        return items
    url = f"https://api.benzinga.com/api/v1/news?token={API_BENZINGA}&category=crypto&limit=20"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        j = r.json()
        for a in j.get("data", [])[:10]:
            uid = "benz_" + str(a.get("id", ""))
            items.append({
                "id": uid,
                "title": a.get("title"),
                "link": a.get("url"),
                "source": "Benzinga",
                "published": a.get("created"),
                "type": "benzinga"
            })
    except Exception as e:
        print("benzinga fetch error:", e)
    return items

def aggregator_job():
    print(f"[{datetime.now().isoformat()}] Aggregator job starting…")
    all_items = []
    # all_items.extend(fetch_cryptonewsapi())
    all_items.extend(fetch_newsdata())
    all_items.extend(fetch_fmp())
    # all_items.extend(fetch_cryptocontrol())
    all_items.extend(fetch_benzinga())

    # dedupe by id
    unique = { it["id"]: it for it in all_items }
    items = list(unique.values())

    # sort by published if possible
    def get_time(it):
        try:
            return datetime.fromisoformat(it["published"].replace("Z","+00:00"))
        except Exception:
            return datetime.now(timezone.utc)
    items.sort(key=get_time, reverse=True)

    posted = 0
    for it in items:
        if already_posted(it["id"]):
            continue
        title = it["title"] or "No title"
        source = it.get("source", "Unknown")
        link = it.get("link")
        pub = it.get("published", "")
        msg = f"<b>{title}</b>\n<i>{source}</i>\n{pub}"
        success = send_to_channel(msg, link)
        if success:
            mark_posted(it["id"], source, title)
            posted += 1
            time.sleep(1.5)
    print(f"Posted {posted} new items.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Profit Oracle Academy aggregator bot")
    parser.add_argument("--dry-run", action="store_true", help="Prepare messages but do not send to Telegram")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if not BOT_TOKEN or not CHANNEL_ID:
        logging.error("Missing BOT_TOKEN or CHANNEL_ID! Put them in the environment or a .env file.")
        exit(1)

    # Create bot now that BOT_TOKEN is present
    try:
        bot = Bot(token=BOT_TOKEN)
    except Exception:
        logging.exception("Failed to create Telegram Bot with provided BOT_TOKEN")
        exit(1)

    # Quick verification: try to getChat to confirm the bot can see the channel and has permission to post
    try:
        chat = bot.get_chat(chat_id=CHANNEL_ID)
        logging.info("Bot can access chat: id=%s title=%s type=%s", getattr(chat, 'id', None), getattr(chat, 'title', None), getattr(chat, 'type', None))
    except Exception:
        logging.exception("Failed to access the chat. Common issues: wrong CHANNEL_ID (use @channelusername), bot not added as admin, or bot blocked from posting.")

    scheduler = BackgroundScheduler()
    # Wrap aggregator_job so it uses the dry_run flag when sending
    def job_wrapper():
        # attach dry_run flag to calls via a small wrapper that monkeypatches send_to_channel
        global send_to_channel
        original_send = send_to_channel
        def send_with_dryrun(message, link=None):
            return original_send(message, link, dry_run=args.dry_run)
        send_to_channel = send_with_dryrun
        try:
            aggregator_job()
        finally:
            send_to_channel = original_send

    scheduler.add_job(job_wrapper, 'interval', minutes=POLL_INTERVAL_MIN, next_run_time=datetime.now())
    scheduler.start()
    logging.info("Aggregator started for channel %s (dry_run=%s)", CHANNEL_ID, args.dry_run)
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logging.info("Shutting down.")
