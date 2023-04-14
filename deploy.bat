@echo off

REM Create necessary folders and files
mkdir ../logs
mkdir ../config
mkdir ../db
type NUL > ../logs/bot.log
echo {"admin" : [],"token": "your_token_here", "users": [], "chats": []} > ../config/bot.conf

REM Install non-standard python libraries
pip3 install python-telegram-bot
pip3 install apscheduler