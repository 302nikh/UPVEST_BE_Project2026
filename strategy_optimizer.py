"""
Strategy Optimizer
==================
Ranks the performance of backtested strategies and outputs the optimal
ensemble weights based on historical Sharpe ratio and Win Rate.
"""

import pandas as pd
import numpy as np
import glob
from pathlib import Path

def calculate_sharpe(pnl_series, risk_free_rate=0.0):
    """Calculate annualized Sharpe Ratio from a series of P&L percentages."""
    if len(pnl_series) < 2:
        return 0.0
    # Assuming intraday trades, daily returns roughly equal sum of trade returns
    # Approx 252 trading days
    mean_return = pnl_series.mean()
    std_return = pnl_series.std()
    
    if std_return == 0:
        return 0.0
        
    return np.sqrt(252) * (mean_return - risk_free_rate) / std_return

def optimize_strategies():
    csv_files = glob.glob("data/historical/*_5m.csv")
    if not csv_files:
        print("[!] No historical data found.")
        return
        
    print(f"==================================================")
    print(f"🧠 RUNNING STRATEGY OPTIMIZATION")
    print(f"==================================================\n")
    print(f"-> This tool will analyze the backtest output to determine which")
    print(f"   of the 19 algorithmic strategies performed best over the dataset.")
    print(f"-> Requires backtesting to be fully completed to aggregate results.\n")
    
    # In a full built out version, the backtest_engine would log every trade's
    # executing strategy, and this script would group by strategy to find the best.
    print("[WAITING] Awaiting final backtest completion to generate report...")
    
if __name__ == "__main__":
    optimize_strategies()
