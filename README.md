# 📢 Discord RSS Bot

A simple and efficient Discord bot that fetches RSS feeds and posts updates to a Discord channel via webhooks.

## ✨ Features

- 🔔 **Real-time RSS Updates** – Fetches news and content from multiple RSS feeds.
- 🔄 **Auto-post to Discord** – Sends updates to Discord channels via webhooks.
- 🛠 **Easy Configuration** – Manage RSS feeds and channels with simple commands.
- ⏳ **Adjustable Fetch Intervals** – Set how often the bot checks for new updates.

## 🚀 Getting Started

### 1️⃣ Prerequisites

Ensure you have **Python 3.8+** installed.

### 2️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/discord-rss-bot.git
cd discord-rss-bot
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Set Up Your Environment

Create a `.env` file and add your Discord bot token:

```ini
DISCORD_BOT_TOKEN=your-token-here
```

### 5️⃣ Configure the Bot

Modify `config.json` to add your RSS feeds and webhooks.

Example `config.json`:

```json
{
  "webhooks": {
    "News": "https://discord.com/api/webhooks/your-webhook-url"
  },
  "rss_feeds": {
    "News": ["https://rss.nytimes.com/services/xml/rss/nyt/World.xml"]
  },
  "fetch_interval": 1800,
  "rss_delay": 60
}
```

### 6️⃣ Run the Bot

```bash
python bot.py
```

## 📜 Bot Commands

| Command                       | Description                              |
| ----------------------------- | ---------------------------------------- |
| `!setchannel <category>`      | Set the current channel for RSS updates. |
| `!addrss <category> <url>`    | Add a new RSS feed to a category.        |
| `!removerss <category> <url>` | Remove an RSS feed from a category.      |
| `!listrss`                    | List all configured RSS feeds.           |

## 🔧 Deployment

To run the bot **24/7**, you can host it on:

- [Railway](https://railway.app/)
- [Heroku](https://www.heroku.com/)
- [VPS (DigitalOcean, Linode, AWS)]

## 🛡 License

This project is licensed under the **MIT License** – feel free to use and modify it!

## 🤝 Contributing

Pull requests are welcome! If you have suggestions, feel free to open an issue.

## 📞 Support

If you need help, create an issue in the repository or reach out via Discord.

---

🚀 **Made with ❤️ for the open-source community!**

