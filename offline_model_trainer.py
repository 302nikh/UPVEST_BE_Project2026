"""
Offline Model Trainer
=====================
Trains the AI LSTMPredictor strictly on localized CSV files, completely bypassing 
the Upstox LIVE API. Extremely useful for paper trading and test runs.
"""

import sys
import os
import glob
import pandas as pd
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from ai_agent.model_trainer_optimized import train_lstm_intraday
except ImportError:
    print("[CRITICAL] Could not import ai_agent. Are you running this from the UPVEST root dir?")
    sys.exit(1)

HISTORICAL_DIR = Path('data/historical')

def resample_to_30m(df_5m: pd.DataFrame) -> pd.DataFrame:
    """Takes a 5-minute OHLCV dataframe and mathematically condenses it to 30-minute variables."""
    # Ensure timestamp is datetime and set as index
    df_5m['timestamp'] = pd.to_datetime(df_5m['timestamp'], utc=True)
    df_5m = df_5m.set_index('timestamp')
    
    # Resample rules for OHLCV
    ohlcv_dict = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }
    
    df_30m = df_5m.resample('30min').agg(ohlcv_dict).dropna()
    df_30m = df_30m.reset_index()
    return df_30m

def build_global_offline_dataset() -> pd.DataFrame:
    """Loads all local CSVs, condenses them to 30m, and stacks them into one huge tensor."""
    csv_files = glob.glob(str(HISTORICAL_DIR / '*_5m.csv'))
    
    if not csv_files:
        print("[!] No historical CSVs found. Please run data_downloader.py first.")
        sys.exit(1)
        
    print(f"[*] Discovered {len(csv_files)} local historical CSV files.")
    print("   Initiating downsampling (5-minute -> 30-minute intervals)...")
    
    all_data = []
    
    # Selecting the first 15 files to prevent PC from locking up or running out of RAM 
    # when allocating PyTorch tensor sequence memory.
    for file in csv_files[:15]:
        symbol = Path(file).stem.replace("_5m", "")
        df_5m = pd.read_csv(file)
        
        if df_5m.empty:
            continue
            
        df_30m = resample_to_30m(df_5m)
        df_30m['symbol'] = symbol
        all_data.append(df_30m)
        
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Sort chronologically, then by symbol for stability
    combined_df = combined_df.sort_values(by=['timestamp', 'symbol']).reset_index(drop=True)
    
    print(f"[*] Extracted an offline pool of {len(combined_df):,} total 30-minute candles.")
    return combined_df

if __name__ == "__main__":
    print("\n" + "="*70)
    print("[*] OFFLINE LSTM TRAINING (ZERO API DEPENDENCY)")
    print("="*70)
    
    global_df = build_global_offline_dataset()
    
    # Define exact output path to replace the generic model
    output_path = 'data/trained_models/lstm_offline_intraday.pth'
    
    print(f"\n   Injecting synthetic offline dataframe into PyTorch LSTMTrainer...")
    print(f"   Target Engine Logic : 30-minute Intraday (LOOKBACK = 78)")
    print(f"   Saving weights to   : {output_path}")
    
    try:
        # Pass data into PyTorch
        # We enforce exactly 100 epochs, but let early stopping trigger via patience=12
        # using train_lstm_intraday which is set to epochs=20 default, we can override or just test with 2
        
        # Test mode arg
        test_mode = len(sys.argv) > 1 and sys.argv[1].lower() == 'test'
        
        if test_mode:
            print("[TEST MODE] ONLY RUNNING 2 EPOCHS")
            trainer, history = train_lstm_intraday(
                global_df,
                epochs=2,
                batch_size=64,
                test_size=0.15,
                learning_rate=0.0005,
                save_path=output_path
            )
        else:
            trainer, history = train_lstm_intraday(
                global_df,
                epochs=100, 
                batch_size=64,
                test_size=0.15,
                learning_rate=0.0005,
                save_path=output_path
            )
            
    except Exception as e:
        import traceback
        print(f"\n[CRITICAL ERROR] Python encountered an active failure during Neural Net matrix calculations.")
        traceback.print_exc()
        sys.exit(1)
