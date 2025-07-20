# config.py

import os

# ✅ Required: Telegram API credentials
API_ID = int(os.getenv("API_ID", "YOUR_API_ID_HERE", "24472937"))  # replace with your API_ID
API_HASH = os.getenv("API_HASH", "YOUR_API_HASH_HERE", "da038362f56272bae92f22ece39e73e1")  # replace with your API_HASH
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE", "7564541101:AAGeeiFMZEh1irUh7d8sl68XsuAG29fzoKE")  # replace with your BOT_TOKEN

# 🔧 Optional: proxy settings (if needed)
# Use these if your network requires a proxy
# PROXY = {
#     "scheme": os.getenv("PROXY_SCHEME", "socks5"),
#     "hostname": os.getenv("PROXY_HOST", "127.0.0.1"),
#     "port": int(os.getenv("PROXY_PORT", 1080)),
# }
# Or simply:
# PROXY_URL = os.getenv("PROXY_URL", "socks5://127.0.0.1:1080")

# 📝 Optional bot settings
# Customize game parameters or messages here
START_MESSAGE = os.getenv("START_MESSAGE", "Hello! Let's play word games 🎮")
DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", 60))  # in seconds

# ✅ Validate that essential variables are set
if not API_ID or not API_HASH or not BOT_TOKEN:
    raise ValueError("API_ID, API_HASH and BOT_TOKEN must be set in environment or config.py")
