import discord
from discord.ext import commands
import aiohttp
import os
import asyncio

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get("DISCORD_TOKEN") 
ALT_TOKENS = [t.strip() for t in os.environ.get("ALT_TOKENS", "").split(",") if t.strip()]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

async def join_server(session, alt_token, invite_code):
    url = f"https://discord.com/api/v9/invites/{invite_code}"
    headers = {
        "Authorization": alt_token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        # The empty json={} payload is required to bypass the 50109 invalid JSON error
        async with session.post(url, headers=headers, json={}) as resp:
            if resp.status == 200:
                return True, "Joined successfully"
            elif resp.status == 429:
                retry = (await resp.json()).get("retry_after", 5)
                return False, f"Rate limited. Wait {retry}s"
            else:
                return False, f"Failed: {resp.status} - {await resp.text()}"
    except Exception as e:
        return False, str(e)

@bot.event
async def on_ready():
    print(f"[*] Logged in as {bot.user}")
    print(f"[*] Loaded {len(ALT_TOKENS)} alt tokens.")

@bot.command(name="join")
async def join_cmd(ctx, invite_code: str):
    if not ALT_TOKENS:
        await ctx.send("```No ALT_TOKENS found in environment variables.```")
        return

    await ctx.send(f"```[*] Forcing alts to join via invite {invite_code}...```")
    
    success = 0
    failed = 0
    
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        for alt_token in ALT_TOKENS:
            joined, result = await join_server(session, alt_token, invite_code)
            
            if joined:
                success += 1
                print(f"[+] Success: {alt_token[:15]}...")
            else:
                failed += 1
                print(f"[-] Failed: {result}")
                
            # 2 second delay to prevent instant ban
            await asyncio.sleep(2.0)

    embed = discord.Embed(title="✅ Join Complete", color=discord.Color.green())
    embed.add_field(name="Invite Code", value=invite_code, inline=False)
    embed.add_field(name="Joined", value=str(success), inline=True)
    embed.add_field(name="Failed", value=str(failed), inline=True)
    
    await ctx.send(embed=embed)

if __name__ == "__main__":
    bot.run(BOT_TOKEN)
