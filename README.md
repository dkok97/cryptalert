# Hyperliquid Trader Alert System

Monitor trades from any Hyperliquid trader in real-time and receive Discord notifications.

Currently watching: **[0xc2a30212a8ddac9e123944d6e29faddce994e5f2](https://hyperdash.info/trader/0xc2a30212a8ddac9e123944d6e29faddce994e5f2)**

## Features

- 🔔 Real-time trade monitoring via WebSocket
- 💬 Discord notifications for every trade
- 🎯 Optional filters (minimum trade size, specific coins)
- ⏰ Automatic timezone conversion
- 🔄 Auto-reconnect on connection loss

## Setup

### 1. Create Virtual Environment

**Important:** Use Python 3.11 or 3.12 (Python 3.13 has SSL compatibility issues with Hyperliquid's API)

```bash
# Use Python 3.12 (recommended)
python3.12 -m venv .venv

# Or Python 3.11
# python3.11 -m venv .venv

source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Discord Webhook

1. Go to your Discord server
2. Click **Server Settings** → **Integrations** → **Webhooks**
3. Click **New Webhook**
4. Give it a name (e.g., "Crypto Alerts")
5. Select the channel where you want alerts
6. Click **Copy Webhook URL**

### 4. Update .env File

Edit the `.env` file and replace the placeholder Discord webhook URL:

```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_ACTUAL_WEBHOOK_URL
```

### 5. Run the Script

```bash
source .venv/bin/activate  # If not already activated
python3 watch_hl_trader.py
```

## Configuration Options

Edit `.env` to customize:

| Variable | Description | Example |
|----------|-------------|---------|
| `WATCH_ADDRESS` | Trader wallet address to monitor | `0xc2a30...` |
| `LOCAL_TZ` | Your timezone | `America/New_York` |
| `ALERT_TARGETS` | Where to send alerts | `console,discord` |
| `DISCORD_WEBHOOK_URL` | Your Discord webhook URL | `https://discord.com/api/webhooks/...` |
| `MIN_NOTIONAL_USDC` | Minimum trade size to alert (optional) | `500` |
| `COIN_ALLOWLIST` | Only alert on specific coins (optional) | `BTC,ETH,SOL` |

## Testing

### Quick Test

Once configured, run:

```bash
source .venv/bin/activate
python3 watch_hl_trader.py
```

You should see:
1. Initial connection message in console and Discord
2. Trade alerts whenever the monitored address executes trades

### Expected Output

```
🔔 Listening for trades by 0xc2a30212a8ddac9e123944d6e29faddce994e5f2 on Hyperliquid…
💥 BUY 0.5 BTC @ 67500.0 • 2025-10-26 14:30:45 EDT • ~$33,750.00
💥 SELL 1000 SOL @ 150.25 • 2025-10-26 14:31:12 EDT • ~$150,250.00
```

## Troubleshooting

### SSL Certificate Error (Python 3.13)
```
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
```
**Solution:** Use Python 3.11 or 3.12 instead:
```bash
rm -rf .venv
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### "WATCH_ADDRESS must be a 42-char hex address"
- Ensure the address starts with `0x` and is exactly 42 characters

### "Command not found: python"
- Use `python3` instead of `python`

### No Discord messages appearing
- Verify your webhook URL is correct
- Check the Discord channel permissions
- Look for error messages in the console

### Connection issues
- The script will automatically reconnect on network issues
- Check your internet connection
- Verify Hyperliquid API is accessible
- Run `python3 test_connection.py` to test connectivity

## Advanced Usage

### Filter by Trade Size

Only alert on trades over $1,000:

```bash
MIN_NOTIONAL_USDC=1000
```

### Filter by Coin

Only alert on Bitcoin and Ethereum trades:

```bash
COIN_ALLOWLIST=BTC,ETH
```

### Run as Background Service

```bash
nohup python3 watch_hl_trader.py > output.log 2>&1 &
```

## Architecture

- **WebSocket Connection**: Connects to Hyperliquid's real-time API
- **User Fills Subscription**: Monitors `userFills` channel for the target address
- **Alert System**: Sends formatted notifications via Discord webhook
- **Auto-Reconnect**: Exponential backoff retry logic on connection loss
- **Ping Loop**: Keeps connection alive with periodic pings

## License

MIT

