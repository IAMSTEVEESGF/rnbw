import discord
from discord.ext import commands
import aiohttp
import os
import asyncio
import random

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get("DISCORD_TOKEN") 
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REDIRECT_URI = "https://localhost" 

# Load alt tokens from Railway env (comma separated)
ALT_TOKENS = [t.strip() for t in os.environ.get("ALT_TOKENS", "").split(",") if t.strip()]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

async def force_join_bypass(session, alt_token, guild_id):
    headers = {
        "Authorization": alt_token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # 1. Authorize the OAuth2 app
    auth_url = f"https://discord.com/api/v9/oauth2/authorize?client_id={CLIENT_ID}&response_type=code&scope=guilds.join%20identify&redirect_uri={REDIRECT_URI}"
    
    try:
        async with session.post(auth_url, headers=headers, json={"authorize": True, "permissions": "0"}) as resp:
            if resp.status == 200:
                data = await resp.json()
                location = data.get("location", "")
                if "code=" not in location:
                    return False, "No code in redirect"
                code = location.split("code=")[1].split("&")[0]
            elif resp.status == 429:
                return False, "Rate limited on auth"
            else:
                return False, f"Auth failed: {resp.status}"
                
        # 2. Exchange the code for an access_token
        token_url = "https://discord.com/api/v10/oauth2/token"
        payload = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI
        }
        
        async with session.post(token_url, data=payload, headers={"Content-Type": "application/x-www-form-urlencoded"}) as resp:
            if resp.status != 200:
                return False, f"Token exchange failed: {resp.status}"
            token_data = await resp.json()
            access_token = token_data["access_token"]
            user_id = token_data["user"]["id"]

        # 3. Force the join using the Bot Token
        join_url = f"https://discord.com/api/v10/guilds/{guild_id}/members/{user_id}"
        bot_headers = {
            "Authorization": f"Bot {BOT_TOKEN}",
            "Content-Type": "application/json"
        }
        
        async with session.put(join_url, headers=bot_headers, json={"access_token": access_token}) as resp:
            if resp.status in (201, 204):
                return True, user_id
            elif resp.status == 429:
                return False, "Rate limited on join"
            else:
                error = await resp.text()
                return False, f"Join failed: {resp.status} - {error}"
                
    except Exception as e:
        return False, str(e)

@bot.event
async def on_ready():
    print(f"[*] Logged in as {bot.user}")
    print(f"[*] Loaded {len(ALT_TOKENS)} alt tokens.")
    print("[*] Command: !join <server_id>")

@bot.command(name="join")
async def join_cmd(ctx, guild_id: str):
    """Forces all loaded alt accounts to join the specified server."""
    if not ALT_TOKENS:
        await ctx.send("```No ALT_TOKENS found in environment variables.```")
        return

    await ctx.send(f"```[*] Starting bypass-join for {len(ALT_TOKENS)} alts into {guild_id}...```")
    
    success = 0
    failed = 0
    
    connector = aiohttp.TCPConnector(ssl=False, limit=10)
    async with aiohttp.ClientSession(connector=connector) as session:
        for alt_token in ALT_TOKENS:
            joined, result = await force_join_bypass(session, alt_token, guild_id)
            
            if joined:
                success += 1
                print(f"[+] Joined: {result}")
            else:
                failed += 1
                print(f"[-] Failed ({alt_token[:10]}...): {result}")
                
            # Delay to avoid triggering Cloudflare
            await asyncio.sleep(random.uniform(1.0, 2.0))

    # Send the "Farm Complete" embed
    embed = discord.Embed(title="✅ Farm Complete", color=discord.Color.green())
    embed.add_field(name="Server", value=guild_id, inline=False)
    embed.add_field(name="Limit", value=str(len(ALT_TOKENS)), inline=False)
    
    results_text = f"✅ Joined: **{success}**\n"
    results_text += f"❌ Failed: **{failed}**\n"
    results_text += f"📊 Total: **{len(ALT_TOKENS)}**"
    
    embed.add_field(name="Results", value=results_text, inline=False)
    embed.set_footer(text=f"Done · {len(ALT_TOKENS)} members scanned")
    
    await ctx.send(embed=embed)

if __name__ == "__main__":
    bot.run(BOT_TOKEN)
