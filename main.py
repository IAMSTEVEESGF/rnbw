import discord
from discord.ext import commands
import imagehash
from PIL import Image
import io
import os
import datetime

# --- CONFIGURATION ---
TOKEN = os.getenv("DISCORD_TOKEN") 
LOG_CHANNEL_NAME = "scam-logs" # The bot will create/find this channel automatically

KNOWN_SCAM_HASHES = []

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

# Helper function to find or create the log channel
async def get_or_create_log_channel(guild):
    # Look for the channel
    channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
    if channel:
        return channel
    
    # If it doesn't exist, create it
    try:
        # Create the channel, hidden from everyone except admins and the bot
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await guild.create_text_channel(LOG_CHANNEL_NAME, overwrites=overwrites)
        print(f"✅ Created new log channel: {LOG_CHANNEL_NAME}")
        return channel
    except discord.Forbidden:
        print(f"❌ Missing permissions to create #{LOG_CHANNEL_NAME} channel in {guild.name}. Please check bot permissions.")
        return None

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}. Security Bot is active.")
    
    # 1. Load images
    folder_path = "."
    print("Loading scam images and generating hashes...")
    
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                file_path = os.path.join(folder_path, filename)
                try:
                    img = Image.open(file_path)
                    phash = imagehash.phash(img)
                    KNOWN_SCAM_HASHES.append(phash)
                    print(f"✅ Loaded and hashed: {filename}")
                except Exception as e:
                    print(f"❌ Error loading {filename}: {e}")
                    
    print(f"Loaded {len(KNOWN_SCAM_HASHES)} scam image hashes. Ready to protect the server.")

    # 2. Check/Create log channel in all servers the bot is in
    for guild in bot.guilds:
        await get_or_create_log_channel(guild)

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    if not KNOWN_SCAM_HASHES:
        await bot.process_commands(message)
        return

    if message.attachments:
        for attachment in message.attachments:
            if attachment.content_type and attachment.content_type.startswith('image'):
                try:
                    image_bytes = await attachment.read()
                    img = Image.open(io.BytesIO(image_bytes))
                    uploaded_hash = imagehash.phash(img)
                    
                    for scam_hash in KNOWN_SCAM_HASHES:
                        if uploaded_hash - scam_hash <= 5:
                            await handle_scam(message, attachment.url)
                            return 
                            
                except Exception as e:
                    print(f"Error processing image: {e}")

    await bot.process_commands(message)

async def handle_scam(message, image_url):
    # 1. Delete the message
    try:
        await message.delete()
    except discord.Forbidden:
        print("Missing permissions to delete message.")

    # 2. Timeout the user for 28 days
    try:
        duration = datetime.timedelta(days=28)
        await message.author.timeout(duration, reason="Auto-Mod: Posting known scam images.")
    except discord.Forbidden:
        print("Missing permissions to timeout user.")

    # 3. Log to mod channel
    log_channel = await get_or_create_log_channel(message.guild)
    
    if log_channel:
        embed = discord.Embed(
            title="🚨 Scam Image Detected & User Muted (28 Days)",
            description=f"**User:** {message.author.mention} ({message.author.id})\n**Channel:** {message.channel.mention}\n**Action Taken:** Message deleted, user timed out for 28 days.\n\n*Please review and issue a permanent ban if necessary.*",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=image_url)
        
        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            print(f"❌ Cannot send messages in {log_channel.name}. Check permissions.")

# Run the bot
bot.run(TOKEN)
