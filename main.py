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
DEFAULT_SETTINGS = {"enabled": False, "punishment": "timeout", "strikes": 3, "user_strikes": {}}
guild_settings = {}

intents = discord.Intents.default()
intents.message_content = True 
intents.members = True 
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
    match = re.match(r"(\d+)([smhd])", duration_str.lower())
    if not match:
        return None
    amount, unit = match.groups()
    amount = int(amount)
    if unit == 's': return datetime.timedelta(seconds=amount)
    elif unit == 'm': return datetime.timedelta(minutes=amount)
    elif unit == 'h': return datetime.timedelta(hours=amount)
    elif unit == 'd': return datetime.timedelta(days=amount)
    return None

async def send_mod_log(guild, action: str, offender: discord.Member, moderator: discord.Member, duration: str = None, reason: str = "No reason provided"):
    log_channel = await get_log_channel(guild)
    if not log_channel:
        return
    bot_name = bot.user.name
    if bot.user.discriminator != '0': bot_name = f"{bot.user.name}#{bot.user.discriminator}"
    mod_name = moderator.name if moderator else bot_name

    embed = discord.Embed(title=action, color=0xFAA61A) # Carl-bot orange
    embed.add_field(name="Offender", value=f"{offender.name} {offender.mention}", inline=False)
    if duration: embed.add_field(name="Duration", value=duration, inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Responsible moderator", value=mod_name, inline=False)

    try: await log_channel.send(embed=embed)
    except discord.Forbidden: pass

# --- THE AUTOMOD DASHBOARD UI ---

def get_automod_embed(guild):
    settings = guild_settings.get(guild.id, DEFAULT_SETTINGS)
    
    status_text = "on" if settings["enabled"] else "off"
    status_icon = "🟢" if settings["enabled"] else "🔴"
    punish_text = "Ban" if settings["punishment"] == "ban" else "Timeout (28 Days)"
    
    embed = discord.Embed(
        title="🛡️ Auto Mod",
        description=f"Automod is **{status_text}** for **{guild.name}** {status_icon}\n\n"
                    f"**Functions:**\n"
                    f"• Image Scam Filter (MrBeast Crypto Scams)\n\n"
                    f"**Current Settings:**\n"
                    f"• **Punishment:** {punish_text}\n"
                    f"• **Auto-Ban Strikes:** {settings['strikes']}",
        color=discord.Color.green() if settings["enabled"] else discord.Color.red()
    )
    return embed

class AutomodView(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=None)
        self.guild = guild

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You must be an **Administrator** to use this.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Toggle Status", style=discord.ButtonStyle.primary, row=1)
    async def toggle_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.guild.id not in guild_settings:
            guild_settings[self.guild.id] = DEFAULT_SETTINGS.copy()
            guild_settings[self.guild.id]["user_strikes"] = {}
            
        guild_settings[self.guild.id]["enabled"] = not guild_settings[self.guild.id]["enabled"]
        button.style = discord.ButtonStyle.success if guild_settings[self.guild.id]["enabled"] else discord.ButtonStyle.danger
        await interaction.response.edit_message(embed=get_automod_embed(self.guild), view=self)

    @discord.ui.button(label="Change Punishment", style=discord.ButtonStyle.secondary, row=1)
    async def change_punish(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.guild.id not in guild_settings:
            guild_settings[self.guild.id] = DEFAULT_SETTINGS.copy()
            guild_settings[self.guild.id]["user_strikes"] = {}

        current = guild_settings[self.guild.id]["punishment"]
        guild_settings[self.guild.id]["punishment"] = "ban" if current == "timeout" else "timeout"
        await interaction.response.edit_message(embed=get_automod_embed(self.guild), view=self)

    @discord.ui.select(
        placeholder="Set Ban Strikes...",
        options=[
            discord.SelectOption(label="1 Strike", value="1"),
            discord.SelectOption(label="2 Strikes", value="2"),
            discord.SelectOption(label="3 Strikes", value="3"),
            discord.SelectOption(label="5 Strikes", value="5"),
        ],
        row=2
    )
    async def set_strikes(self, interaction: discord.Interaction, select: discord.ui.Select):
        if self.guild.id not in guild_settings:
            guild_settings[self.guild.id] = DEFAULT_SETTINGS.copy()
            guild_settings[self.guild.id]["user_strikes"] = {}

        guild_settings[self.guild.id]["strikes"] = int(select.values[0])
        await interaction.response.edit_message(embed=get_automod_embed(self.guild), view=self)

@bot.hybrid_command(name="automod", description="Open the Auto Mod configuration dashboard.")
@commands.has_permissions(administrator=True)
async def automod(ctx):
    if ctx.guild.id not in guild_settings:
        guild_settings[ctx.guild.id] = DEFAULT_SETTINGS.copy()
        guild_settings[ctx.guild.id]["user_strikes"] = {}

    await ctx.send(embed=get_automod_embed(ctx.guild), view=AutomodView(ctx.guild))

# --- TIMEOUT COMMANDS ---

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

# --- BOT EVENTS & LOGIC ---

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
                except Exception: pass
    print(f"Loaded {len(KNOWN_SCAM_HASHES)} scam image hashes.")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    await bot.process_commands(message)

    settings = guild_settings.get(message.guild.id, DEFAULT_SETTINGS)
    if not settings.get("enabled", False) or not KNOWN_SCAM_HASHES:
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
    try: await message.delete()
    except discord.Forbidden: pass

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
        except discord.Forbidden: pass
    else:
        try:
            duration = datetime.timedelta(days=28)
            await message.author.timeout(duration, reason="Auto-Mod: Posting known scam images.")
            await send_mod_log(message.guild, "timeout", message.author, None, duration="28 days", reason="hacked account (sent mr beast scam)")
        except discord.Forbidden: pass

bot.run(TOKEN)
