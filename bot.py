import discord
import feedparser
import aiohttp
import asyncio
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timezone

# Discord bot token
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")  # Load from environment variable

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

CONFIG_FILE = "config.json"
SEEN_ENTRIES_FILE = "seen_entries.json"
DEFAULT_CONFIG = {
    "channels": {},  # Dictionary mapping categories to channel IDs
    "fetch_interval": 1800,  # 30 minutes
    "rss_feeds": {},  # Dictionary mapping categories to lists of RSS URLs
    "rss_delay": 60  # Delay between feeds
}

# Load configuration
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
else:
    config = DEFAULT_CONFIG

# Load seen entries
if os.path.exists(SEEN_ENTRIES_FILE):
    with open(SEEN_ENTRIES_FILE, "r", encoding="utf-8") as f:
        seen_entries = json.load(f)
else:
    seen_entries = {}


async def send_webhook(category, title, link):
    webhook_url = config["webhooks"].get(category)
    if not webhook_url:
        print(f"⚠️ No webhook found for {category}, skipping...")
        return
    
    payload = {
        "username": category + " Bot",  # Dynamic bot name
        "content": f"**{title}**\n{link}"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(webhook_url, json=payload) as response:
            if response.status == 204:
                print(f"✅ Sent news to {category}")
            else:
                print(f"❌ Failed to send news to {category}, Status: {response.status}")

def save_config():
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

def save_seen_entries():
    with open(SEEN_ENTRIES_FILE, "w", encoding="utf-8") as f:
        json.dump(seen_entries, f, indent=2)

async def fetch_rss():
    await client.wait_until_ready()

    while not client.is_closed():
        for category, rss_urls in config["rss_feeds"].items():
            for rss_url in rss_urls:
                feed = feedparser.parse(rss_url)

                if not feed.entries:
                    print(f"⚠️ No entries found for {rss_url}")
                    continue

                # Handle missing 'published_parsed' safely
                sorted_entries = sorted(feed.entries, key=lambda e: getattr(e, "published_parsed", None) or datetime.min, reverse=True)

                latest_entry = sorted_entries[0]
                if latest_entry.link not in seen_entries:
                    title = f"**{latest_entry.title}**"
                    link = latest_entry.link

                    await send_webhook(category, title, link)

                    # Save seen entry
                    seen_entries[latest_entry.link] = str(datetime.now(timezone.utc))
                    save_seen_entries()

                await asyncio.sleep(config["rss_delay"])  # Delay between feeds

        await asyncio.sleep(config["fetch_interval"])  # Global fetch delay



@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
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

    elif command == "!addrss" and len(args) == 2:
        category, rss_url = args
        if category not in config["rss_feeds"]:
            config["rss_feeds"][category] = []
        if rss_url not in config["rss_feeds"][category]:
            config["rss_feeds"][category].append(rss_url)
            save_config()
            await message.channel.send(f"✅ RSS feed added to **{category}**: {rss_url}")
        else:
            await message.channel.send("⚠️ This RSS feed is already added.")

    elif command == "!removerss" and len(args) == 2:
        category, rss_url = args
        if category in config["rss_feeds"] and rss_url in config["rss_feeds"][category]:
            config["rss_feeds"][category].remove(rss_url)
            save_config()
            await message.channel.send(f"✅ RSS feed removed from **{category}**: {rss_url}")
        else:
            await message.channel.send("⚠️ RSS feed not found in this category.")

    elif command == "!listrss":
        if not config["rss_feeds"]:
            await message.channel.send("⚠️ No RSS feeds added.")
        else:
            response = "📜 **RSS Feeds by Category:**\n"
            for category, feeds in config["rss_feeds"].items():
                response += f"\n**{category}:**\n" + "\n".join(f"🔹 {feed}" for feed in feeds)
            await message.channel.send(response)

client.run(TOKEN)
