"""
trading_execution.py
---------------------
This script connects:
- Pre-startup checks
- Strategy engine
- Upstox order placement

It executes real BUY/SELL orders on Upstox based on strategy signals.
Supports both INTRADAY (MIS) and DELIVERY (CNC) order types automatically.
"""

import json
import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from strategy_engine import StrategyEngine
from pre_startup_checks import run_pre_startup_checks
from database_manager import initialize_database, log_trade, update_daily_summary

# Safe token loader — returns empty dict in paper mode (no real credentials needed)
def _safe_load_token():
    try:
        from standalone_login_auth import load_token_from_file
        return load_token_from_file() or {}
    except Exception:
        return {}

def load_token_from_file():
    return _safe_load_token()

# upstox helpers — wrapped to avoid crash when no token present
try:
    from upstox import upstox_margin, upstox_positions
except Exception:
    def upstox_margin(c): return c
    def upstox_positions(c): return c


# =============================================
# 🔹 PRODUCT TYPE HELPER
# =============================================
# Intervals that are considered intraday (will use MIS product)
INTRADAY_INTERVALS = {"1minute", "3minute", "5minute", "10minute", "15minute", "30minute", "1hour"}

# Strategies that are inherently intraday (will use MIS even if interval is not set)
INTRADAY_STRATEGIES = {
    "vwap", "ema_crossover", "supertrend", "pivot_point",
    "candlestick", "stochastic", "adx_trend", "volume_price"
}


def get_product_type(interval: str = "day", strategy: str = "") -> str:
    """
    Determine Upstox product type based on interval and strategy.

    Returns:
        'I'  → MIS (Margin Intraday Square-off) — auto squares off at 3:20 PM
        'D'  → CNC (Cash and Carry / Delivery)  — holds overnight
    """
    interval_lower = (interval or "day").lower().strip()
    strategy_lower = (strategy or "").lower().strip()

    if interval_lower in INTRADAY_INTERVALS or strategy_lower in INTRADAY_STRATEGIES:
        return "I"   # Intraday / MIS
    return "D"       # Delivery / CNC


# =============================================
# 🔹 FETCH HISTORICAL DATA
# =============================================
from datetime import datetime, timedelta

def fetch_historical_data(symbol, interval="day", days=100):
    """
    Fetch historical OHLCV data from Upstox API.
    symbol format: 'NSE_EQ|INE467B01029'
    interval: '1minute', '30minute', 'day', etc.
    """
    token_info = load_token_from_file()
    access_token = token_info.get("access_token")
    
    # Calculate dates
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    # Correct URL format: /historical-candle/{instrumentKey}/{interval}/{to_date}/{from_date}
    url = f"https://api.upstox.com/v2/historical-candle/{symbol}/{interval}/{to_date}/{from_date}"
    headers = {"Authorization": f"Bearer {access_token}"}

    # Implement robust retry mechanism for noisy APIs
    max_retries = 3
    data = []
    
    for attempt in range(max_retries):
        try:
            # Added a 10-second timeout to prevent indefinite hangs
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json().get("data", {}).get("candles", [])
            
            # If data is empty but request succeeded, the market might be closed or symbol wrong
            if not data and attempt == max_retries - 1:
                print(f"⚠️ No data found for {symbol} after {max_retries} attempts.")
                return pd.DataFrame()
            
            # Successful fetch!
            if data:
                break
                
        except Exception as e:
            print(f"⚠️ [Attempt {attempt+1}/{max_retries}] Upstox API error for {symbol}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)  # Wait 2 seconds before retry
            else:
                print(f"❌ Permanent failure fetching data for {symbol}.")
                return pd.DataFrame()

    df = pd.DataFrame(data, columns=["time", "open", "high", "low", "close", "volume", "oi"])
    # Adjust columns if response has fewer
    if df.shape[1] == 7:
        df.columns = ["time", "open", "high", "low", "close", "volume", "oi"]
    else:
        df = df.iloc[:, :6]
        df.columns = ["time", "open", "high", "low", "close", "volume"]

    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values(by="time").reset_index(drop=True)
    return df


# =============================================
# 🔹 CAPITAL MANAGEMENT
# =============================================
def get_available_funds():
    """Fetch available funds depending on execution mode (Live Upstox or Paper)."""
    # 1. In paper mode: use the shared in-memory instance so deducted cash
    #    is reflected immediately (avoids stale balance from file re-reads).
    try:
        from trading_mode_manager import TradingModeManager
        mode_mgr = TradingModeManager()
        if mode_mgr.get_mode() == 'paper':
            try:
                import paper_trading_orders as _pto
                if _pto.paper_portfolio is not None:
                    return float(_pto.paper_portfolio.cash)
            except Exception:
                pass
            # Fallback: load from file if shared instance not set yet
            from paper_portfolio_manager import PaperPortfolioManager
            return float(PaperPortfolioManager().cash)
    except ImportError:
        pass

    # 2. Live upstream logic
    token_info = load_token_from_file()
    creds = {
        "api": {"headers": {"Authorization": f"Bearer {token_info.get('access_token')}", "accept": "application/json"}},
        "auth": {"client_id": "AUTO_BOT"}
    }
    
    try:
        creds = upstox_margin(creds)
        margin_data = creds.get("api", {}).get("margin", {})
        funds = 0
        if margin_data:
             funds = margin_data.get("equity", {}).get("available_margin", 0)
        
        print(f"💰 Available Funds (Live): ₹{funds}")
        return float(funds)
    except Exception as e:
        print(f"❌ Error fetching Live funds: {e}")
        return 0.0


def calculate_quantity(symbol, price, capital_per_trade=0.2):
    """Calculate quantity to buy based on available funds."""
    total_funds = get_available_funds()
    if total_funds <= 0:
        return 0

    trade_amount = total_funds * capital_per_trade
    # enforce maximum position size if configured (percentage of total funds)
    try:
        from paper_trading_config import PaperTradingConfig
        if hasattr(PaperTradingConfig, 'MAX_POSITION_SIZE_PCT'):
            cap = total_funds * (PaperTradingConfig.MAX_POSITION_SIZE_PCT / 100.0)
            trade_amount = min(trade_amount, cap)
    except ImportError:
        pass
    qty = int(trade_amount / price)
    return qty


# =============================================
# 🔹 P&L REPORTING (Local Only)
# =============================================
def get_pnL_summary():
    """Fetch current P&L and open positions (Live Upstox or Paper)."""
    # 1. Check if paper mode is active
    try:
        from trading_mode_manager import TradingModeManager
        mode_mgr = TradingModeManager()
        if mode_mgr.get_mode() == 'paper':
            from paper_portfolio_manager import PaperPortfolioManager
            paper_portfolio = PaperPortfolioManager()
            if paper_portfolio:
                stats = paper_portfolio.get_statistics()
                open_positions = len([p for p in paper_portfolio.positions.values() if p.get('qty', 0) != 0])
                total_pnl = float(stats.get('total_pnl', 0.0))
                return total_pnl, open_positions
            return 0.0, 0
    except ImportError:
        pass

    # 2. Live upstream logic
    token_info = load_token_from_file()
    creds = {
        "api": {"headers": {"Authorization": f"Bearer {token_info.get('access_token')}", "accept": "application/json"}},
        "auth": {"client_id": "AUTO_BOT"}
    }

    try:
        creds = upstox_positions(creds)
        positions = creds.get("api", {}).get("positions", [])
        
        if not positions:
            return 0.0, 0

        total_pnl = 0.0
        open_positions = 0
        
        for pos in positions:
            pnl = float(pos.get("pnl", 0))
            total_pnl += pnl
            if int(pos.get("quantity", 0)) != 0:
                open_positions += 1
                
        return total_pnl, open_positions
        
    except Exception as e:
        print(f"❌ Error fetching P&L: {e}")
        return 0.0, 0


# =============================================
# 🔹 PLACE ORDER FUNCTION
# =============================================
def place_order(symbol, side, qty, price, strategy="unknown", stock_name="", interval="day"):
    """
    Place an order via Upstox REST API and log to database.
    Automatically uses MIS (intraday) or CNC (delivery) based on interval/strategy.
    """
    if qty <= 0:
        print(f"⚠️ Quantity is 0. Skipping order for {symbol}.")
        return

    token_info = load_token_from_file()
    access_token = token_info.get("access_token")

    url = "https://api.upstox.com/v2/order/place"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    product = get_product_type(interval, strategy)
    product_label = "MIS (Intraday)" if product == "I" else "CNC (Delivery)"
    print(f"   📦 Product type: {product_label}")

    payload = {
        "instrument_token": symbol,
        "quantity": qty,
        "order_type": "MARKET",
        "transaction_type": side,
        "product": product,
        "duration": "DAY"
    }

    order_id = None
    status = "FAILED"
    
    try:
        r = requests.post(url, headers=headers, json=payload)
        response = r.json()
        
        if response.get("status") == "success":
            order_id = response.get('data', {}).get('order_id')
            status = "SUCCESS"
            msg = f"ORDER EXECUTED: {side} {qty} {symbol} @ ₹{price:.2f} | ID: {order_id}"
            print(f"✅ {msg}")
        else:
             err_msg = f"❌ Order Failed: {response}"
             print(err_msg)
    except Exception as e:
        print(f"❌ Order Exception: {e}")
    
    # Log trade to database
    try:
        trade_data = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'stock_name': stock_name if stock_name else symbol.split('|')[0],
            'strategy': strategy,
            'signal': side,
            'quantity': qty,
            'price': price,
            'order_id': order_id if order_id else '',
            'status': status,
            'ai_enabled': False,
            'confidence': None,
            'models_used': ''
        }
        log_trade(trade_data)
    except Exception as e:
        print(f"⚠️ Failed to log trade to database: {e}")


# =============================================
# 🔹 MAIN EXECUTION FUNCTION
# =============================================
def main():
    """
    Executes full trading workflow for multiple strategies.
    """
    print("\n🚀 Starting Trading Execution...\n")
    
    # Initialize database
    initialize_database()

    # Step 1: Check market status
    if not run_pre_startup_checks():
        print("❌ Pre-checks failed. Aborting startup.")
        return False
    
    # Record starting balance
    starting_balance = get_available_funds()

    # Define Portfolio watchlist
    portfolio = [
        {"symbol": "NSE_EQ|INE467B01029", "name": "TCS", "strategy": "ma_crossover", "interval": "day"},
        {"symbol": "NSE_EQ|INE002A01018", "name": "RELIANCE", "strategy": "rsi_reversion", "interval": "day"},
        {"symbol": "NSE_EQ|INE009A01021", "name": "INFY", "strategy": "breakout", "interval": "day"},
        {"symbol": "NSE_EQ|INE238A01034", "name": "AXISBANK", "strategy": "bollinger", "interval": "day"},
        {"symbol": "NSE_EQ|INE467B01029", "name": "TCS_Intraday", "strategy": "vwap", "interval": "30minute"}, 
    ]

    print(f"📋 Processing {len(portfolio)} strategies...")
    trades_taken = 0

    for item in portfolio:
        symbol = item["symbol"]
        strategy = item["strategy"]
        interval = item["interval"]
        name = item["name"]

        print(f"\n🔎 Analyzing {name} ({strategy})...")
        
        # Step 2: Fetch Data
        df = fetch_historical_data(symbol, interval=interval, days=100)
        if df.empty:
            continue

        # Step 3: Run Strategy
        engine = StrategyEngine(strategy_name=strategy)
        try:
            result_df = engine.run_strategy(df)
            latest_signal = result_df.iloc[-1]["signal"]
            current_price = result_df.iloc[-1]["close"]
            
            print(f"   📊 Signal: {latest_signal} | Price: {current_price}")

            # Step 4: Execute
            if latest_signal in ["BUY", "SELL"]:
                qty = calculate_quantity(symbol, current_price, capital_per_trade=0.1)
                if qty > 0:
                    place_order(symbol, latest_signal, qty, current_price,
                               strategy=strategy, stock_name=name, interval=interval)
                    trades_taken += 1
                else:
                    print("   ⚠️ Insufficient funds for trade.")
            else:
                print("   ⏳ No Action.")
                
        except Exception as e:
            print(f"   ❌ Strategy Error: {e}")

    # Step 5: Final Report and Database Logging
    print("\n📊 Generating P&L Report...")
    pnl, open_pos = get_pnL_summary()
    ending_balance = get_available_funds()
    
    summary_msg = (
        f"💰 Daily Summary\n"
        f"------------------\n"
        f"💵 Balance: ₹{ending_balance:.2f}\n"
        f"📉 Open Pos: {open_pos}\n"
        f"📊 Day's P&L: {'+' if pnl >=0 else ''}₹{pnl:.2f}\n"
        f"✅ Trades: {trades_taken}"
    )
    print(summary_msg)
    
    # Log daily summary to database
    try:
        from datetime import date
        summary_data = {
            'date': date.today(),
            'starting_balance': starting_balance,
            'ending_balance': ending_balance,
            'total_pnl': pnl,
            'realized_pnl': 0,  # Would need additional tracking
            'unrealized_pnl': pnl,
            'total_trades': trades_taken,
            'buy_trades': 0,  # Would need to track separately
            'sell_trades': 0,  # Would need to track separately
            'total_capital_used': 0,  # Would need to calculate from trades
            'open_positions': open_pos,
            'ai_trades': 0,
            'rule_based_trades': trades_taken
        }
        update_daily_summary(summary_data)
    except Exception as e:
        print(f"⚠️ Failed to log daily summary: {e}")

    print("\n✅ All strategies executed.\n")
    return True


# =============================================
# 🔹 RUN DIRECTLY
# =============================================
if __name__ == "__main__":
    main()
