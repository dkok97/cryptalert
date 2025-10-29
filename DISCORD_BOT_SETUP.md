# Discord Bot Setup Guide

This guide shows you how to set up a Discord bot that can respond to commands like "last 20" to show recent trades.

## 🤖 What You Get

With the bot version, you can:
- Get real-time trade alerts (like before)
- Type `last` in Discord to see last 20 trades
- Type `last 50` to see last 50 trades (up to 100)
- Query trade history anytime from Discord

## 📋 Setup Steps

### 1. Create a Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application**
3. Give it a name (e.g., "Crypto Alert Bot")
4. Click **Create**

### 2. Get Your Bot Token

1. In your application, click **Bot** in the left sidebar
2. Click **Reset Token** (or **View Token** if first time)
3. Click **Copy** to copy your bot token
4. **Save this token securely** - you'll need it in .env

### 3. Enable Message Content Intent

1. Still in the **Bot** section
2. Scroll down to **Privileged Gateway Intents**
3. Enable **MESSAGE CONTENT INTENT** (required to read messages)
4. Click **Save Changes**

### 4. Invite Bot to Your Server

1. Click **OAuth2** → **URL Generator** in left sidebar
2. Under **SCOPES**, check:
   - ✅ `bot`
3. Under **BOT PERMISSIONS**, check:
   - ✅ `Send Messages`
   - ✅ `Read Messages/View Channels`
   - ✅ `Read Message History`
4. Copy the generated URL at the bottom
5. Open URL in browser and select your server
6. Click **Authorize**

### 5. Get Your Channel ID

1. In Discord, go to **User Settings** (⚙️) → **Advanced**
2. Enable **Developer Mode**
3. Right-click on the channel where you want the bot to work
4. Click **Copy Channel ID**

### 6. Update Your .env File

Add these lines to your `.env`:

```bash
# Discord Bot (for receiving commands)
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_CHANNEL_ID=your_channel_id_here  # Optional: restrict to one channel

# Discord Webhook (for sending alerts - keep this)
DISCORD_WEBHOOK_URL=your_webhook_url_here
```

### 7. Install Dependencies

```bash
source .venv/bin/activate
pip install discord.py==2.4.0
```

Or reinstall all:

```bash
pip install -r requirements.txt
```

### 8. Run the Bot Version

```bash
python3 watch_hl_trader_with_bot.py
```

## 💬 Using the Bot

Once running, go to your Discord channel and type:

| Command | Description |
|---------|-------------|
| `last` | Show last 20 trades |
| `last 50` | Show last 50 trades |
| `last 10` | Show last 10 trades |

The bot will respond with formatted trade history!

## 🎯 How It Works

The script runs **two things simultaneously**:

1. **WebSocket Monitor** (like before)
   - Listens for real-time trades
   - Sends alerts via webhook when trades happen
   
2. **Discord Bot**
   - Listens for your messages in Discord
   - Responds to "last N" commands
   - Fetches historical trades on demand

## 🔧 Configuration Options

### Restrict Bot to One Channel

Set `DISCORD_CHANNEL_ID` in `.env` to only respond in that channel:

```bash
DISCORD_CHANNEL_ID=123456789012345678
```

If not set, bot responds in all channels where it has permissions.

### Keep Using Simple Webhook Version

If you don't want the bot features, just keep using:

```bash
python3 watch_hl_trader.py
```

The simple version only sends alerts, doesn't receive commands.

## 🆚 Which Version Should I Use?

| Feature | `watch_hl_trader.py` | `watch_hl_trader_with_bot.py` |
|---------|---------------------|-------------------------------|
| Real-time alerts | ✅ | ✅ |
| Simple setup | ✅ | ❌ (needs bot token) |
| Query trade history | ❌ | ✅ |
| Interactive commands | ❌ | ✅ |
| Webhook only | ✅ | Uses both |

**Recommendation:**
- Start with `watch_hl_trader.py` (simpler)
- Upgrade to `watch_hl_trader_with_bot.py` if you want to query history

## 🐛 Troubleshooting

### Bot doesn't respond to messages

1. ✅ Check **MESSAGE CONTENT INTENT** is enabled in Discord Developer Portal
2. ✅ Verify bot is in your server (you should see it online)
3. ✅ Check `DISCORD_BOT_TOKEN` in `.env` is correct
4. ✅ Make sure you're typing in the right channel (if `DISCORD_CHANNEL_ID` is set)

### "403 Forbidden" error

- Bot doesn't have permissions in that channel
- Go to channel settings → Permissions → Add the bot role → Grant "Send Messages"

### Bot is offline

- Check the script is running: `python3 watch_hl_trader_with_bot.py`
- Check for errors in console output
- Verify bot token is valid

### Both bots showing in server?

If you created a webhook AND a bot, you'll see both. That's fine:
- The webhook is for sending real-time alerts
- The bot is for receiving and responding to commands

## 🎉 Example Usage

```
You: last 10

Bot: 🔍 Fetching last 10 trades for `0xc2a302...e994e5f2`...

Bot: 📊 **Trades 1-10 of 10:**
```
BUY 2.5 BTC @ 67500.0 • 2025-10-27 14:23:15 EDT • ~$168,750.00
SELL 1000 SOL @ 150.25 • 2025-10-27 13:45:32 EDT • ~$150,250.00
BUY 0.1 ETH @ 3500.0 • 2025-10-27 12:10:05 EDT • ~$350.00
...
```

Bot: ✅ Displayed 10 trades
```

## 🚀 Deploy with Bot

When deploying to Fly.io/Render/Railway:

1. Add `DISCORD_BOT_TOKEN` to environment variables
2. Add `DISCORD_CHANNEL_ID` (optional)
3. Use `python3 watch_hl_trader_with_bot.py` as the start command
4. Ensure discord.py is in `requirements.txt`

That's it! 🎊

