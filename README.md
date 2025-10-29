# Hyperliquid Trading Alert Bot

Dynamic Discord bot that monitors trades from multiple Hyperliquid traders in real-time across different channels.

## ✨ Features

- 🔔 **Real-time Trade Monitoring** - Instant alerts when traders execute
- 🎯 **Multi-Trader Support** - Track unlimited addresses simultaneously
- 📺 **Channel-Based Organization** - Each trader gets their own Discord channel
- 💬 **Interactive Commands** - Query trade history, check status, and more
- 🔄 **Auto-Reconnect** - Resilient connection with exponential backoff
- ⏰ **Timezone Support** - Display trades in your local time
- 🎨 **Smart Filtering** - Filter by trade size or specific coins

## 🚀 Quick Start

### 1. Create a Channel
For any address, say `0x17d9a536a5b883cfeb414b97268ee1c2d001ad95`, create:
```
Channel name: #alert-1ad95
```
(Use last 5 characters of the address)

### 2. Track the Address
In that channel, type:
```
track 0x17d9a536a5b883cfeb414b97268ee1c2d001ad95
```

### 3. Get Alerts!
```
✅ Now tracking 0x17d9a536a5b883cfeb414b97268ee1c2d001ad95
📈 Last 10 trades:
[shows history]
🔔 You'll now get real-time alerts here!

💥 NEW TRADE
BUY 0.5 BTC @ 67500.0 • 2025-10-29 14:30:45 EDT • ~$33,750.00
```

## 📋 Setup Guide

### Prerequisites

- Python 3.11 or 3.12 (Python 3.13 has SSL issues with Hyperliquid)
- Discord account with server admin access
- Discord bot token

### Step 1: Create Virtual Environment

```bash
# Use Python 3.12 (recommended)
python3.12 -m venv .venv

# Or Python 3.11
# python3.11 -m venv .venv

source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application** → Give it a name
3. Go to **Bot** section → Click **Reset Token** → Copy the token
4. Enable **MESSAGE CONTENT INTENT** under Privileged Gateway Intents
5. Go to **OAuth2** → **URL Generator**:
   - Scopes: `bot`
   - Bot Permissions: `Send Messages`, `Read Messages/View Channels`, `Read Message History`
6. Copy generated URL, open in browser, and add bot to your server

### Step 4: Configure Environment

Edit `.env`:

```bash
# Required
DISCORD_BOT_TOKEN=your_bot_token_here

# Optional
LOCAL_TZ=America/New_York
AGGREGATE_BY_TIME=true

# Filters (apply to ALL tracked addresses)
MIN_NOTIONAL_USDC=500          # Only alert trades > $500
COIN_ALLOWLIST=BTC,ETH,SOL     # Only alert these coins
```

### Step 5: Run the Bot

```bash
source .venv/bin/activate
python3 watch_hl_trader_with_bot.py
```

You should see:
```
✅ Discord bot logged in as YourBot#1234
📺 Bot is in 1 server(s)
🔌 Connected to Hyperliquid WebSocket
✅ Monitoring 0 addresses (initially)
```

## 🎯 How to Use

### Basic Workflow

1. **Find a trader** you want to monitor (e.g., from [HyperDash](https://hyperdash.info/))
2. **Create Discord channel**: `alert-XXXXX` (last 5 chars of address)
3. **Track in channel**: `track 0xFullAddressHere`
4. **Receive alerts** automatically in that channel!

## 🤖 Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `track 0x...` | Start tracking an address in this channel | `track 0xc2b431...1ade4` |
| `untrack` | Stop tracking in this channel | `untrack` |
| `status` | Show what's being tracked here | `status` |
| `last` | Show last 20 trades | `last` |
| `last N` | Show last N trades (max 100) | `last 50` |

## 🌟 Advanced Features

### Track Multiple Traders

Create separate channels for different traders:

```
#alert-4e5f2  → tracks 0x...4e5f2 (Whale Watcher)
#alert-9a3b7  → tracks 0x...9a3b7 (Day Trader)
#alert-f2c1d  → tracks 0x...f2c1d (Institutional)
```

Each channel gets alerts only for its specific trader!

## Debugging

### SSL Certificate Error (Python 3.13)

**Error:**
```
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
```

**Solution:** Use Python 3.11 or 3.12:
```bash
rm -rf .venv
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Bot Goes Offline Randomly

**Solutions:**
- Check your internet connection
- Look at console output for error messages
- The bot auto-reconnects, but if it crashes, restart it
- Consider running as a service (see below)

### Dependencies

- `websockets` - WebSocket client for Hyperliquid
- `httpx` - Async HTTP client for API calls
- `discord.py` - Discord bot framework
- `python-dotenv` - Environment variable management

## 📜 License

MIT

## 🤝 Contributing

Issues and pull requests welcome!

## 💬 Support

- Check console output for detailed error messages
- Ensure all environment variables are set correctly
- Verify bot permissions in Discord
- Test with a single address before scaling up

---

**Ready to track trades?** Follow the Quick Start section above! 🚀
