import discord
import feedparser
import aiohttp
import asyncio
import json
import os
import logging
from dotenv import load_dotenv
from datetime import datetime, timezone

# Setup logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")  # Ensure the token is set

if not TOKEN:
    logging.error("❌ DISCORD_BOT_TOKEN is missing in .env file!")
    exit(1)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

CONFIG_FILE = "config.json"
SEEN_ENTRIES_FILE = "seen_entries.json"
DEFAULT_CONFIG = {
    "channels": {},
    "fetch_interval": 1800,  # 30 min
    "rss_feeds": {},
    "rss_delay": 60,
    "webhooks": {}
}

# Load configuration with error handling
try:
    if os.path.exists(CONFIG_FILE) and os.stat(CONFIG_FILE).st_size > 0:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        logging.warning("⚠️ Config file not found or empty. Using default config.")
        config = DEFAULT_CONFIG
except json.JSONDecodeError:
    logging.error("❌ Config file is corrupted. Resetting to default.")
    config = DEFAULT_CONFIG

# Load seen entries with error handling
try:
    if os.path.exists(SEEN_ENTRIES_FILE) and os.stat(SEEN_ENTRIES_FILE).st_size > 0:
        with open(SEEN_ENTRIES_FILE, "r", encoding="utf-8") as f:
            seen_entries = json.load(f)
    else:
        logging.warning("⚠️ Seen entries file not found or empty. Creating a new one.")
        seen_entries = {}
except json.JSONDecodeError:
    logging.error("❌ Seen entries file is corrupted. Resetting.")
    seen_entries = {}


def save_config():
    """Save the configuration file safely."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logging.error(f"❌ Failed to save config file: {e}")


def save_seen_entries():
    """Save the seen entries file safely."""
    try:
        with open(SEEN_ENTRIES_FILE, "w", encoding="utf-8") as f:
            json.dump(seen_entries, f, indent=2)
    except Exception as e:
        logging.error(f"❌ Failed to save seen entries file: {e}")


async def send_webhook(category, title, link):
    """Send RSS updates to the webhook."""
    webhook_url = config["webhooks"].get(category)

    if not webhook_url:
        logging.warning(f"⚠️ No webhook found for {category}, skipping...")
        return

    payload = {
        "username": f"{category} Bot",
        "content": f"**{title}**\n{link}"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(webhook_url, json=payload) as response:
                if response.status == 204:
                    logging.info(f"✅ Sent news to {category}")
                else:
                    logging.error(f"❌ Failed to send news to {category}. Status: {response.status} | {await response.text()}")
        except Exception as e:
            logging.error(f"❌ Error sending webhook for {category}: {e}")


async def fetch_rss():
    """Fetch and process RSS feeds."""
    await client.wait_until_ready()

    while not client.is_closed():
        logging.info("🔄 Fetching RSS feeds...")

        for category, rss_urls in config["rss_feeds"].items():
            for rss_url in rss_urls:
                try:
                    feed = feedparser.parse(rss_url)

                    if not feed.entries:
                        logging.warning(f"⚠️ No entries found for {rss_url}")
                        continue

                    sorted_entries = sorted(feed.entries, key=lambda e: getattr(e, "published_parsed", None) or datetime.min, reverse=True)
                    latest_entry = sorted_entries[0]

                    if latest_entry.link not in seen_entries:
                        title = latest_entry.title
                        link = latest_entry.link

                        await send_webhook(category, title, link)

                        # Save seen entry
                        seen_entries[latest_entry.link] = str(datetime.now(timezone.utc))
                        save_seen_entries()

                    await asyncio.sleep(config["rss_delay"])
                except Exception as e:
                    logging.error(f"❌ Error processing RSS feed {rss_url}: {e}")

        logging.info(f"⏳ Sleeping for {config['fetch_interval']} seconds before next fetch...")
        await asyncio.sleep(config["fetch_interval"])


@client.event
async def on_ready():
    logging.info(f"✅ Logged in as {client.user}")
    client.loop.create_task(fetch_rss())


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    parts = message.content.split()
    if len(parts) < 2:
        return

    command, *args = parts

    if command == "!setchannel" and len(args) == 1:
        category = args[0]
        config["channels"][category] = message.channel.id
        save_config()
        await message.channel.send(f"✅ RSS updates for **{category}** will be sent here.")
        logging.info(f"📌 Set channel for {category} to {message.channel.id}")

    elif command == "!addrss" and len(args) == 2:
        category, rss_url = args
        if category not in config["rss_feeds"]:
            config["rss_feeds"][category] = []
        if rss_url not in config["rss_feeds"][category]:
            config["rss_feeds"][category].append(rss_url)
            save_config()
            await message.channel.send(f"✅ RSS feed added to **{category}**: {rss_url}")
            logging.info(f"➕ Added RSS feed: {rss_url} to category {category}")
        else:
            await message.channel.send("⚠️ This RSS feed is already added.")
            logging.warning(f"⚠️ RSS feed {rss_url} already exists in {category}")

    elif command == "!removerss" and len(args) == 2:
        category, rss_url = args
        if category in config["rss_feeds"] and rss_url in config["rss_feeds"][category]:
            config["rss_feeds"][category].remove(rss_url)
            save_config()
            await message.channel.send(f"✅ RSS feed removed from **{category}**: {rss_url}")
            logging.info(f"❌ Removed RSS feed {rss_url} from category {category}")
        else:
            await message.channel.send("⚠️ RSS feed not found in this category.")
            logging.warning(f"⚠️ Attempted to remove non-existing RSS feed {rss_url} from {category}")

    elif command == "!listrss":
        if not config["rss_feeds"]:
            await message.channel.send("⚠️ No RSS feeds added.")
            logging.warning("⚠️ No RSS feeds configured.")
        else:
            response = "📜 **RSS Feeds by Category:**\n"
            for category, feeds in config["rss_feeds"].items():
                response += f"\n**{category}:**\n" + "\n".join(f"🔹 {feed}" for feed in feeds)
            await message.channel.send(response)
            logging.info("📜 Listed all RSS feeds.")

client.run(TOKEN)
