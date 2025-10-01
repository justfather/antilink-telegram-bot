#!/bin/bash

echo "🤖 Starting Antilink Telegram Bot..."
echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "▶️ Running bot..."
python bot.py
