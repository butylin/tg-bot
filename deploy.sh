#!/bin/bash

# Create necessary folders and files
mkdir ../logs
mkdir ../config
mkdir ../db
touch ../logs/bot.log
echo '{"admin" : [],"token": "your_token_here", "users": [], "chats": []}' > ../config/bot.conf

# Install non-standard python libraries
pip3 install python-telegram-bot
pip3 install apscheduler