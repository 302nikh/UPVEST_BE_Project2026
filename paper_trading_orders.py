"""
Paper Trading Order Execution Functions
----------------------------------------
These functions should replace the place_order_ai function in trading_execution_ai.py
"""

# core imports needed by multiple functions
import time
import requests
from datetime import datetime

# helpers from other modules (import inline where possible to avoid circular)
# load_token_from_file is imported lazily inside place_live_order() so that
# this module can be safely loaded in paper mode without requiring credentials.
from database_manager import log_trade

# paper trading configuration and portfolio
try:
    from paper_trading_config import PaperTradingConfig
    from paper_portfolio_manager import PaperPortfolioManager
    PAPER_TRADING_AVAILABLE = True
except Exception as e:
    PAPER_TRADING_AVAILABLE = False
    print(f"⚠️ Paper trading not available: {e}")

# global portfolio instance (may be set externally by run_live_paper_bot)
paper_portfolio = None

def place_order_ai(symbol, side, qty, price, strategy="unknown", stock_name="",
                   ai_enabled=False, confidence=None, models_used="", interval="day"):
    """
    Place an order - either PAPER or LIVE based on configuration.
    Routes to appropriate execution method based on PAPER_TRADING_MODE.
    interval is passed through for correct MIS/CNC product selection.
    """
    if qty <= 0:
        print(f"⚠️ Quantity is 0. Skipping order for {symbol}.")
        return False
    
    # Check if paper trading mode is enabled
    if PAPER_TRADING_AVAILABLE and PaperTradingConfig.PAPER_TRADING_MODE:
        return place_paper_order(symbol, side, qty, price, strategy, stock_name,
                                ai_enabled, confidence, models_used)
    else:
        return place_live_order(symbol, side, qty, price, strategy, stock_name,
                               ai_enabled, confidence, models_used, interval=interval)


def place_paper_order(symbol, side, qty, price, strategy, stock_name, 
                     ai_enabled, confidence, models_used):
    """Execute paper (simulated) order with virtual money."""
    global paper_portfolio
    
    if paper_portfolio is None:
        print("⚠️ Paper portfolio not initialized!")
        return False
    
    # Apply slippage if enabled
    execution_price = price
    if PaperTradingConfig.SIMULATE_SLIPPAGE:
        slippage = price * (PaperTradingConfig.SLIPPAGE_PERCENT / 100)
        if side == 'BUY':
            execution_price = price + slippage
        else:
            execution_price = price - slippage
    
    # Simulate execution delay
    if PaperTradingConfig.SIMULATE_DELAY:
        time.sleep(PaperTradingConfig.EXECUTION_DELAY_MS / 1000.0)
    
    # Execute virtual trade
    if side == 'BUY':
        success, msg = paper_portfolio.execute_buy(symbol, qty, execution_price, stock_name)
    else:
        success, msg = paper_portfolio.execute_sell(symbol, qty, execution_price, stock_name)
    
    status = "SUCCESS" if success else "FAILED"
    order_id = f"PAPER_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    
    # Log message with paper prefix (include symbol for extra clarity)
    prefix = PaperTradingConfig.PAPER_TRADE_PREFIX
    detailed_msg = f"{msg} ({symbol})"
    print(f"{'✅' if success else '❌'} {prefix} {detailed_msg} | ID: {order_id}")
    
    # Log to database (marked as PAPER)
    if PaperTradingConfig.LOG_PAPER_TRADES:
        try:
            trade_data = {
                'timestamp': datetime.now(),
                'symbol': symbol,
                'stock_name': stock_name if stock_name else symbol.split('|')[0],
                'strategy': f"{strategy}_PAPER",
                'signal': side,
                'quantity': qty,
                'price': execution_price,
                'order_id': order_id,
                'status': status,
                'ai_enabled': ai_enabled,
                'confidence': confidence,
                'models_used': models_used
            }
            log_trade(trade_data)
        except Exception as e:
            print(f"⚠️ Failed to log paper trade to database: {e}")
    
    return success


def place_live_order(symbol, side, qty, price, strategy, stock_name,
                    ai_enabled, confidence, models_used, interval="day"):
    """Execute live (real) order via Upstox API with real money.
    Product type is automatically selected: MIS for intraday, CNC for delivery.
    """
    from trading_execution import get_product_type

    from standalone_login_auth import load_token_from_file
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
            'ai_enabled': ai_enabled,
            'confidence': confidence,
            'models_used': models_used
        }
        log_trade(trade_data)
    except Exception as e:
        print(f"⚠️ Failed to log trade to database: {e}")
    
    return status == "SUCCESS"
