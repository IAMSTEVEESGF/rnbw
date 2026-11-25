import discord
from discord.ext import commands
import imagehash
from PIL import Image
import io
import os
import datetime
import re

# --- CONFIGURATION ---
TOKEN = os.getenv("DISCORD_TOKEN") 
LOG_CHANNEL_NAME = "scam-logs"

KNOWN_SCAM_HASHES = []
# Structure: {guild_id: {"enabled": True, "punishment": "timeout", "strikes": 3, "user_strikes": {user_id: count}}}
guild_settings = {}

intents = discord.Intents.default()
intents.message_content = True 
intents.members = True # Required for timeouts/bans
bot = commands.Bot(command_prefix="!", intents=intents)

# --- HELPER FUNCTIONS ---

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

def parse_duration(duration_str: str):
    """Parses strings like 10m, 2h, 28d into a timedelta."""
    match = re.match(r"(\d+)([smhd])", duration_str.lower())
    if not match:
        return None
    amount, unit = match.groups()
    amount = int(amount)
    
    if unit == 's':
        return datetime.timedelta(seconds=amount)
    elif unit == 'm':
        return datetime.timedelta(minutes=amount)
    elif unit == 'h':
        return datetime.timedelta(hours=amount)
    elif unit == 'd':
        return datetime.timedelta(days=amount)
    return None

async def send_mod_log(guild, action: str, offender: discord.Member, moderator: discord.Member, duration: str = None, reason: str = "No reason provided"):
    log_channel = await get_log_channel(guild)
    if not log_channel:
        return

    bot_name = bot.user.name
    if bot.user.discriminator != '0': 
        bot_name = f"{bot.user.name}#{bot.user.discriminator}"
        
    mod_name = moderator.name if moderator else bot_name

    embed = discord.Embed(title=action, color=0xFAA61A) # Carl-bot orange
    
    embed.add_field(name="Offender", value=f"{offender.name} {offender.mention}", inline=False)
    if duration:
        embed.add_field(name="Duration", value=duration, inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Responsible moderator", value=mod_name, inline=False)

    try:
        await log_channel.send(embed=embed)
    except discord.Forbidden:
        pass

# --- BOT EVENTS ---

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}. Security Bot is active.")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    
    folder_path = "."
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                try:
                    img = Image.open(os.path.join(folder_path, filename))
                    KNOWN_SCAM_HASHES.append(imagehash.phash(img))
                except Exception:
                    pass
    print(f"Loaded {len(KNOWN_SCAM_HASHES)} scam image hashes.")

# --- AUTOMOD COMMANDS ---

@bot.hybrid_group(name="automod", description="Configure the Automod settings.", invoke_without_command=True)
@commands.has_permissions(administrator=True)
async def automod(ctx):
    embed = discord.Embed(
        title="Automod Configuration",
        description="Use the subcommands to configure:\n"
                    "`/automod toggle <on/off>`\n"
                    "`/automod punishment <timeout/ban>`\n"
                    "`/automod strikes <number>`",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

@automod.command(name="toggle", description="Turn the scam image filter on or off.")
async def automod_toggle(ctx, state: str):
    gid = ctx.guild.id
    if gid not in guild_settings:
        guild_settings[gid] = {"enabled": False, "punishment": "timeout", "strikes": 3, "user_strikes": {}}
        
    if state.lower() == "on":
        guild_settings[gid]["enabled"] = True
        embed = discord.Embed(description="✅ **Scam Image Filter Enabled.**", color=discord.Color.green())
    elif state.lower() == "off":
        guild_settings[gid]["enabled"] = False
        embed = discord.Embed(description="❌ **Scam Image Filter Disabled.**", color=discord.Color.red())
    else:
        embed = discord.Embed(description="Please use `on` or `off`.", color=discord.Color.orange())
    await ctx.send(embed=embed)

@automod.command(name="punishment", description="Set what happens when a scam image is caught.")
async def automod_punishment(ctx, action: str):
    gid = ctx.guild.id
    if gid not in guild_settings:
        guild_settings[gid] = {"enabled": False, "punishment": "timeout", "strikes": 3, "user_strikes": {}}
        
    if action.lower() in ["timeout", "ban"]:
        guild_settings[gid]["punishment"] = action.lower()
        embed = discord.Embed(description=f"✅ **Punishment set to `{action.lower()}`.**", color=discord.Color.green())
    else:
        embed = discord.Embed(description="Please use `timeout` or `ban`.", color=discord.Color.orange())
    await ctx.send(embed=embed)

@automod.command(name="strikes", description="Ban user after X amount of deleted scam images.")
async def automod_strikes(ctx, amount: int):
    gid = ctx.guild.id
    if gid not in guild_settings:
        guild_settings[gid] = {"enabled": False, "punishment": "timeout", "strikes": 3, "user_strikes": {}}
        
    guild_settings[gid]["strikes"] = amount
    embed = discord.Embed(description=f"✅ **User will be auto-banned if they reach `{amount}` scam strikes.**", color=discord.Color.green())
    await ctx.send(embed=embed)

# Error handler for automod commands
@automod.error
async def automod_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=discord.Embed(description="❌ You must be an **Administrator** to use this.", color=discord.Color.red()), ephemeral=True)

# --- TIMEOUT / REMOVE TIMEOUT COMMANDS ---

@bot.hybrid_command(name="timeout", description="Timeout a member.")
@commands.has_permissions(moderate_members=True)
async def timeout_cmd(ctx, member: discord.Member, duration: str, *, reason: str = "No reason provided"):
    td = parse_duration(duration)
    if not td:
        return await ctx.send(embed=discord.Embed(description="❌ Invalid duration. Use `10m`, `1h`, `28d`.", color=discord.Color.red()), ephemeral=True)
    
    if td > datetime.timedelta(days=28):
        return await ctx.send(embed=discord.Embed(description="❌ Discord max timeout is `28d`.", color=discord.Color.red()), ephemeral=True)

    try:
        await member.timeout(td, reason=reason)
        await ctx.send(embed=discord.Embed(description=f"✅ **{member.mention}** has been timed out for `{duration}`.", color=discord.Color.green()))
        await send_mod_log(ctx.guild, "timeout", member, ctx.author, duration=duration, reason=reason)
    except discord.Forbidden:
        await ctx.send(embed=discord.Embed(description="❌ I cannot timeout this user. My role is too low.", color=discord.Color.red()), ephemeral=True)

@bot.hybrid_command(name="removetimeout", description="Remove a timeout from a member.")
@commands.has_permissions(moderate_members=True)
async def removetimeout_cmd(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    try:
        await member.timeout(None, reason=reason)
        await ctx.send(embed=discord.Embed(description=f"✅ Timeout removed for **{member.mention}**.", color=discord.Color.green()))
        await send_mod_log(ctx.guild, "timeout removed", member, ctx.author, reason=reason)
    except discord.Forbidden:
        await ctx.send(embed=discord.Embed(description="❌ I cannot modify this user.", color=discord.Color.red()), ephemeral=True)

# --- MESSAGE EVENT (AUTOMOD LOGIC) ---

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    await bot.process_commands(message)

    # Check if automod is enabled for this guild
    settings = guild_settings.get(message.guild.id, {})
    if not settings.get("enabled", False):
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
                            await handle_scam(message, attachment.url, settings)
                            return 
                except Exception as e:
                    print(f"Error processing image: {e}")

async def handle_scam(message, image_url, settings):
    # 1. Delete the message
    try:
        await message.delete()
    except discord.Forbidden:
        pass

    # 2. Track Strikes
    user_id = message.author.id
    if user_id not in settings["user_strikes"]:
        settings["user_strikes"][user_id] = 0
    settings["user_strikes"][user_id] += 1
    
    strikes = settings["user_strikes"][user_id]
    punishment = settings["punishment"]
    max_strikes = settings["strikes"]

    # 3. Apply Punishment
    if strikes >= max_strikes or punishment == "ban":
        try:
            await message.author.ban(reason="Auto-Mod: Posting known scam images.")
            await send_mod_log(message.guild, "ban", message.author, None, reason="hacked account (sent mr beast scam)")
        except discord.Forbidden:
            pass
    else:
        try:
            duration = datetime.timedelta(days=28)
            await message.author.timeout(duration, reason="Auto-Mod: Posting known scam images.")
            await send_mod_log(message.guild, "timeout", message.author, None, duration="28 days", reason="hacked account (sent mr beast scam)")
        except discord.Forbidden:
            pass

bot.run(TOKEN)
