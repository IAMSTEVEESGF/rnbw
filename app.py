import socket
# Force IPv4 to prevent Railway boot hangs
_orig_getaddrinfo = socket.getaddrinfo
def getaddrinfo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = getaddrinfo_ipv4

# --- DISCORD BOT ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}', flush=True)

@bot.command()
async def vid(ctx):
    embed = discord.Embed(title="TikTok Video 🎥", description="Click to watch", color=0x2b2d31)
    embed.url = RAILWAY_URL
    embed.set_image(url="https://i.imgur.com/8QOq4w9.jpeg")
    await ctx.send(embed=embed)

def run_bot():
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN missing.", flush=True)
        return
    try:
        print("Starting bot thread...", flush=True)
        bot.run(BOT_TOKEN)
    except Exception as e:
        print(f"BOT CRASHED: {e}", flush=True)

# Start the bot thread immediately on import
threading.Thread(target=run_bot, daemon=True).start()

# Remove the app.run() block entirely. Gunicorn will handle it.
