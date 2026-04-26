"""
Core Backtesting Engine
=======================
Simulates intraday trades for all Nifty 50 stocks over historical data.
Applies the 19 strategies and handles slippage, brokerage, stop-loss,
profit targets, and 3:15 PM auto square-off.
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, time

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from strategy_engine import StrategyEngine

HISTORICAL_DIR = Path("data/historical")
BROKERAGE_PCT = 0.0005  # 0.05% per trade (buy + sell = 0.1%)
SLIPPAGE_PCT = 0.0002   # 0.02% slippage
SL_PCT = 0.01           # 1% Stop Loss
PT_PCT = 0.02           # 2% Profit Target (1:2 R:R)
SQUARE_OFF_TIME = time(15, 15) # 3:15 PM auto square off

class Backtester:
    def __init__(self):
        self.engine = StrategyEngine()
        self.results = []
    
    def run_backtest(self, csv_path: Path):
        """Run backtest on a single stock CSV."""
        symbol = csv_path.stem.replace("_5m", "")
        
        try:
            df = pd.read_csv(csv_path)
            if df.empty or len(df) < 50:
                return None
                
            # Convert timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True).dt.tz_convert('Asia/Kolkata')
            
            trades = []
            open_position = None
            
            # Note: A real vectorised backtest is faster, but for 19 strategies 
            # and Intraday constraints, iterrows with rolling windows is easier to
            # implement accurately without peeking ahead, albeit slower.
            # We'll simulate bar by bar for realism.
            
            # Start from index 50 to allow indicators to warm up
            for i in range(50, len(df)):
                row = df.iloc[i]
                current_time = row['timestamp'].time()
                current_price = row['close']
                
                # Check for open position management FIRST
                if open_position:
                    days_held = (row['timestamp'].date() - open_position['entry_time'].date()).days
                    # Intraday square-off
                    if current_time >= SQUARE_OFF_TIME or days_held > 0:
                        exit_price = current_price * (1 - SLIPPAGE_PCT) if open_position['type'] == 'BUY' else current_price * (1 + SLIPPAGE_PCT)
                        self._close_position(trades, open_position, exit_price, row['timestamp'], "SQUARE_OFF")
                        open_position = None
                        continue
                    
                    # Stop Loss / Profit Target
                    if open_position['type'] == 'BUY':
                        if current_price <= open_position['sl']:
                            self._close_position(trades, open_position, open_position['sl'], row['timestamp'], "STOP_LOSS")
                            open_position = None
                            continue
                        elif current_price >= open_position['pt']:
                            self._close_position(trades, open_position, open_position['pt'], row['timestamp'], "PROFIT_TARGET")
                            open_position = None
                            continue
                    else: # SELL
                        if current_price >= open_position['sl']:
                            self._close_position(trades, open_position, open_position['sl'], row['timestamp'], "STOP_LOSS")
                            open_position = None
                            continue
                        elif current_price <= open_position['pt']:
                            self._close_position(trades, open_position, open_position['pt'], row['timestamp'], "PROFIT_TARGET")
                            open_position = None
                            continue
                
                # Look for new entries ONLY if we don't have an open position 
                # AND it is before 3:00 PM
                if not open_position and current_time < time(15, 0):
                    # We pass the historical slice up to the current bar
                    # This is O(N^2) but guarantees index stability for your strategies
                    hist_slice = df.iloc[:i+1].copy()
                    
                    # Call all strategies. This computes indicators dynamically.
                    # This returns a dictionary with consensus, buy_count, etc.
                    signals_dict = self.engine.get_all_signals(hist_slice)
                    
                    buys = signals_dict.get('buy_count', 0)
                    sells = signals_dict.get('sell_count', 0)
                    
                    if buys >= 10: # Strong buy consensus
                        entry_price = current_price * (1 + SLIPPAGE_PCT)
                        open_position = {
                            'symbol': symbol,
                            'type': 'BUY',
                            'entry_price': entry_price,
                            'entry_time': row['timestamp'],
                            'sl': entry_price * (1 - SL_PCT),
                            'pt': entry_price * (1 + PT_PCT),
                            'strategy': 'ensemble'
                        }
                    elif sells >= 10:
                        entry_price = current_price * (1 - SLIPPAGE_PCT)
                        open_position = {
                            'symbol': symbol,
                            'type': 'SELL',
                            'entry_price': entry_price,
                            'entry_time': row['timestamp'],
                            'sl': entry_price * (1 + SL_PCT),
                            'pt': entry_price * (1 - PT_PCT),
                            'strategy': 'ensemble'
                        }
            
            return pd.DataFrame(trades)
            
        except Exception as e:
            print(f"[!] Backtest failed for {symbol}: {e}")
            return None

    def _close_position(self, trades_list, pos, exit_price, exit_time, reason):
        """Helper to record a closed trade and compute P&L."""
        if pos['type'] == 'BUY':
            pnl_pct = (exit_price - pos['entry_price']) / pos['entry_price']
        else:
            pnl_pct = (pos['entry_price'] - exit_price) / pos['entry_price']
            
        # Deduct brokerage (round trip)
        pnl_pct -= (BROKERAGE_PCT * 2) 
        
        trades_list.append({
            'symbol': pos['symbol'],
            'type': pos['type'],
            'entry_time': pos['entry_time'],
            'exit_time': exit_time,
            'entry_price': pos['entry_price'],
            'exit_price': exit_price,
            'pnl_pct': pnl_pct,
            'reason': reason,
            'strategy': pos['strategy']
        })

    def analyze_results(self, all_trades_df: pd.DataFrame):
        """Compute metrics from trade list."""
        if all_trades_df.empty:
            return None
            
        total_trades = len(all_trades_df)
        winning_trades = all_trades_df[all_trades_df['pnl_pct'] > 0]
        losing_trades = all_trades_df[all_trades_df['pnl_pct'] <= 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        avg_win = winning_trades['pnl_pct'].mean() if not winning_trades.empty else 0
        avg_loss = losing_trades['pnl_pct'].mean() if not losing_trades.empty else 0
        
        # Risk Reward
        rr_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        # Cumulative Return
        all_trades_df['cum_return'] = (1 + all_trades_df['pnl_pct']).cumprod()
        total_return = all_trades_df['cum_return'].iloc[-1] - 1 if not all_trades_df.empty else 0
        
        # Max Drawdown
        roll_max = all_trades_df['cum_return'].cummax()
        drawdown = all_trades_df['cum_return'] / roll_max - 1.0
        max_drawdown = drawdown.min()
        
        # Sharpe Ratio (annualised, using daily P&L series)
        all_trades_df['trade_date'] = all_trades_df['entry_time'].dt.date
        daily_pnl = all_trades_df.groupby('trade_date')['pnl_pct'].sum()
        sharpe = 0.0
        if len(daily_pnl) > 1 and daily_pnl.std() != 0:
            sharpe = (daily_pnl.mean() / daily_pnl.std()) * (252 ** 0.5)

        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_return_pct': total_return * 100,
            'max_drawdown_pct': max_drawdown * 100,
            'risk_reward': rr_ratio,
            'avg_win_pct': avg_win * 100,
            'avg_loss_pct': avg_loss * 100,
            'sharpe_ratio': round(sharpe, 3)
        }

if __name__ == "__main__":
    import glob
    bt = Backtester()
    
    csv_files = glob.glob("data/historical/*_5m.csv")
    if not csv_files:
        print("[!] No historical data found. Please run data_downloader.py first.")
        sys.exit(1)
        
    print(f"==================================================")
    print(f"[*] STARTING INTRADAY BACKTEST")
    print(f"   Files found: {len(csv_files)}")
    print(f"==================================================\n")
    
    all_trades = []
    
    # We will test on just 3 stocks first for speed
    for csv_file in csv_files:
        symbol = Path(csv_file).stem.replace("_5m", "")
        print(f"[*] Testing {symbol}...")
        trades_df = bt.run_backtest(Path(csv_file))
        if trades_df is not None and not trades_df.empty:
            all_trades.append(trades_df)
            print(f"   -> Placed {len(trades_df)} simulated trades")
        else:
            print(f"   -> No trades placed")
            
    if all_trades:
        final_df = pd.concat(all_trades, ignore_index=True)
        # Sort chronologically
        final_df = final_df.sort_values('entry_time')
        
        print(f"\n==================================================")
        print(f"[*] BACKTEST RESULTS")
        metrics = bt.analyze_results(final_df)
        if metrics:
            print(f"   Total Trades : {metrics['total_trades']}")
            print(f"   Win Rate     : {metrics['win_rate']*100:.2f}%")
            print(f"   Total Return : {metrics['total_return_pct']:.2f}%")
            print(f"   Max Drawdown : {metrics['max_drawdown_pct']:.2f}%")
            print(f"   Risk/Reward  : 1:{metrics['risk_reward']:.2f}")
            print(f"   Sharpe Ratio : {metrics['sharpe_ratio']:.3f}")
            print(f"   Avg Win      : +{metrics['avg_win_pct']:.2f}%")
            print(f"   Avg Loss     : {metrics['avg_loss_pct']:.2f}%")
        print(f"==================================================")
    else:
        print("[!] No trades executed across the dataset.")
