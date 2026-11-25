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
guild_settings = {}

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

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
    
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    
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

# --- THE COMMAND (WORKS AS !imagescam AND /imagescam) ---
@bot.hybrid_command(name="imagescam", description="Enable or disable the automated scam image filter.")
@commands.has_permissions(administrator=True)
async def imagescam(ctx, state: str):
    guild_id = ctx.guild.id
    embed = discord.Embed()

    if state.lower() == "on":
        guild_settings[guild_id] = True
        embed.description = "✅ **Scam Protection Enabled.** The bot will now automatically delete matching scam images and timeout the users who post them."
        embed.color = discord.Color.green()
    elif state.lower() == "off":
        guild_settings[guild_id] = False
        embed.description = "❌ **Scam Protection Disabled.** The bot will no longer monitor for these images."
        embed.color = discord.Color.red()
    else:
        embed.description = "Invalid option. Please use `/imagescam on` or `/imagescam off`."
        embed.color = discord.Color.orange()
        
    await ctx.send(embed=embed)

@imagescam.error
async def imagescam_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            description="❌ You must be an **Administrator** to use this command.",
            color=discord.Color.red()
        )
        # Ephemeral makes it so only the user who typed it sees the error
        await ctx.send(embed=embed, ephemeral=True)

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    await bot.process_commands(message)

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
    # 1. Delete the message
    try:
        await message.delete()
    except discord.Forbidden:
        print("Missing permissions to delete message.")

    # 2. Timeout the user (28 days)
    try:
        duration = datetime.timedelta(days=28)
        await message.author.timeout(duration, reason="Auto-Mod: Posting known scam images.")
    except discord.Forbidden as e:
        print(f"❌ TIMEOUT FAILED: {e}. The bot's role is likely lower than the user's role, or it lacks the 'Moderate Members' permission.")

    # 3. Send Custom Log Embed
    log_channel = await get_log_channel(message.guild)
    if log_channel:
        # Get bot name for the "Responsible moderator" field
        bot_name = bot.user.name
        if bot.user.discriminator != '0': 
            bot_name = f"{bot.user.name}#{bot.user.discriminator}"

        # Recreating the format from your screenshot
        embed = discord.Embed(
            title="timeout",
            color=0xFAA61A # A nice orange/yellow to match the screenshot
        )
        
        embed.add_field(name="Offender", value=f"{message.author.name} {message.author.mention}", inline=False)
        embed.add_field(name="Duration", value="28 days", inline=False)
        embed.add_field(name="Reason", value="hacked account (sent mr beast scam)", inline=False)
        embed.add_field(name="Responsible moderator", value=bot_name, inline=False)

        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
             print(f"❌ Cannot send messages in #{log_channel.name}. Check permissions.")

bot.run(TOKEN)
