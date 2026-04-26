"""
Performance Analytics Module
==============================
Calculates advanced trading performance metrics:
- Sharpe Ratio (annualized)
- Maximum Drawdown
- Win/Loss Streaks
- Strategy-wise Performance
- Day-wise Aggregation

Author: UPVEST Team
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Optional

DB_PATH = Path(__file__).parent / "data" / "trading_database.db"
RISK_FREE_RATE = 0.065  # 6.5% annual (India 10Y bond yield approx)


# ─── Core Metric Functions ───────────────────────────────────────────────────

def calculate_sharpe_ratio(daily_returns: List[float], risk_free_rate: float = RISK_FREE_RATE) -> float:
    """
    Calculate annualized Sharpe Ratio.

    Args:
        daily_returns: List of daily P&L as % returns (e.g. [0.01, -0.005, 0.02])
        risk_free_rate: Annual risk-free rate (default 6.5%)

    Returns:
        float: Annualized Sharpe Ratio (higher is better; >1 is good, >2 is excellent)
    """
    if not daily_returns or len(daily_returns) < 2:
        return 0.0

    returns = np.array(daily_returns, dtype=float)
    daily_rf = risk_free_rate / 252  # Convert annual to daily

    excess_returns = returns - daily_rf
    mean_excess = np.mean(excess_returns)
    std_excess = np.std(excess_returns, ddof=1)

    if std_excess == 0:
        return 0.0

    sharpe = (mean_excess / std_excess) * np.sqrt(252)  # Annualize
    return round(float(sharpe), 3)


def calculate_max_drawdown(equity_curve: List[float]) -> Dict:
    """
    Calculate maximum drawdown from an equity curve.

    Args:
        equity_curve: List of portfolio values over time

    Returns:
        dict with max_drawdown_pct, peak_value, trough_value, recovery_days
    """
    if not equity_curve or len(equity_curve) < 2:
        return {"max_drawdown_pct": 0.0, "peak_value": 0.0, "trough_value": 0.0}

    values = np.array(equity_curve, dtype=float)
    peak = values[0]
    max_dd = 0.0
    peak_val = values[0]
    trough_val = values[0]

    for v in values:
        if v > peak:
            peak = v
        dd = (peak - v) / peak if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd
            peak_val = peak
            trough_val = v

    return {
        "max_drawdown_pct": round(max_dd * 100, 2),
        "peak_value": round(peak_val, 2),
        "trough_value": round(trough_val, 2)
    }


def calculate_win_loss_streaks(trades: List[Dict]) -> Dict:
    """
    Calculate win/loss streaks from a list of trades.

    Args:
        trades: List of trade dicts with 'pnl' key (positive = win, negative = loss)

    Returns:
        dict with current_streak, max_win_streak, max_loss_streak, streak_type
    """
    if not trades:
        return {
            "current_streak": 0,
            "streak_type": "none",
            "max_win_streak": 0,
            "max_loss_streak": 0
        }

    # Filter to closed trades with P&L
    closed = [t for t in trades if t.get('pnl') is not None]
    if not closed:
        return {
            "current_streak": 0,
            "streak_type": "none",
            "max_win_streak": 0,
            "max_loss_streak": 0
        }

    max_win = 0
    max_loss = 0
    current = 0
    current_type = None

    for trade in closed:
        pnl = trade.get('pnl', 0)
        is_win = pnl > 0

        if current_type is None:
            current_type = is_win
            current = 1
        elif current_type == is_win:
            current += 1
        else:
            current_type = is_win
            current = 1

        if is_win:
            max_win = max(max_win, current)
        else:
            max_loss = max(max_loss, current)

    return {
        "current_streak": current,
        "streak_type": "win" if current_type else "loss",
        "max_win_streak": max_win,
        "max_loss_streak": max_loss
    }


def calculate_strategy_performance(trades: List[Dict]) -> List[Dict]:
    """
    Calculate per-strategy win rate and average P&L.

    Args:
        trades: List of trade dicts with 'strategy', 'signal', 'pnl' keys

    Returns:
        List of dicts with strategy performance metrics
    """
    if not trades:
        return []

    strategy_stats = {}

    for trade in trades:
        strategy = trade.get('strategy', 'Unknown')
        pnl = trade.get('pnl', 0) or 0

        if strategy not in strategy_stats:
            strategy_stats[strategy] = {
                'strategy': strategy,
                'total_trades': 0,
                'wins': 0,
                'losses': 0,
                'total_pnl': 0.0,
                'best_trade': 0.0,
                'worst_trade': 0.0
            }

        s = strategy_stats[strategy]
        s['total_trades'] += 1
        s['total_pnl'] += pnl

        if pnl > 0:
            s['wins'] += 1
            s['best_trade'] = max(s['best_trade'], pnl)
        elif pnl < 0:
            s['losses'] += 1
            s['worst_trade'] = min(s['worst_trade'], pnl)

    result = []
    for s in strategy_stats.values():
        total = s['total_trades']
        win_rate = (s['wins'] / total * 100) if total > 0 else 0
        avg_pnl = s['total_pnl'] / total if total > 0 else 0

        result.append({
            'strategy': s['strategy'],
            'total_trades': total,
            'wins': s['wins'],
            'losses': s['losses'],
            'win_rate_pct': round(win_rate, 1),
            'total_pnl': round(s['total_pnl'], 2),
            'avg_pnl_per_trade': round(avg_pnl, 2),
            'best_trade': round(s['best_trade'], 2),
            'worst_trade': round(s['worst_trade'], 2)
        })

    return sorted(result, key=lambda x: x['total_pnl'], reverse=True)


# ─── Database Query Functions ─────────────────────────────────────────────────

def get_day_wise_analytics(days: int = 30) -> List[Dict]:
    """
    Get day-wise aggregated analytics from the database.

    Args:
        days: Number of past days to include

    Returns:
        List of dicts with daily metrics
    """
    if not DB_PATH.exists():
        return _generate_sample_data(days)

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Try daily_summary table first
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, starting_balance, ending_balance, total_pnl,
                   total_trades, buy_trades, sell_trades, ai_trades, rule_based_trades
            FROM daily_summary
            WHERE date >= ? AND date <= ?
            ORDER BY date ASC
        """, (start_date.isoformat(), end_date.isoformat()))

        rows = cursor.fetchall()

        if rows:
            result = []
            for row in rows:
                total = row['total_trades'] or 1
                # Estimate win rate from P&L (positive day = wins > losses)
                pnl = row['total_pnl'] or 0
                win_rate = 60.0 if pnl > 0 else 40.0  # Estimate

                result.append({
                    'date': str(row['date']),
                    'total_pnl': round(pnl, 2),
                    'total_trades': row['total_trades'] or 0,
                    'buy_trades': row['buy_trades'] or 0,
                    'sell_trades': row['sell_trades'] or 0,
                    'starting_balance': round(row['starting_balance'] or 0, 2),
                    'ending_balance': round(row['ending_balance'] or 0, 2),
                    'win_rate_pct': win_rate,
                    'ai_trades': row['ai_trades'] or 0,
                    'rule_based_trades': row['rule_based_trades'] or 0
                })
            conn.close()
            return result

        # Fallback: aggregate from trades table
        cursor.execute("""
            SELECT date,
                   COUNT(*) as total_trades,
                   SUM(CASE WHEN signal='BUY' THEN 1 ELSE 0 END) as buy_trades,
                   SUM(CASE WHEN signal='SELL' THEN 1 ELSE 0 END) as sell_trades,
                   SUM(CASE WHEN ai_enabled=1 THEN 1 ELSE 0 END) as ai_trades
            FROM trades
            WHERE date >= ? AND date <= ?
            GROUP BY date
            ORDER BY date ASC
        """, (start_date.isoformat(), end_date.isoformat()))

        rows = cursor.fetchall()
        conn.close()

        return [{
            'date': str(row['date']),
            'total_pnl': 0.0,
            'total_trades': row['total_trades'] or 0,
            'buy_trades': row['buy_trades'] or 0,
            'sell_trades': row['sell_trades'] or 0,
            'starting_balance': 0.0,
            'ending_balance': 0.0,
            'win_rate_pct': 50.0,
            'ai_trades': row['ai_trades'] or 0,
            'rule_based_trades': 0
        } for row in rows] or _generate_sample_data(days)

    except Exception as e:
        print(f"[ANALYTICS] DB error: {e}")
        return _generate_sample_data(days)


def get_performance_metrics(days: int = 30) -> Dict:
    """
    Get comprehensive performance metrics.

    Returns:
        dict with Sharpe ratio, max drawdown, win rate, streaks, etc.
    """
    day_data = get_day_wise_analytics(days)

    if not day_data:
        return _empty_performance_metrics()

    # Build equity curve and daily returns
    equity_curve = []
    daily_returns = []
    total_pnl = 0.0
    total_trades = 0
    winning_days = 0
    losing_days = 0

    for d in day_data:
        pnl = d.get('total_pnl', 0)
        balance = d.get('ending_balance', 0)
        total_pnl += pnl
        total_trades += d.get('total_trades', 0)

        if balance > 0:
            equity_curve.append(balance)

        if pnl > 0:
            winning_days += 1
        elif pnl < 0:
            losing_days += 1

        # Daily return as %
        start_bal = d.get('starting_balance', 0)
        if start_bal > 0:
            daily_returns.append(pnl / start_bal)

    # Calculate metrics
    sharpe = calculate_sharpe_ratio(daily_returns)
    drawdown = calculate_max_drawdown(equity_curve)
    total_days = winning_days + losing_days
    win_rate = (winning_days / total_days * 100) if total_days > 0 else 0

    return {
        "period_days": days,
        "total_pnl": round(total_pnl, 2),
        "total_trades": total_trades,
        "winning_days": winning_days,
        "losing_days": losing_days,
        "win_rate_pct": round(win_rate, 1),
        "sharpe_ratio": sharpe,
        "max_drawdown_pct": drawdown["max_drawdown_pct"],
        "peak_portfolio_value": drawdown["peak_value"],
        "trough_portfolio_value": drawdown["trough_value"],
        "avg_daily_pnl": round(total_pnl / max(len(day_data), 1), 2),
        "best_day_pnl": round(max((d.get('total_pnl', 0) for d in day_data), default=0), 2),
        "worst_day_pnl": round(min((d.get('total_pnl', 0) for d in day_data), default=0), 2)
    }


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _generate_sample_data(days: int) -> List[Dict]:
    """Generate sample data when DB has no records (for demo/testing)."""
    result = []
    balance = 100000.0
    today = date.today()

    for i in range(days, 0, -1):
        d = today - timedelta(days=i)
        if d.weekday() >= 5:  # Skip weekends
            continue

        pnl = round(np.random.normal(200, 800), 2)
        trades = np.random.randint(2, 8)
        balance += pnl

        result.append({
            'date': d.isoformat(),
            'total_pnl': pnl,
            'total_trades': trades,
            'buy_trades': trades // 2,
            'sell_trades': trades - trades // 2,
            'starting_balance': round(balance - pnl, 2),
            'ending_balance': round(balance, 2),
            'win_rate_pct': round(np.random.uniform(40, 70), 1),
            'ai_trades': trades // 2,
            'rule_based_trades': trades - trades // 2
        })

    return result


def _empty_performance_metrics() -> Dict:
    return {
        "period_days": 30,
        "total_pnl": 0.0,
        "total_trades": 0,
        "winning_days": 0,
        "losing_days": 0,
        "win_rate_pct": 0.0,
        "sharpe_ratio": 0.0,
        "max_drawdown_pct": 0.0,
        "peak_portfolio_value": 0.0,
        "trough_portfolio_value": 0.0,
        "avg_daily_pnl": 0.0,
        "best_day_pnl": 0.0,
        "worst_day_pnl": 0.0
    }


# ─── Example usage ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n📊 Performance Analytics Report")
    print("=" * 50)

    metrics = get_performance_metrics(days=30)
    for k, v in metrics.items():
        print(f"   {k}: {v}")

    print("\n📅 Day-wise Analytics (last 7 days):")
    days = get_day_wise_analytics(days=7)
    for d in days:
        print(f"   {d['date']}: P&L=₹{d['total_pnl']:+,.0f} | Trades={d['total_trades']} | Win%={d['win_rate_pct']:.0f}%")
