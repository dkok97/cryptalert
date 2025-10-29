FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY watch_hl_trader_with_bot.py .

# Run the bot
ENV PYTHONUNBUFFERED=1
CMD ["python", "watch_hl_trader_with_bot.py"]

