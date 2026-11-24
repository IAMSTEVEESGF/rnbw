# language: Python, file: gift_scraper.py, target: Railway / Linux, Python 3.10+
# Requires: pip install aiohttp colorama
#
# How it works:
# 1. Hits the GitHub REST API for recent commits containing "discord.gift/".
# 2. Hits public Pastebin scraping endpoints.
# 3. Extracts the 16-character code using regex.
# 4. Tests the code against Discord's API to see if it's unclaimed.
# 5. Sends valid codes to your webhook.

import asyncio
import aiohttp
import re
import os
import random
from colorama import Fore, init

init(autoreset=True)

# --- CONFIGURATION ---
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
# GitHub Personal Access Token (optional, but raises rate limits from 10 to 30 req/min)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

GIFT_REGEX = re.compile(r'discord\.gift/([a-zA-Z0-9]{16})')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/vnd.github.v3+json"
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

async def test_code(session, code):
    """Tests if a found code is valid and unclaimed."""
    url = f"https://discord.com/api/v9/entitlements/gift-codes/{code}?with_application=false&with_subscription_plan=true"
    
    # We test from the main IP. If we get blocked, we sleep.
    try:
        async with session.get(url, timeout=5) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("uses", 0) < data.get("max_uses", 1):
                    print(f"\n{Fore.GREEN}[!!!] VALID UNCLAIMED CODE: discord.gift/{code}")
                    await send_webhook(session, code)
                    return True
            elif resp.status == 429:
                retry = (await resp.json()).get("retry_after", 5.0)
                print(f"{Fore.YELLOW}[!] Discord rate limit. Sleeping {retry}s")
                await asyncio.sleep(retry)
    except Exception:
        pass
    return False

async def send_webhook(session, code):
    if not WEBHOOK_URL: return
    payload = {"content": f"Valid Nitro Gift: https://discord.gift/{code}"}
    try:
        async with session.post(WEBHOOK_URL, json=payload) as resp:
            pass
    except Exception:
        pass

async def scrape_github(session):
    """Scrapes recent GitHub commits for gift codes."""
    # Search for recent commits mentioning discord.gift
    url = "https://api.github.com/search/commits?q=discord.gift&sort=committer-date&order=desc&per_page=50"
    
    try:
        async with session.get(url, headers=HEADERS) as resp:
            if resp.status == 403:
                print(f"{Fore.RED}[!] GitHub rate limit hit. Need a GITHUB_TOKEN.")
                return
            if resp.status != 200:
                return
                
            data = await resp.json()
            items = data.get("items", [])
            
            for item in items:
                # Get the actual patch/diff of the commit to find the code
                commit_url = item["url"]
                async with session.get(commit_url, headers=HEADERS) as commit_resp:
                    if commit_resp.status == 200:
                        commit_data = await commit_resp.json()
                        files = commit_data.get("files", [])
                        for file in files:
                            patch = file.get("patch", "")
                            matches = GIFT_REGEX.findall(patch)
                            for code in matches:
                                print(f"{Fore.CYAN}[*] Found code in GitHub: {code}")
                                await test_code(session, code)
                                
    except Exception as e:
        print(f"{Fore.RED}[!] GitHub scrape error: {e}")

async def scrape_pastebin(session):
    """Scrapes Pastebin's public archive for codes."""
    # Pastebin has an API, but scraping the archive is easier for recent dumps
    url = "https://pastebin.com/archive"
    try:
        async with session.get(url) as resp:
            if resp.status != 200: return
            
            text = await resp.text()
            # Find recent paste IDs
            paste_ids = re.findall(r'href="/([a-zA-Z0-9]{8})"', text)
            
            for paste_id in set(paste_ids): # Deduplicate
                raw_url = f"https://pastebin.com/raw/{paste_id}"
                async with session.get(raw_url) as raw_resp:
                    if raw_resp.status == 200:
                        raw_text = await raw_resp.text()
                        matches = GIFT_REGEX.findall(raw_text)
                        for code in matches:
                            print(f"{Fore.CYAN}[*] Found code in Pastebin: {code}")
                            await test_code(session, code)
                await asyncio.sleep(1) # Don't hammer Pastebin
    except Exception as e:
        print(f"{Fore.RED}[!] Pastebin scrape error: {e}")

async def main():
    print(f"{Fore.CYAN}[*] Starting Gift Scraper...")
    
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        while True:
            print(f"{Fore.CYAN}[*] Running scrape cycle...")
            await scrape_github(session)
            await scrape_pastebin(session)
            
            # Wait before next cycle to avoid rate limits
            wait_time = random.uniform(60, 120)
            print(f"{Fore.CYAN}[*] Cycle complete. Sleeping for {int(wait_time)}s...")
            await asyncio.sleep(wait_time)

if __name__ == "__main__":
    asyncio.run(main())
