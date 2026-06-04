import discord
from discord.ext import commands, tasks
import os
import asyncio
from datetime import time, timezone, timedelta
from dotenv import load_dotenv
import io

import email_client
import gemini_analyzer
import database

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))

# Channel IDs
CHANNELS = {
    "High": int(os.getenv("CHANNEL_HIGH_PRIORITY", "0")),
    "Mid": int(os.getenv("CHANNEL_MID_PRIORITY", "0")),
    "Low": int(os.getenv("CHANNEL_LOW_PRIORITY", "0")),
    "Summaries": int(os.getenv("CHANNEL_SUMMARIES", "0"))
}

# IST is UTC+5:30
IST_TZ = timezone(timedelta(hours=5, minutes=30))
# Set time for 8:00 AM IST
SUMMARY_TIME = time(hour=8, minute=0, tzinfo=IST_TZ)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

class TaskView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Timeout None for persistent buttons

    @discord.ui.button(label="Mark Done", style=discord.ButtonStyle.green, custom_id="mark_done")
    async def mark_done(self, interaction: discord.Interaction, button: discord.ui.Button):
        database.update_deadline_status(str(interaction.message.id), "Done")
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.set_footer(text="Status: Done")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Mark Pending", style=discord.ButtonStyle.grey, custom_id="mark_pending")
    async def mark_pending(self, interaction: discord.Interaction, button: discord.ui.Button):
        database.update_deadline_status(str(interaction.message.id), "Pending")
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.orange()
        embed.set_footer(text="Status: Pending")
        await interaction.response.edit_message(embed=embed, view=self)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    bot.add_view(TaskView()) # Re-register persistent views
    if not poll_emails.is_running():
        poll_emails.start()
    if not daily_summary.is_running():
        daily_summary.start()

@tasks.loop(seconds=POLL_INTERVAL)
async def poll_emails():
    print("Polling for new emails...")
    try:
        # Run IMAP fetching in a thread so it doesn't block Discord event loop
        emails = await asyncio.to_thread(email_client.fetch_emails)
    except Exception as e:
        print(f"Error fetching emails: {e}")
        return

    for email_data in emails:
        message_id = email_data["message_id"]
        
        if database.is_email_processed(message_id):
            continue

        print(f"Analyzing email: {email_data['subject']}")
        # Run Gemini in a thread
        analysis = await asyncio.to_thread(
            gemini_analyzer.analyze_email,
            email_data["subject"],
            email_data["sender"],
            email_data["date"],
            email_data["body"]
        )

        priority = analysis.get("priority", "Spam")
        
        if priority == "Spam":
            database.mark_email_processed(message_id)
            continue

        channel_id = CHANNELS.get(priority)
        if not channel_id:
            print(f"Warning: No channel ID configured for priority {priority}")
            database.mark_email_processed(message_id)
            continue

        channel = bot.get_channel(channel_id)
        if not channel:
            print(f"Warning: Channel with ID {channel_id} not found.")
            database.mark_email_processed(message_id)
            continue

        embed = discord.Embed(
            title=email_data["subject"][:256],
            description=analysis.get("summary", "No summary provided."),
            color=discord.Color.red() if priority == "High" else (discord.Color.blue() if priority == "Mid" else discord.Color.light_grey())
        )
        embed.add_field(name="From", value=email_data["sender"][:1024], inline=False)
        embed.add_field(name="Date", value=email_data["date"], inline=True)
        
        deadline = analysis.get("deadline")
        if deadline:
            embed.add_field(name="Extracted Deadline", value=deadline, inline=True)
        
        embed.set_footer(text="Status: Pending")

        # Prepare attachments
        discord_files = []
        for att in email_data["attachments"]:
            if att["filename"].lower().endswith('.pdf'):
                discord_files.append(discord.File(fp=io.BytesIO(att["data"]), filename=att["filename"]))

        try:
            view = TaskView()
            msg = await channel.send(embed=embed, files=discord_files, view=view)
            
            # Pin if it's Mid priority and has a PDF (e.g., Mess Menu)
            if priority == "Mid" and discord_files:
                 await msg.pin()

            # Record in DB
            database.mark_email_processed(message_id)
            if deadline:
                database.add_deadline(message_id, analysis.get("summary"), deadline, priority, str(msg.id))
        except Exception as e:
            print(f"Error sending Discord message: {e}")

@tasks.loop(time=SUMMARY_TIME)
async def daily_summary():
    print("Running daily summary...")
    summary_channel_id = CHANNELS.get("Summaries")
    if not summary_channel_id:
        return
        
    channel = bot.get_channel(summary_channel_id)
    if not channel:
        return

    pending_tasks = database.get_pending_deadlines()
    
    if not pending_tasks:
        await channel.send("☕ Good morning! You have no pending deadlines.")
        return

    embed = discord.Embed(
        title="📅 Daily Deadline Summary",
        description="Here are your pending tasks:",
        color=discord.Color.gold()
    )

    for task in pending_tasks:
        # discord_message_id can be used to link back to the original message if we know the channel,
        # but for simplicity we just list them.
        embed.add_field(
            name=f"[{task['priority']}] Deadline: {task['deadline']}", 
            value=task['summary'], 
            inline=False
        )

    await channel.send("☕ Good morning! Here is your daily summary:", embed=embed)

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: DISCORD_BOT_TOKEN not found in environment.")
