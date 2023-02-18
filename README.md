# CryptoTradingBot
Smart CryptoTradingBot on Binance API (spot &amp; futures long/short pos) with Telegram Notification(and command to manage it)

## bot.py
the main python script to start

# Instructions

1. Get free historical crypto data API key there https://www.alphavantage.co/support/#api-key

2. Get your free binance API key on binance.com (KEY & SECRET KEY) and paste them in cred.py

3. Paste the obtained keys from binance into cred.py file (key & secret accondingly) & api keys from alphavantage inside of bot.py

4. futures_signature.py is needed to get access to binance futures by your binance API keys

5. Get your telegram api key on telegram bot father and paste in into bot.py

P.S. (don't allow your binance API key use Widthrawal & Transfer permissions)


## Run on VPS or any cloud provider

1. Recommend to use Ubuntu 20.04 LTS image or docker with lighweight version (python:3-alpine) and pyenv within.
2.  Install required libs & run it
```pip install python-binance
pip install binance
python bot.py```

3. You can use crontab to reshedule launch of the cryptobot (bot.py) whenever you want.
