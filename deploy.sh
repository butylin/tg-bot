#!/bin/bash

# Create necessary folders and files
mkdir ../logs
mkdir ../config
mkdir ../db
touch ../logs/bot.log
echo '{"token": "your_token_here", "users": [], "chats": []}' > ../config/bot.conf

# Install non-standard python libraries
pip install python-telegram-bot
pip install apscheduler

# Run the program
python program.py