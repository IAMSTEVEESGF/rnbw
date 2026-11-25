import discord
from discord.ext import commands
import imagehash
from PIL import Image
import io
import os
import datetime

# --- CONFIGURATION ---
TOKEN = os.getenv("DISCORD_TOKEN") # We will put this in Railway later
LOG_CHANNEL_ID = 123456789012345678 # Replace with your mod-log channel ID

# The hashes from the 4 images you provided (Run the script in Step 1 to get the real ones)
KNOWN_SCAM_HASHES = {
    "abcdef1234567890", # Image 1 (MrBeast Tweet)
    "1234567890abcdef", # Image 2 (Repeaterbet Promo Code)
    "fedcba0987654321", # Image 3 (Withdrawal Success Screen)
    "0987654321fedcba"  # Image 4 (Phone holding $5600)
}

intents = discord.Intents.default()
intents.message_content = True # REQUIRED: Must be enabled in Discord Developer Portal
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}. Security Bot is active.")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    # Check if the message has image attachments
    if message.attachments:
        for attachment in message.attachments:
            if attachment.content_type and attachment.content_type.startswith('image'):
                try:
                    # Download the image
                    image_bytes = await attachment.read()
                    img = Image.open(io.BytesIO(image_bytes))
                    
                    # Generate pHash of the uploaded image
                    uploaded_hash = imagehash.phash(img)
                    
                    # Compare against known scam hashes
                    for scam_hash_str in KNOWN_SCAM_HASHES:
                        scam_hash = imagehash.hex_to_hash(scam_hash_str)
                        
                        # Check similarity (0 is identical, higher means more different. 5 is a good threshold)
                        if uploaded_hash - scam_hash <= 5:
                            # SCAM DETECTED!
                            await handle_scam(message, attachment.url)
                            return # Stop checking other images if one matches
                            
                except Exception as e:
                    print(f"Error processing image: {e}")

    await bot.process_commands(message)

async def handle_scam(message, image_url):
    # 1. Delete the message
    try:
        await message.delete()
    except discord.Forbidden:
        print("Missing permissions to delete message.")

    # 2. Timeout the user for 28 days (Discord's maximum limit)
    try:
        duration = datetime.timedelta(days=28)
        await message.author.timeout(duration, reason="Auto-Mod: Posting known MrBeast crypto scam images.")
    except discord.Forbidden:
        print("Missing permissions to timeout user.")

    # 3. Log to a private moderator channel
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        embed = discord.Embed(
            title="🚨 Scam Image Detected & User Muted (28 Days)",
            description=f"**User:** {message.author.mention} ({message.author.id})\n**Channel:** {message.channel.mention}\n**Action Taken:** Message deleted, user timed out for 28 days.\n\n*Please review and issue a permanent ban if necessary.*",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=image_url)
        await log_channel.send(embed=embed)

# Run the bot
bot.run(TOKEN)
