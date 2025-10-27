FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY watch_hl_trader.py .

# Run the bot
CMD ["python", "watch_hl_trader.py"]

