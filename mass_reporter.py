# language: Python, file: mass_reporter.py, target: Railway, Python 3.10+
# *Requires: pip install aiohttp aiohttp-socks colorama*

import asyncio
import aiohttp
import random
import os
from colorama import Fore, init

init(autoreset=True)

# --- CONFIGURATION ---
TARGET_USER_ID = "123456789012345678"     # Target User ID
TARGET_GUILD_ID = "987654321098765432"    # Target Server ID
TARGET_CHANNEL_ID = "111111111111111111"  # Channel where the message was sent
TARGET_MESSAGE_ID = "222222222222222222"  # The specific message ID that violated TOS

# Report Reasons: 0=Illegal, 1=Harassment, 2=Spam, 3=Self-harm, 4=NSFW, 5=Hate Speech
REPORT_REASON = 1 
REPORT_COUNT = 100

# Load from Railway Environment Variables
PROXIES = [p.strip() for p in os.environ.get("PROXIES", "").split(",") if p.strip()]
TOKENS = [t.strip() for t in os.environ.get("TOKENS", "").split(",") if t.strip()]

API_BASE = "https://discord.com/api/v9"

async def submit_report(session, token, proxy):
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "X-Discord-Locale": "en-US"
    }
    
    # Discord T&S requires message context. Without the message_id, the report is dropped.
    payload = {
        "guild_id": TARGET_GUILD_ID,
        "channel_id": TARGET_CHANNEL_ID,
        "message_id": TARGET_MESSAGE_ID,
        "user_id": TARGET_USER_ID,
        "reason": REPORT_REASON
    }

    try:
        async with session.post(f"{API_BASE}/report", headers=headers, json=payload, proxy=proxy, timeout=10) as resp:
            if resp.status in (204, 200):
                print(f"{Fore.GREEN}[+] Success via {proxy[:20]}...")
            elif resp.status == 429:
                retry = (await resp.json()).get("retry_after", 5)
                print(f"{Fore.YELLOW}[!] Rate limited. Sleeping {retry}s")
                await asyncio.sleep(retry)
            elif resp.status == 401:
                print(f"{Fore.RED}[-] Invalid token: {token[:15]}...")
            else:
                print(f"{Fore.RED}[-] Failed ({resp.status}): {await resp.text()}")
    except Exception as e:
        print(f"{Fore.RED}[!] Proxy/Network Error: {e}")

async def worker(session, proxy, semaphore):
    async with semaphore:
        token = random.choice(TOKENS)
        await submit_report(session, token, proxy)

async def main():
    if not TOKENS or not PROXIES:
        print(f"{Fore.RED}[!] Missing TOKENS or PROXIES in Railway variables.")
        return

    print(f"{Fore.CYAN}[*] Starting mass report against User: {TARGET_USER_ID}")
    print(f"{Fore.CYAN}[*] Proxies: {len(PROXIES)} | Tokens: {len(TOKENS)}")
    
    semaphore = asyncio.Semaphore(10) 
    
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False, limit=50)) as session:
        tasks = []
        for _ in range(REPORT_COUNT):
            proxy = random.choice(PROXIES)
            tasks.append(worker(session, proxy, semaphore))
            await asyncio.sleep(random.uniform(0.1, 0.5))

        await asyncio.gather(*tasks)
        print(f"{Fore.CYAN}[*] Report cycle complete.")

if __name__ == "__main__":
    asyncio.run(main())
