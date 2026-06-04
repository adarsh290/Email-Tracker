# Discord Email Agent

An intelligent email agent that monitors a college email inbox, uses the free Gemini 1.5 Flash API to categorize and extract deadlines, and sends interactive notifications to specific Discord channels.

## Features
- **AI Categorization**: Sorts emails into High, Mid, Low priority, or Spam based on a customizable prompt.
- **Deadline Extraction**: Automatically finds and highlights deadlines.
- **Interactive UI**: Discord messages include "Mark Done" and "Mark Pending" buttons to track tasks.
- **PDF Extraction**: Automatically downloads and attaches PDFs (e.g., Mess Menus).
- **Daily Summaries**: Sends a morning digest of all pending tasks at 8:00 AM IST.

## Pre-requisites
1.  **Email App Password**: For Gmail, enable 2-Step Verification and generate an "App Password".
2.  **Gemini API Key**: Get a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
3.  **Discord Bot**:
    - Go to [Discord Developer Portal](https://discord.com/developers/applications).
    - Create a new application and add a Bot.
    - Enable **Message Content Intent** under the Bot tab.
    - Invite the bot to your server.
    - Copy the Bot Token.
    - Create four channels in your server (e.g., `#high-priority`, `#mid-priority`, `#low-priority`, `#summaries`). Right-click them to copy their IDs (you may need to enable Developer Mode in Discord settings).

## Deployment (Oracle Cloud Ubuntu)

1. Upload this entire folder to your Oracle Cloud instance (e.g., via SFTP/SCP or Git).
2. SSH into your instance.
3. Navigate to the uploaded folder.
4. Make the setup script executable:
   ```bash
   chmod +x setup.sh
   ```
5. Run the setup script:
   ```bash
   ./setup.sh
   ```
6. Edit the `.env` file with your credentials:
   ```bash
   nano /opt/email-agent/.env
   ```
7. Start the background service:
   ```bash
   sudo systemctl start email-agent.service
   ```

## Logs
To view the bot running in the background:
```bash
sudo journalctl -u email-agent.service -f
```
