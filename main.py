import discord
from discord.ext import commands
import imagehash
from PIL import Image
import io
import os
import datetime

# --- CONFIGURATION ---
TOKEN = os.getenv("DISCORD_TOKEN") 
LOG_CHANNEL_NAME = "scam-logs"

KNOWN_SCAM_HASHES = []

# Dictionary to keep track of which servers have the protection turned on
guild_settings = {}

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

# Helper function to find, create, or fallback to a log channel
async def get_log_channel(guild):
    channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
    if channel:
        return channel
    try:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await guild.create_text_channel(LOG_CHANNEL_NAME, overwrites=overwrites)
        return channel
    except discord.Forbidden:
        if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
            return guild.system_channel
        for c in guild.text_channels:
            if c.permissions_for(guild.me).send_messages:
                return c
        return None

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}. Security Bot is active.")
    
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

    for guild in bot.guilds:
        await get_log_channel(guild)

# --- THE TOGGLE COMMAND ---
@bot.command()
@commands.has_permissions(administrator=True) # Only admins can turn it on/off
async def mrbeast(ctx, state: str = None):
    guild_id = ctx.guild.id
    
    if state is None:
        await ctx.reply("Usage: `!mrbeast on` or `!mrbeast off`")
        return

    if state.lower() == "on":
        guild_settings[guild_id] = True
        await ctx.reply("✅ **MrBeast Scam Protection is now ON.** I will delete and mute anyone posting the scam images.")
    elif state.lower() == "off":
        guild_settings[guild_id] = False
        await ctx.reply("❌ **MrBeast Scam Protection is now OFF.**")
    else:
        await ctx.reply("Please use `!mrbeast on` or `!mrbeast off`")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    # Check if the command was used
    await bot.process_commands(message)

    # Check if protection is enabled for this server (Default is False if they haven't used the command yet)
    if not guild_settings.get(message.guild.id, False):
        return

    if not KNOWN_SCAM_HASHES:
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

async def handle_scam(message, image_url):
    # 1. Delete
    try:
        await message.delete()
    except discord.Forbidden:
        print("Missing permissions to delete message.")

    # 2. Timeout (Mute)
    try:
        duration = datetime.timedelta(days=28)
        await message.author.timeout(duration, reason="Auto-Mod: Posting known scam images.")
    except discord.Forbidden as e:
        print(f"❌ MUTE FAILED: {e}. The bot's role is likely lower than the user's role, or it lacks the 'Moderate Members' permission.")
    except Exception as e:
         print(f"❌ MUTE FAILED: {e}")

    # 3. Log
    log_channel = await get_log_channel(message.guild)
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
             print(f"❌ Cannot send messages in #{log_channel.name}. Check permissions.")

# Run the bot
bot.run(TOKEN)
