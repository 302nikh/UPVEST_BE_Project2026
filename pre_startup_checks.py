"""
Pre-startup checks before running trading algorithms.
Ensures trading session is valid, network is available, and credentials are present.
"""

import os
import json
import socket
from datetime import datetime, time, date

# Import Telegram notifications (optional)
try:
    from telegram_notifier import send_market_closed, send_out_of_time
    TELEGRAM_ENABLED = True
except:
    TELEGRAM_ENABLED = False

# Detect paper trading mode — skip credential checks if virtual
try:
    from paper_trading_config import PaperTradingConfig
    _IS_PAPER_MODE = PaperTradingConfig.PAPER_TRADING_MODE
except Exception:
    _IS_PAPER_MODE = False

# ----------------------------------------------
# CONFIGURABLE PARAMETERS
# ----------------------------------------------
MARKET_START = time(9, 15)
MARKET_END = time(15, 30)
TOKEN_FILE = "access_token.json"
CREDS_FILE = "creds.json"

# Common Indian market holidays (you can expand/update dynamically)
MARKET_HOLIDAYS = {
    "2025-01-26",  # Republic Day
    "2025-03-14",  # Holi
    "2025-04-18",  # Good Friday
    "2025-05-01",  # Maharashtra Day
    "2025-08-15",  # Independence Day
    "2025-10-02",  # Gandhi Jayanti
    "2025-10-24",  # Diwali
    "2025-12-25",  # Christmas
}

# ----------------------------------------------
# CHECK FUNCTIONS
# ----------------------------------------------

def check_internet_connection(host="8.8.8.8", port=53, timeout=3):
    """Verify active internet connection."""
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False


def check_market_hours():
    """Ensure current time is within trading hours."""
    now = datetime.now().time()
    if MARKET_START <= now <= MARKET_END:
        return True
    return False


def check_weekend():
    """Return True if it's a weekend (Saturday or Sunday)."""
    today = datetime.today().weekday()
    return today in [5, 6]


def check_market_holiday():
    """Check if today is an NSE/BSE market holiday."""
    today_str = date.today().strftime("%Y-%m-%d")
    return today_str in MARKET_HOLIDAYS


def check_files_exist():
    """Ensure required files (credentials and token) are present."""
    missing = []
    if not os.path.exists(CREDS_FILE):
        missing.append(CREDS_FILE)
    if not os.path.exists(TOKEN_FILE):
        missing.append(TOKEN_FILE)
    return missing


def check_token_validity():
    """Basic validation to ensure access token file isn't expired."""
    if not os.path.exists(TOKEN_FILE):
        return False, "Token file missing."

    try:
        with open(TOKEN_FILE, "r") as f:
            token_data = json.load(f)
        
        # If the backend generated the token without a timestamp, assume it's valid for now
        if "generated_at" not in token_data:
            return True, "Token valid (no generated_at timestamp found)."

        gen_time = datetime.strptime(token_data.get("generated_at"), "%Y-%m-%d %H:%M:%S")
        age_hours = (datetime.now() - gen_time).total_seconds() / 3600
        # Upstox tokens usually last 24 hours
        if age_hours > 23:
            return False, f"Token expired ({age_hours:.1f} hours old)."
        return True, "Token valid."
    except Exception as e:
        return False, f"Error reading token: {e}"


# ----------------------------------------------
# MAIN CHECK EXECUTION
# ----------------------------------------------

def run_pre_startup_checks():
    print("\n🔍 Running Pre-Startup Checks...\n" + "="*40)

    # 1️⃣ Internet
    if not check_internet_connection():
        print("❌ Internet connection failed.")
        return False

    # 2️⃣ Weekend
    if check_weekend():
        print("❌ Markets closed - it's a weekend.")
        return False

    # 3️⃣ Holiday
    if check_market_holiday():
        print("❌ Market holiday today.")
        return False

    # 4️⃣ Trading hours
    if not check_market_hours():
        current_time = datetime.now().time().strftime('%H:%M')
        print(f"⏳ Market Closed. Current time {current_time} is outside trading hours (09:15 - 15:30).")
        # Send out of time notification
        if TELEGRAM_ENABLED:
            send_out_of_time(cutoff_time="15:30")
        return False

    # 5️⃣ Required files (skipped in paper mode — no real credentials needed)
    if _IS_PAPER_MODE:
        print("📝 PAPER MODE: Skipping credential file checks (virtual money only).")
    else:
        missing = check_files_exist()
        if missing:
            print(f"❌ Missing files: {', '.join(missing)}")
            return False

        # 6️⃣ Token validity (only in live mode)
        valid, msg = check_token_validity()
        if not valid:
            print(f"❌ Token issue: {msg}")
            return False
        else:
            print(f"✅ Token check: {msg}")

    print("\n✅ All pre-startup checks passed! Safe to start trading agent.\n" + "="*40)
    return True


if __name__ == "__main__":
    ok = run_pre_startup_checks()
    if not ok:
        print("\n⚠️  Pre-checks failed. Aborting startup.\n")
    else:
        print("\n🚀 Proceeding to trading script...\n")
