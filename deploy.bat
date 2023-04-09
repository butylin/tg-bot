@echo off

REM Create necessary folders and files
mkdir ../logs
mkdir ../config
mkdir ../db
type NUL > ../logs/bot.log
echo {"token": "your_token_here", "users": [], "chats": []} > ../config/bot.conf

REM Install non-standard python libraries
pip install python-telegram-bot
pip install apscheduler

REM Run the program
REM python program.py