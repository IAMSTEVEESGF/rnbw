import discord
from discord.ext import commands
import aiohttp
import string
import itertools
import os
import asyncio
import random

TOKEN = os.environ.get("DISCORD_TOKEN") 

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

CHARSET = string.ascii_lowercase + string.digits
available_usernames = []
tested_count = 0
global_cooldown = 0.3 

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
]

async def check_username_real(session, username):
    global global_cooldown
    url = "https://discord.com/api/v9/auth/register"
    
    payload = {
        "username": username,
        "email": f"{username}@example.com",
        "password": "P@ssw0rd123!",
        "captcha_key": "dummy",
        "consent": True
    }
    
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Content-Type": "application/json",
        "Accept": "*/*"
    }

    if global_cooldown > 0.5:
        await asyncio.sleep(global_cooldown)

    try:
        async with session.post(url, json=payload, headers=headers, timeout=10) as resp:
            data = await resp.json()
            
            if resp.status == 400:
                errors = data.get("errors", {})
                if "username" in errors:
                    if global_cooldown > 0.3:
                        global_cooldown -= 0.1
                    return False
                return True
            
            elif resp.status == 429:
                retry = data.get("retry_after", 5.0)
                global_cooldown = min(global_cooldown + 1.0, 10.0)
                await asyncio.sleep(retry)
                return False
                
            return False
    except Exception:
        return False

@bot.event
async def on_ready():
    print(f"[*] Logged in as {bot.user}")

@bot.command()
async def hunt3(ctx):
    await ctx.send("```[*] Starting TURBO 3-char hunt...```")
    await run_hunt(ctx, 3)

@bot.command()
async def hunt4(ctx):
    await ctx.send("```[*] Starting TURBO 4-char hunt...```")
    await run_hunt(ctx, 4)

async def run_hunt(ctx, length):
    global tested_count, available_usernames, global_cooldown
    tested_count = 0
    available_usernames = []
    global_cooldown = 0.3 
    
    combinations = itertools.product(CHARSET, repeat=length)
    queue = asyncio.Queue()
    
    for combo in combinations:
        queue.put_nowait(''.join(combo))

    total_to_test = queue.qsize()
    await ctx.send(f"```[*] Generated {total_to_test} combinations. Ripping at 0.3s/check...```")

    connector = aiohttp.TCPConnector(ssl=False, limit=20)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        
        async def worker():
            global tested_count
            while not queue.empty():
                username = await queue.get()
                
                if await check_username_real(session, username):
                    available_usernames.append(username)
                    await ctx.send(f"**AVAILABLE:** `{username}`")
                    # THE FIX: Sleep 2 seconds ONLY when a hit is found to prevent Discord channel spam
                    await asyncio.sleep(2.0) 
                
                tested_count += 1
                if tested_count % 500 == 0:
                    print(f"[*] Tested {tested_count}/{total_to_test} | Cooldown: {global_cooldown:.2f}s")
                
                queue.task_done()
                await asyncio.sleep(0.3)

        await worker()

    await ctx.send(f"```[*] Hunt complete. Tested {tested_count}. Found {len(available_usernames)}.```")

if __name__ == "__main__":
    bot.run(TOKEN)
