import os
import json
import asyncio
import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import websockets
import httpx

load_dotenv()  # Load environment variables from .env file

HL_WS = "wss://api.hyperliquid.xyz/ws"

ADDR = os.getenv("WATCH_ADDRESS", "").strip()  # e.g. 0xc2a30212a8ddac9e123944d6e29faddce994e5f2
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
TZ = ZoneInfo(os.getenv("LOCAL_TZ", "America/New_York"))
AGGREGATE_BY_TIME = os.getenv("AGGREGATE_BY_TIME", "true").lower() == "true"

# Optional filters
MIN_NOTIONAL_USDC = float(os.getenv("MIN_NOTIONAL_USDC", "0"))  # set >0 to suppress tiny fills
COIN_ALLOWLIST = set(
    [c.strip().upper() for c in os.getenv("COIN_ALLOWLIST", "").split(",") if c.strip()]
)

async def send_alert(text: str):
    if not DISCORD_WEBHOOK:
        print("Discord webhook URL not set. Skipping alert.", flush=True)
        return
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(DISCORD_WEBHOOK, json={"content": text})
        except Exception as e:
            print(f"Error sending Discord alert: {e}", flush=True)

def fmt_usdc(x):
    try:
        return f"{float(x):,.2f}"
    except Exception:
        return str(x)

def side_str(letter):
    return {"B": "BUY", "A": "SELL"}.get(letter, letter)

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
        await asyncio.sleep(45)  # < 60s idle limit
        try:
            await ws.send(json.dumps({"method": "ping"}))
        except Exception:
            return

async def run():
    assert ADDR.startswith("0x") and len(ADDR) == 42, "WATCH_ADDRESS must be a 42-char hex address"
    backoff = 1

    while True:
        try:
            async with websockets.connect(HL_WS, ping_interval=None, close_timeout=5) as ws:
                await subscribe_userfills(ws, ADDR)
                asyncio.create_task(ping_loop(ws))
                await send_alert(f"🔔 Listening for trades by {ADDR} on Hyperliquid…")

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
                            t = datetime.datetime.fromtimestamp(ts / 1000, TZ).strftime("%Y-%m-%d %H:%M:%S %Z")

                            notional = None
                            try:
                                notional = float(px) * float(sz)
                            except Exception:
                                pass
                            if notional is not None and notional < MIN_NOTIONAL_USDC:
                                continue

                            text = f"💥 {side_str(side)} {sz} {coin} @ {px} • {t}"
                            if notional is not None:
                                text += f" • ~${fmt_usdc(notional)}"
                            await send_alert(text)
        except Exception as e:
            print(f"[reconnect] {e}")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30)
            continue

if __name__ == "__main__":
    asyncio.run(run())
