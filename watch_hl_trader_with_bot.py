import os
import json
import asyncio
import datetime
import warnings
import re
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import websockets
import httpx
import discord
from discord.ext import commands

# Suppress SSL warnings when using verify=False (needed for some corporate networks)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

load_dotenv()

HL_WS = "wss://api.hyperliquid.xyz/ws"
HL_API = "https://api.hyperliquid.xyz/info"

ADDR = os.getenv("WATCH_ADDRESS", "").strip()
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "").strip()
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0")) if os.getenv("DISCORD_CHANNEL_ID") else None
TZ = ZoneInfo(os.getenv("LOCAL_TZ", "America/New_York"))
AGGREGATE_BY_TIME = os.getenv("AGGREGATE_BY_TIME", "true").lower() == "true"

# Optional filters
MIN_NOTIONAL_USDC = float(os.getenv("MIN_NOTIONAL_USDC", "0"))
COIN_ALLOWLIST = set(
    [c.strip().upper() for c in os.getenv("COIN_ALLOWLIST", "").split(",") if c.strip()]
)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

async def send_alert(text: str):
    """Send alert via Discord webhook"""
    if not DISCORD_WEBHOOK:
        print(text, flush=True)
        return
    async with httpx.AsyncClient(timeout=10, verify=False) as client:
        try:
            await client.post(DISCORD_WEBHOOK, json={"content": text})
            print(text, flush=True)
        except Exception as e:
            print(f"Error sending Discord alert: {e}", flush=True)

async def fetch_recent_trades(addr: str, limit: int = 20):
    """Fetch recent trades for the address"""
    try:
        async with httpx.AsyncClient(timeout=10, verify=False) as client:
            response = await client.post(
                HL_API,
                json={"type": "userFills", "user": addr}
            )
            if response.status_code == 200:
                data = response.json()
                fills = data[-limit:] if len(data) > limit else data
                return fills
    except Exception as e:
        print(f"Could not fetch recent trades: {e}")
    return []

def fmt_usdc(x):
    try:
        return f"{float(x):,.2f}"
    except Exception:
        return str(x)

def side_str(letter):
    return {"B": "BUY", "A": "SELL"}.get(letter, letter)

def format_trade(fill):
    """Format a single trade for display"""
    coin = fill.get("coin")
    px, sz, side, ts = fill.get("px"), fill.get("sz"), fill.get("side"), fill.get("time")
    t = datetime.datetime.fromtimestamp(ts / 1000, TZ).strftime("%Y-%m-%d %H:%M:%S %Z")
    
    notional = None
    try:
        notional = float(px) * float(sz)
    except Exception:
        pass
    
    text = f"{side_str(side)} {sz} {coin} @ {px} • {t}"
    if notional is not None:
        text += f" • ~${fmt_usdc(notional)}"
    return text

@bot.event
async def on_ready():
    print(f"✅ Discord bot logged in as {bot.user}")
    print(f"📺 Bot is in {len(bot.guilds)} server(s)")
    for guild in bot.guilds:
        print(f"   - {guild.name} (ID: {guild.id})")
    if DISCORD_CHANNEL_ID:
        print(f"🔒 Bot will only respond in channel ID: {DISCORD_CHANNEL_ID}")
    else:
        print(f"🌐 Bot will respond in all channels where it has permissions")

@bot.event
async def on_message(message):
    print(f"📨 Message received: '{message.content}' from {message.author} in #{message.channel.name} (ID: {message.channel.id})")
    
    if message.author == bot.user:
        print("   ↳ Ignoring (from bot itself)")
        return
    
    if DISCORD_CHANNEL_ID and message.channel.id != DISCORD_CHANNEL_ID:
        print(f"   ↳ Ignoring (not in configured channel {DISCORD_CHANNEL_ID})")
        return
    
    print(f"   ↳ Processing message...")
    
    # Check for "last N" command
    match = re.match(r'^last\s+(\d+)$', message.content.lower().strip())
    if match:
        n = int(match.group(1))
        n = min(n, 100)
        print(f"   ↳ Matched 'last {n}' command")
        
        await message.channel.send(f"🔍 Fetching last {n} trades for `{ADDR[:8]}...{ADDR[-6:]}`...")
        
        trades = await fetch_recent_trades(ADDR, limit=n)
        
        if not trades:
            await message.channel.send("❌ No recent trades found.")
            return
        
        # Split into chunks of 10 trades per message (Discord has message length limits)
        chunk_size = 10
        for i in range(0, len(trades), chunk_size):
            chunk = trades[i:i+chunk_size]
            lines = [f"📊 **Trades {i+1}-{i+len(chunk)} of {len(trades)}:**\n```"]
            for fill in chunk:
                lines.append(format_trade(fill))
            lines.append("```")
            await message.channel.send("\n".join(lines))
        
        await message.channel.send(f"✅ Displayed {len(trades)} trades")
        return
    
    if message.content.lower().strip() == "last":
        print(f"   ↳ Matched 'last' command")
        await message.channel.send(f"🔍 Fetching last 20 trades for `{ADDR[:8]}...{ADDR[-6:]}`...")
        
        trades = await fetch_recent_trades(ADDR, limit=20)
        
        if not trades:
            await message.channel.send("❌ No recent trades found.")
            return
        
        chunk_size = 10
        for i in range(0, len(trades), chunk_size):
            chunk = trades[i:i+chunk_size]
            lines = [f"📊 **Recent Trades {i+1}-{i+len(chunk)}:**\n```"]
            for fill in chunk:
                lines.append(format_trade(fill))
            lines.append("```")
            await message.channel.send("\n".join(lines))
        return
    
    print(f"   ↳ No command matched. Message was: '{message.content}'")

async def subscribe_userfills(ws, addr):
    sub = {
        "method": "subscribe",
        "subscription": {
            "type": "userFills",
            "user": addr,
            "aggregateByTime": AGGREGATE_BY_TIME,
        },
    }
    await ws.send(json.dumps(sub))

async def ping_loop(ws):
    while True:
        await asyncio.sleep(45)
        try:
            await ws.send(json.dumps({"method": "ping"}))
        except Exception:
            return

async def run_trade_monitor():
    """Monitor real-time trades via WebSocket"""
    backoff = 1
    
    while True:
        try:
            async with websockets.connect(HL_WS, ping_interval=None, close_timeout=5) as ws:
                await subscribe_userfills(ws, ADDR)
                asyncio.create_task(ping_loop(ws))
                await send_alert(f"🔔 Listening for trades by {ADDR} on Hyperliquid…")
                
                # Fetch and display last 20 trades on startup
                print("\n📊 Fetching last 20 trades...\n")
                recent_trades = await fetch_recent_trades(ADDR, limit=20)
                if recent_trades:
                    print(f"Found {len(recent_trades)} recent trades:\n")
                    for fill in recent_trades:
                        print(f"  {format_trade(fill)}")
                    print(f"\n✅ Connected! Now listening for new trades...\n")
                else:
                    print("No recent trades found (or address has no trading history)\n")

                async for raw in ws:
                    msg = json.loads(raw)
                    ch = msg.get("channel")
                    data = msg.get("data", {})
                    if ch == "userFills":
                        if data.get("isSnapshot"):
                            continue
                        fills = data.get("fills") or []
                        for f in fills:
                            coin = f.get("coin")
                            if COIN_ALLOWLIST and (coin or "").upper() not in COIN_ALLOWLIST:
                                continue
                            px, sz, side, ts = f.get("px"), f.get("sz"), f.get("side"), f.get("time")
                            
                            notional = None
                            try:
                                notional = float(px) * float(sz)
                            except Exception:
                                pass
                            if notional is not None and notional < MIN_NOTIONAL_USDC:
                                continue

                            text = f"💥 {format_trade(f)}"
                            await send_alert(text)
        except Exception as e:
            print(f"[reconnect] {e}")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30)
            continue

async def main():
    """Run both the Discord bot and trade monitor concurrently"""
    if not ADDR or not ADDR.startswith("0x") or len(ADDR) != 42:
        print("❌ Error: WATCH_ADDRESS must be a 42-char hex address")
        return
    
    if not DISCORD_BOT_TOKEN:
        print("❌ Error: DISCORD_BOT_TOKEN not set in .env")
        print("📝 Get a bot token from: https://discord.com/developers/applications")
        return
    
    async with asyncio.TaskGroup() as tg:
        tg.create_task(bot.start(DISCORD_BOT_TOKEN))
        tg.create_task(run_trade_monitor())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")

