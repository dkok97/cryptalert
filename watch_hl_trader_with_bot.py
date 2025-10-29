import os
import json
import asyncio
import datetime
import warnings
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from typing import Dict
import websockets
import httpx
import discord
from discord.ext import commands

warnings.filterwarnings('ignore', message='Unverified HTTPS request')

load_dotenv()

HL_WS = "wss://api.hyperliquid.xyz/ws"
HL_API = "https://api.hyperliquid.xyz/info"

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "").strip()
TZ = ZoneInfo(os.getenv("LOCAL_TZ", "America/New_York"))
AGGREGATE_BY_TIME = os.getenv("AGGREGATE_BY_TIME", "true").lower() == "true"

# Optional filters
MIN_NOTIONAL_USDC = float(os.getenv("MIN_NOTIONAL_USDC", "0"))
COIN_ALLOWLIST = set(
    [c.strip().upper() for c in os.getenv("COIN_ALLOWLIST", "").split(",") if c.strip()]
)

# Store mapping of channel_id -> address
tracked_addresses: Dict[int, str] = {}

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

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

def extract_last_5_chars(address: str) -> str:
    """Extract last 5 chars from address (excluding 0x)"""
    return address[-5:].lower()

def validate_address(address: str) -> bool:
    """Validate Ethereum address format"""
    return address.startswith("0x") and len(address) == 42

@bot.event
async def on_ready():
    print(f"✅ Discord bot logged in as {bot.user}")
    print(f"📺 Bot is in {len(bot.guilds)} server(s)")
    for guild in bot.guilds:
        print(f"   - {guild.name} (ID: {guild.id})")
    print(f"\n💡 Usage:")
    print(f"   1. Create channel: alert-{extract_last_5_chars('0xc2a30212a8ddac9e123944d6e29faddce994e5f2')}")
    print(f"   2. In that channel: track 0xc2a30212a8ddac9e123944d6e29faddce994e5f2")
    print(f"   3. Get real-time alerts in that channel!\n")

@bot.event
async def on_message(message):
    print(f"📨 Message: '{message.content}' from {message.author} in #{message.channel.name} (ID: {message.channel.id})")
    
    if message.author == bot.user:
        print("   ↳ Ignoring (from bot)")
        return
    
    content = message.content.strip()
    
    # Command: track <address>
    track_match = re.match(r'^track\s+(0x[a-fA-F0-9]{40})$', content, re.IGNORECASE)
    if track_match:
        address = track_match.group(1).lower()
        
        if not validate_address(address):
            await message.channel.send(f"❌ Invalid address format: {address}")
            return
        
        # Extract last 5 chars
        last_5 = extract_last_5_chars(address)
        expected_channel = f"alert-{last_5}"
        
        # Check if channel name matches
        if not message.channel.name.startswith("alert-"):
            await message.channel.send(
                f"⚠️ This command should be used in a channel starting with `alert-`\n"
                f"💡 Create a channel called `{expected_channel}` for this address"
            )
            return
        
        if message.channel.name != expected_channel:
            await message.channel.send(
                f"⚠️ Channel name mismatch!\n"
                f"Expected: `{expected_channel}` (based on address ending)\n"
                f"Current: `{message.channel.name}`\n\n"
                f"💡 Either:\n"
                f"- Rename this channel to `{expected_channel}`, or\n"
                f"- Use the address ending with `...{message.channel.name[6:]}`"
            )
            return
        
        # Add to tracked addresses
        tracked_addresses[message.channel.id] = address
        print(f"   ↳ Now tracking {address} in #{message.channel.name}")
        
        await message.channel.send(
            f"✅ **Now tracking** `{address}`\n"
            f"📊 Fetching recent trades..."
        )
        
        # Show last 10 trades
        trades = await fetch_recent_trades(address, limit=10)
        if trades:
            lines = [f"📈 **Last {len(trades)} trades:**\n```"]
            for fill in trades:
                lines.append(format_trade(fill))
            lines.append("```")
            await message.channel.send("\n".join(lines))
        else:
            await message.channel.send("No recent trades found (new address or no history)")
        
        await message.channel.send(f"🔔 You'll now get real-time alerts here!")
        return
    
    # Command: untrack
    if content.lower() == "untrack":
        if message.channel.id in tracked_addresses:
            address = tracked_addresses[message.channel.id]
            del tracked_addresses[message.channel.id]
            await message.channel.send(f"✅ Stopped tracking `{address}`")
            print(f"   ↳ Untracked {address} from #{message.channel.name}")
        else:
            await message.channel.send("❌ No address is being tracked in this channel")
        return
    
    # Command: status
    if content.lower() == "status":
        if message.channel.id in tracked_addresses:
            address = tracked_addresses[message.channel.id]
            await message.channel.send(
                f"✅ **Currently tracking:** `{address}`\n"
                f"📺 Channel: #{message.channel.name}"
            )
        else:
            await message.channel.send(
                f"❌ No address tracked in this channel\n"
                f"💡 Use: `track 0x...` to start tracking"
            )
        return
    
    # Command: last [N]
    match = re.match(r'^last\s+(\d+)$', content.lower())
    if match or content.lower() == "last":
        n = int(match.group(1)) if match else 20
        n = min(n, 100)
        
        if message.channel.id not in tracked_addresses:
            await message.channel.send("❌ No address tracked. Use `track 0x...` first")
            return
        
        address = tracked_addresses[message.channel.id]
        print(f"   ↳ Fetching last {n} for {address}")
        
        await message.channel.send(f"🔍 Fetching last {n} trades...")
        
        trades = await fetch_recent_trades(address, limit=n)
        if not trades:
            await message.channel.send("❌ No trades found")
            return
        
        # Send in chunks of 10
        chunk_size = 10
        for i in range(0, len(trades), chunk_size):
            chunk = trades[i:i+chunk_size]
            lines = [f"📊 **Trades {i+1}-{i+len(chunk)} of {len(trades)}:**\n```"]
            for fill in chunk:
                lines.append(format_trade(fill))
            lines.append("```")
            await message.channel.send("\n".join(lines))
        return

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
    print(f"   📡 Subscribed to {addr}")

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
    subscribed_addresses = set()
    
    while True:
        try:
            async with websockets.connect(HL_WS, ping_interval=None, close_timeout=5) as ws:
                asyncio.create_task(ping_loop(ws))
                print(f"🔌 Connected to Hyperliquid WebSocket")
                
                # Subscribe to all tracked addresses
                for channel_id, address in tracked_addresses.items():
                    if address not in subscribed_addresses:
                        await subscribe_userfills(ws, address)
                        subscribed_addresses.add(address)
                
                print(f"✅ Monitoring {len(subscribed_addresses)} addresses")
                
                async for raw in ws:
                    msg = json.loads(raw)
                    ch = msg.get("channel")
                    data = msg.get("data", {})
                    
                    if ch == "userFills":
                        if data.get("isSnapshot"):
                            continue
                        
                        # Find which channel(s) should get this alert
                        user_address = data.get("user", "").lower()
                        
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

                            text = f"💥 **NEW TRADE**\n```{format_trade(f)}```"
                            
                            # Send to all channels tracking this address
                            for channel_id, address in tracked_addresses.items():
                                if address.lower() == user_address:
                                    try:
                                        channel = bot.get_channel(channel_id)
                                        if channel:
                                            await channel.send(text)
                                            print(f"   📤 Sent alert to #{channel.name}")
                                    except Exception as e:
                                        print(f"   ❌ Failed to send to channel {channel_id}: {e}")
                    
                    # Check if we need to subscribe to new addresses
                    current_addresses = set(tracked_addresses.values())
                    new_addresses = current_addresses - subscribed_addresses
                    for address in new_addresses:
                        await subscribe_userfills(ws, address)
                        subscribed_addresses.add(address)
                        
        except Exception as e:
            print(f"[reconnect] {e}")
            subscribed_addresses.clear()
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30)
            continue

async def main():
    """Run both the Discord bot and trade monitor concurrently"""
    if not DISCORD_BOT_TOKEN:
        print("❌ Error: DISCORD_BOT_TOKEN not set in .env")
        print("📝 Get a bot token from: https://discord.com/developers/applications")
        return
    
    # Run both concurrently
    async with asyncio.TaskGroup() as tg:
        tg.create_task(bot.start(DISCORD_BOT_TOKEN))
        tg.create_task(run_trade_monitor())

if __name__ == "__main__":
    # Minimal HTTP health server for Cloud Run
    class _HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, format, *args):
            return

    def start_health_server():
        port = int(os.environ.get("PORT", "8080"))
        server = HTTPServer(("0.0.0.0", port), _HealthHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        print(f"🩺 Health server listening on :{port}")
        return server

    try:
        start_health_server()
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
