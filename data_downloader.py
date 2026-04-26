"""
Historical Data Downloader
==========================
Downloads up to 60 days of 5-minute interval historical data from Yahoo Finance 
for the configured Nifty 50 universe. Caches data to data/historical/.
"""

import os
import time
import pandas as pd
import yfinance as yf
from pathlib import Path

# Try to import from project universe, fallback to some defaults if missing
try:
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from stock_universe import NIFTY_50
except ImportError:
    print("[WARN] stock_universe.py not found. Using default symbols.")
    NIFTY_50 = [{"name": "RELIANCE"}, {"name": "TCS"}, {"name": "HDFCBANK"}]

HISTORICAL_DIR = Path("data/historical")

def convert_to_yf_symbol(name: str) -> str:
    """Convert UPVEST name to Yahoo Finance ticker (e.g., RELIANCE -> RELIANCE.NS)"""
    # Remove _I suffix if present (from intraday variants)
    base_name = name.split("_")[0]
    return f"{base_name}.NS"

def download_data():
    """Download historical 5m data for all Nifty 50 stocks."""
    HISTORICAL_DIR.mkdir(parents=True, exist_ok=True)
    
    # We use 59d to comfortably fit inside the 60-day limit for 5m candles
    period = "59d"
    interval = "5m"
    
    print(f"==================================================")
    print(f"[*] INITIATING HISTORICAL DATA DOWNLOAD")
    print(f"   Period: {period} | Interval: {interval}")
    print(f"==================================================\n")
    
    successful = 0
    failed = []
    
    # We only need unique base names, don't double download intraday/daily variants
    unique_names = list(set([s["name"].split("_")[0] for s in NIFTY_50]))
    
    for i, name in enumerate(unique_names):
        yf_symbol = convert_to_yf_symbol(name)
        save_path = HISTORICAL_DIR / f"{name}_5m.csv"
        
        print(f"[{i+1}/{len(unique_names)}] Downloading {yf_symbol}...")
        
        try:
            ticker = yf.Ticker(yf_symbol)
            # Fetch data
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                print(f"   [X] No data returned for {yf_symbol}.")
                failed.append(name)
                continue
                
            # Clean and format to match our strategy_engine expected inputs
            # Yahoo returns tz-aware datetime index, convert to string or localized
            df = df.reset_index()
            # The column is named 'Datetime' for intraday data
            time_col = 'Datetime' if 'Datetime' in df.columns else 'Date'
            
            # Format dataframe
            clean_df = pd.DataFrame({
                'timestamp': df[time_col],
                'open': df['Open'],
                'high': df['High'],
                'low': df['Low'],
                'close': df['Close'],
                'volume': df['Volume']
            })
            
            # Drop NaN rows
            clean_df.dropna(inplace=True)
            
            # Save to CSV
            clean_df.to_csv(save_path, index=False)
            print(f"   [OK] Saved {len(clean_df)} candles for {name} ({clean_df['timestamp'].iloc[0].strftime('%Y-%m-%d')} to {clean_df['timestamp'].iloc[-1].strftime('%Y-%m-%d')})")
            successful += 1
            
            # To respect rate limits
            time.sleep(0.5)
            
        except Exception as e:
            print(f"   [ERROR] Failed to process {name}: {e}")
            failed.append(name)
            
    print(f"\n==================================================")
    print(f"[*] DOWNLOAD COMPLETE")
    print(f"   Successfully Downloaded : {successful}/{len(unique_names)}")
    if failed:
        print(f"   Failed Symbols          : {', '.join(failed)}")
    print(f"   Data cached to          : {HISTORICAL_DIR.absolute()}")
    print(f"==================================================")

if __name__ == "__main__":
    download_data()
