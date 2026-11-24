import discord
from discord.ext import commands
import aiohttp
import string
import itertools
import os
import asyncio

TOKEN = os.environ.get("DISCORD_TOKEN") 

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# a-z and 0-9 only
CHARSET = string.ascii_lowercase + string.digits
available_usernames = []
tested_count = 0

async def check_username(session, username):
    url = f"https://discord.com/api/v9/invites/{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    try:
        async with session.get(url, headers=headers, timeout=5) as resp:
            if resp.status == 404:
                return True # 404 means the invite is unknown, username is likely free
            elif resp.status == 429:
                # If we hit a rate limit, wait exactly as long as Discord tells us to
                retry = (await resp.json()).get("retry_after", 2.0)
                await asyncio.sleep(retry)
                return False
            else:
                return False # 200 means it exists
    except Exception:
        return False

@bot.event
async def on_ready():
    print(f"[*] Logged in as {bot.user}")

@bot.command()
async def hunt3(ctx):
    await ctx.send("```[*] Starting 3-character hunt...```")
    await run_hunt(ctx, 3)

@bot.command()
async def hunt4(ctx):
    await ctx.send("```[*] Starting 4-character hunt...```")
    await run_hunt(ctx, 4)

async def run_hunt(ctx, length):
    global tested_count, available_usernames
    tested_count = 0
    available_usernames = []
    
    combinations = itertools.product(CHARSET, repeat=length)
    queue = asyncio.Queue()
    
    for combo in combinations:
        queue.put_nowait(''.join(combo))

    total_to_test = queue.qsize()
    await ctx.send(f"```[*] Generated {total_to_test} combinations. Starting...```")

    async with aiohttp.ClientSession() as session:
        
        async def worker():
            global tested_count
            while not queue.empty():
                username = await queue.get()
                
                if await check_username(session, username):
                    available_usernames.append(username)
                    await ctx.send(f"**AVAILABLE:** `{username}`")
                
                tested_count += 1
                if tested_count % 500 == 0:
                    print(f"[*] Tested {tested_count}/{total_to_test}...")
                
                queue.task_done()
                # 0.5 second delay keeps us under the rate limit
                await asyncio.sleep(0.5)

        await worker()

    await ctx.send(f"```[*] Hunt complete. Tested {tested_count}. Found {len(available_usernames)}.```")

if __name__ == "__main__":
    bot.run(TOKEN)
