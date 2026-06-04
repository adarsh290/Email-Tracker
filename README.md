# 📬 Discord Email Agent

An intelligent email agent that monitors a college inbox, uses **Gemini 1.5 Flash** to classify and extract deadlines, and sends interactive notifications to a Discord server — running 24/7 on a cloud server.

## ✨ Features

| Feature | Details |
|---|---|
| 🤖 AI Classification | Sorts emails into **High**, **Mid**, **Low** or silently drops **Spam** |
| 📅 Deadline Extraction | Automatically detects and highlights deadlines from email body |
| 🖱️ Interactive Buttons | **Mark Done** / **Mark Pending** buttons on every Discord message |
| 📎 PDF Attachments | Downloads & attaches PDFs (e.g. mess menu) directly to Discord |
| 📌 Auto-Pin | Mid-priority messages with PDFs are automatically pinned |
| 📊 Daily Summary | Sends a digest of all pending tasks every morning at **8:00 AM IST** |
| 🔁 Deduplication | Uses email `Message-ID` to never double-notify |
| ♻️ Auto-Restart | Runs as a `systemd` service — restarts on crash, starts on boot |

---

## 🗂️ Discord Channel Structure

Create these **4 channels** in your Discord server:

| Channel | Purpose |
|---|---|
| `#high-priority` | Exam results, submissions, Upstop competition alerts |
| `#mid-priority` | Club sessions, mess menu, events & fests |
| `#low-priority` | Seminars with snacks, anything else noteworthy |
| `#summaries` | Daily 8 AM digest of all pending deadlines |

---

## 🔑 Pre-requisites

### 1. Gmail App Password
- Enable **2-Step Verification** on your Google account
- Go directly to: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)  
  *(Search "App passwords" in your Google Account search bar if you can't find it)*
- Generate a password for "Mail" → copy the 16-character code

### 2. Gemini API Key (Free)
- Go to [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
- Click **Create API Key** → copy it

### 3. Discord Bot
1. Go to [discord.com/developers/applications](https://discord.com/developers/applications)
2. Create a new application → go to **Bot** tab
3. Toggle **ON** the **Message Content Intent** under Privileged Gateway Intents
4. Click **Reset Token** → copy the token
5. Go to **OAuth2 → URL Generator**:
   - Check scope: `bot`
   - Check permissions: **Send Messages**, **Embed Links**, **Attach Files**, **Read Message History**
   - Copy the generated URL → paste in browser → invite bot to your server
6. In Discord, enable **Developer Mode** (User Settings → Advanced)
7. Right-click each channel → **Copy Channel ID**

---

## 🚀 Deployment

### On any Linux server (Ubuntu / Fedora / Oracle Cloud)

```bash
# 1. Clone the repo
git clone https://github.com/adarsh290/Email-Tracker.git ~/email-agent
cd ~/email-agent

# 2. Run the setup script (handles venv, packages, systemd automatically)
chmod +x setup.sh
./setup.sh

# 3. Fill in your credentials
nano /opt/email-agent/.env

# 4. Start the bot
sudo systemctl start email-agent.service

# 5. Watch it run
sudo journalctl -u email-agent.service -f
```

> **Note:** The setup script auto-detects your username and Linux package manager (`apt` or `dnf`), so it works on Ubuntu and Fedora alike.

---

## ⚙️ Configuration (`.env`)

Copy `.env.example` to `.env` and fill in your values:

```env
EMAIL_ACCOUNT="your@college.edu"
EMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"
IMAP_SERVER="imap.gmail.com"

GEMINI_API_KEY="your_gemini_key"
IMPORTANCE_PROMPT="..."   # Pre-filled with college-specific rules

DISCORD_BOT_TOKEN="your_bot_token"
CHANNEL_HIGH_PRIORITY="channel_id"
CHANNEL_MID_PRIORITY="channel_id"
CHANNEL_LOW_PRIORITY="channel_id"
CHANNEL_SUMMARIES="channel_id"

FETCH_SINCE_DATE="20-Dec-2025"   # Backfill from this date
POLL_INTERVAL_SECONDS=300         # Check every 5 minutes
```

> 💡 You can update `IMPORTANCE_PROMPT` in `.env` at any time to change what counts as important — no code changes needed.

---

## 🛠️ Useful Commands

```bash
# Check bot status
sudo systemctl status email-agent.service

# Watch live logs
sudo journalctl -u email-agent.service -f

# Restart after editing .env
sudo systemctl restart email-agent.service

# Stop the bot
sudo systemctl stop email-agent.service
```

---

## 📁 Project Structure

```
email-agent/
├── bot.py               # Discord bot: routing, buttons, daily summary
├── email_client.py      # IMAP client: fetch emails & extract PDFs
├── gemini_analyzer.py   # Gemini AI: classify priority, extract deadlines
├── database.py          # SQLite: deduplicate emails, track task status
├── requirements.txt     # Python dependencies
├── .env.example         # Configuration template
├── email-agent.service  # systemd service file
├── setup.sh             # One-command deployment script
└── .gitignore           # Keeps .env and venv out of git
```

---

## 🔒 Security Notes

- **Never commit `.env`** — it's in `.gitignore` for this reason
- Rotate your API keys if you ever accidentally expose them
- The bot token and app password act like passwords — keep them private
