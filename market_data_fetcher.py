"""
Multi-Source Market Data Fetcher
=================================
Fetches NIFTY 50 data from multiple sources with automatic fallback:
1. Upstox API (Primary - Real-time, most reliable)
2. trading_execution.py (Secondary - Your existing system)
3. Yahoo Finance (Tertiary - Backup)

Usage:
    from market_data_fetcher import get_market_data
    price, indicators = get_market_data("NSE_INDEX|Nifty 50")
"""

import pandas as pd
from datetime import datetime

# Data source priorities
DATA_SOURCES = {
    'upstox': {'priority': 1, 'name': 'Upstox API'},
    'trading_execution': {'priority': 2, 'name': 'Trading Execution'},
    'yahoo': {'priority': 3, 'name': 'Yahoo Finance'}
}

# Track which source is currently working
current_source = None
source_failures = {'upstox': 0, 'trading_execution': 0, 'yahoo': 0}

def fetch_from_upstox(symbol, interval="5minute", days=5):
    """Fetch data from Upstox API"""
    try:
        from trading_execution import fetch_historical_data
        
        # Use your existing Upstox integration
        df = fetch_historical_data(symbol, interval=interval, days=days)
        
        if df is not None and not df.empty:
            print(f"[OK] Data from Upstox ({len(df)} candles)")
            return df
        return None
    except Exception as e:
        print(f"[ERROR] Upstox failed: {e}")
        return None

def fetch_from_trading_execution(symbol, interval="5minute", days=5):
    """Fetch data from trading_execution.py"""
    try:
        from trading_execution import fetch_historical_data
        
        df = fetch_historical_data(symbol, interval=interval, days=days)
        
        if df is not None and not df.empty:
            print(f"[OK] Data from Trading Execution ({len(df)} candles)")
            return df
        return None
    except Exception as e:
        print(f"[ERROR] Trading Execution failed: {e}")
        return None

def fetch_from_yahoo(symbol, interval="5m", period="5d", stock_name=None):
    """Fetch data from Yahoo Finance (fallback)"""
    try:
        import yfinance as yf
        
        # Determine Yahoo ticker
        ticker = None
        
        # 1. Check if it's an index
        if "Nifty 50" in symbol or "^NSEI" in symbol or "NSEI" in symbol:
            ticker = "^NSEI"
        elif "Nifty Bank" in symbol or "^NSEBANK" in symbol or "NSEBANK" in symbol:
            ticker = "^NSEBANK"
        # 2. Use stock_name if provided (e.g. "RELIANCE")
        elif stock_name and "|" not in stock_name:
            ticker = f"{stock_name}.NS"
        # 3. Try to extract ticker from Upstox symbol if it's in format "NSE_EQ|RELIANCE"
        elif "|" in symbol:
            parts = symbol.split('|')
            # If the part after | is a symbol (not numeric ISIN)
            if len(parts) > 1 and not parts[1].startswith('INE'):
                ticker = f"{parts[1]}.NS"
        
        if not ticker:
            # Fallback to symbol but it might fail if it's an ISIN
            ticker = symbol if ".NS" in symbol or "^" in symbol else f"{symbol}.NS"

        print(f"[FETCH] Yahoo Ticker: {ticker}")
        nifty = yf.Ticker(ticker)
        hist = nifty.history(period=period, interval=interval)
        
        if hist.empty:
            # Try one last fallback - sometimes just the symbol works
            if ".NS" in ticker:
                alt_ticker = ticker.replace(".NS", "")
                print(f"[FETCH] Retrying Yahoo with: {alt_ticker}")
                nifty = yf.Ticker(alt_ticker)
                hist = nifty.history(period=period, interval=interval)
        
        if not hist.empty:
            # Rename columns to match your format
            df = pd.DataFrame({
                'open': hist['Open'],
                'high': hist['High'],
                'low': hist['Low'],
                'close': hist['Close'],
                'volume': hist['Volume']
            })
            print(f"[OK] Data from Yahoo Finance ({len(df)} candles)")
            return df
        return None
    except Exception as e:
        print(f"[ERROR] Yahoo Finance failed: {e}")
        return None

def calculate_indicators(df):
    """Calculate technical indicators from dataframe"""
    try:
        if df is None or df.empty:
            return None
        
        current_price = df['close'].iloc[-1]
        
        # SMA calculations with safety checks
        if len(df) >= 50:
            sma_20 = df['close'].rolling(20).mean().iloc[-1]
            sma_50 = df['close'].rolling(50).mean().iloc[-1]
        elif len(df) >= 20:
            sma_20 = df['close'].rolling(20).mean().iloc[-1]
            sma_50 = df['close'].rolling(len(df)).mean().iloc[-1]
        else:
            sma_20 = df['close'].mean()
            sma_50 = df['close'].mean()
        
        # RSI calculation
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, 0.0001)
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        return {
            'price': current_price,
            'sma_20': sma_20,
            'sma_50': sma_50,
            'rsi': current_rsi,
            'data_points': len(df)
        }
    except Exception as e:
        print(f"[!] Indicator calculation failed: {e}")
        return None

def get_market_data(symbol="NSE_INDEX|Nifty 50", interval="5minute", days=5, stock_name=None):
    """
    Get market data with automatic fallback between sources.
    
    Returns:
        tuple: (price, indicators_dict) or (None, None) if all sources fail
    """
    global current_source, source_failures
    
    # Try sources in priority order
    sources = [
        ('upstox', lambda: fetch_from_upstox(symbol, interval, days)),
        ('trading_execution', lambda: fetch_from_trading_execution(symbol, interval, days)),
        ('yahoo', lambda: fetch_from_yahoo(symbol, "5m", "5d", stock_name=stock_name))
    ]
    
    for source_name, fetch_func in sources:
        try:
            print(f"[FETCH] Trying {DATA_SOURCES[source_name]['name']}...")
            df = fetch_func()
            
            if df is not None and not df.empty:
                # Calculate indicators
                indicators = calculate_indicators(df)
                
                if indicators:
                    current_source = source_name
                    source_failures[source_name] = 0  # Reset failure count
                    
                    print(f"[SUCCESS] Using {DATA_SOURCES[source_name]['name']}")
                    return indicators['price'], {
                        'sma_20': indicators['sma_20'],
                        'sma_50': indicators['sma_50'],
                        'rsi': indicators['rsi'],
                        'data_points': indicators['data_points'],
                        'source': DATA_SOURCES[source_name]['name']
                    }
        except Exception as e:
            source_failures[source_name] += 1
            print(f"[ERROR] {DATA_SOURCES[source_name]['name']} error: {e}")
            continue
    
    # All sources failed
    print("[CRITICAL] All data sources failed!")
    return None, None

def get_source_status():
    """Get status of all data sources"""
    return {
        'current': current_source,
        'failures': source_failures,
        'available': [name for name, info in DATA_SOURCES.items()]
    }

if __name__ == "__main__":
    # Test the fetcher
    print("Testing Multi-Source Market Data Fetcher\n")
    
    price, indicators = get_market_data()
    
    if price and indicators:
        print(f"\n[SUCCESS] Market Data Retrieved:")
        print(f"  NIFTY 50: Rs.{price:,.2f}")
        print(f"  SMA(20): Rs.{indicators['sma_20']:,.2f}")
        print(f"  SMA(50): Rs.{indicators['sma_50']:,.2f}")
        print(f"  RSI: {indicators['rsi']:.1f}")
        print(f"  Data Points: {indicators['data_points']}")
        print(f"  Source: {indicators['source']}")
    else:
        print("\n[FAILED] Could not fetch data from any source")
    
    # Show source status
    status = get_source_status()
    print(f"\nSource Status:")
    print(f"  Current: {status['current']}")
    print(f"  Failures: {status['failures']}")
