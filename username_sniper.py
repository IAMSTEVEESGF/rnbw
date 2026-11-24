# language: Python, file: gift_scraper.py
# Requires: pip install discord.py aiohttp beautifulsoup4

import discord
from discord.ext import commands
import aiohttp
import re
import os
import asyncio
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
TOKEN = os.environ.get("DISCORD_TOKEN") 
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GIFT_REGEX = re.compile(r'discord\.gift/([a-zA-Z0-9]{16})')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/vnd.github.v3+json"
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

async def test_code(session, code):
    url = f"https://discord.com/api/v9/entitlements/gift-codes/{code}?with_application=false&with_subscription_plan=true"
    try:
        async with session.get(url, timeout=5) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("uses", 0) < data.get("max_uses", 1):
                    return True
    except Exception:
        pass
    return False

@bot.event
async def on_ready():
    print(f"[*] Logged in as {bot.user}")

@bot.command()
async def scrape(ctx):
    """Triggers a manual scrape."""
    await ctx.send("```[*] Scraping GitHub for Discord gifts...```")
    
    found_codes = []
    connector = aiohttp.TCPConnector(ssl=False)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        # Search GitHub
        url = "https://api.github.com/search/code?q=discord.gift&per_page=20"
        try:
            async with session.get(url, headers=HEADERS) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for item in data.get("items", []):
                        raw_url = item["html_url"].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                        async with session.get(raw_url) as raw_resp:
                            if raw_resp.status == 200:
                                text = await raw_resp.text()
                                matches = GIFT_REGEX.findall(text)
                                for code in matches:
                                    if await test_code(session, code):
                                        found_codes.append(code)
        except Exception as e:
            await ctx.send(f"```Error searching GitHub: {e}```")
            
        # Search Gists
        url = "https://gist.github.com/discover"
        try:
            async with session.get(url, headers=HEADERS) as resp:
                if resp.status == 200:
                    soup = BeautifulSoup(await resp.text(), "html.parser")
                    links = [f"https://gist.github.com{a['href']}/raw" for a in soup.find_all("a", href=True) if a['href'].count('/') == 2]
                    for link in set(links[:10]):
                        async with session.get(link) as raw_resp:
                            if raw_resp.status == 200:
                                text = await raw_resp.text()
                                matches = GIFT_REGEX.findall(text)
                                for code in matches:
                                    if await test_code(session, code):
                                        found_codes.append(code)
        except Exception as e:
            await ctx.send(f"```Error scraping Gists: {e}```")

    if found_codes:
        await ctx.send(f"**Found {len(found_codes)} valid codes!**\n" + "\n".join([f"https://discord.gift/{c}" for c in found_codes]))
    else:
        await ctx.send("No valid codes found in this cycle.")

if __name__ == "__main__":
    if not TOKEN:
        print("Missing DISCORD_TOKEN in Railway variables.")
    else:
        bot.run(TOKEN)
