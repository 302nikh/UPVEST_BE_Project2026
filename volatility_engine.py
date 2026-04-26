"""
Volatility Engine
=================
Calculates market volatility and provides position-holding strategy guidance.

Key functions:
- ATR-based volatility score (0-1)
- Rolling std-dev volatility
- Recommended hold duration based on volatility
- Position sizing based on volatility + risk tolerance

Author: UPVEST Team
"""

import pandas as pd
import numpy as np
from datetime import datetime


def calculate_atr_volatility(df: pd.DataFrame, period: int = 14) -> float:
    """
    Calculate ATR-based volatility score normalized to 0-1.

    Args:
        df: DataFrame with columns: high, low, close
        period: ATR period (default 14)

    Returns:
        float: Volatility score 0.0 (calm) to 1.0 (very volatile)
    """
    if df is None or len(df) < period + 1:
        return 0.5  # default moderate volatility

    try:
        high = df['high']
        low = df['low']
        close = df['close']

        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # ATR
        atr = tr.rolling(window=period).mean().iloc[-1]

        # Normalize: ATR as % of price
        last_price = close.iloc[-1]
        if last_price <= 0:
            return 0.5

        atr_pct = atr / last_price  # e.g. 0.015 = 1.5%

        # Map to 0-1 scale:
        # < 0.5% = very calm (0.0-0.2)
        # 0.5-1.5% = normal (0.2-0.6)
        # 1.5-3% = volatile (0.6-0.85)
        # > 3% = very volatile (0.85-1.0)
        score = min(1.0, atr_pct / 0.03)
        return round(score, 3)

    except Exception:
        return 0.5


def calculate_rolling_volatility(df: pd.DataFrame, window: int = 20) -> float:
    """
    Calculate rolling standard deviation of returns as volatility.

    Args:
        df: DataFrame with 'close' column
        window: Rolling window (default 20)

    Returns:
        float: Annualized volatility (e.g. 0.25 = 25%)
    """
    if df is None or len(df) < window + 1:
        return 0.20  # default 20% annualized vol

    try:
        returns = df['close'].pct_change().dropna()
        daily_vol = returns.rolling(window=window).std().iloc[-1]
        annualized_vol = daily_vol * np.sqrt(252)
        return round(annualized_vol, 4)
    except Exception:
        return 0.20


def get_hold_duration_minutes(volatility_score: float) -> int:
    """
    Get recommended position hold duration based on volatility.

    High volatility -> shorter hold (exit quickly to lock gains / cut losses)
    Low volatility  -> longer hold (let the trend develop)

    Args:
        volatility_score: 0.0 to 1.0 from calculate_atr_volatility()

    Returns:
        int: Recommended hold duration in minutes
    """
    if volatility_score >= 0.80:
        return 20    # Very volatile: hold max 20 min
    elif volatility_score >= 0.60:
        return 45    # Volatile: hold max 45 min
    elif volatility_score >= 0.40:
        return 90    # Moderate: hold max 90 min
    elif volatility_score >= 0.20:
        return 180   # Calm: hold max 3 hours
    else:
        return 240   # Very calm: hold max 4 hours


def calculate_position_size(
    available_capital: float,
    current_price: float,
    volatility_score: float,
    risk_pct: float = 0.02
) -> int:
    """
    Calculate position size using volatility-adjusted Kelly criterion.

    The higher the volatility, the smaller the position size.

    Args:
        available_capital: Total capital available for this trade
        current_price: Current stock price
        volatility_score: 0.0 to 1.0 from calculate_atr_volatility()
        risk_pct: Max % of capital to risk per trade (default 2%)

    Returns:
        int: Number of shares to buy (minimum 1)
    """
    if available_capital <= 0 or current_price <= 0:
        return 0

    # Reduce position size as volatility increases
    # At vol=0.0: use full risk_pct
    # At vol=1.0: use 25% of risk_pct
    vol_adjustment = 1.0 - (volatility_score * 0.75)
    adjusted_risk_pct = risk_pct * vol_adjustment

    # Capital to risk
    capital_at_risk = available_capital * adjusted_risk_pct

    # Shares
    shares = int(capital_at_risk / current_price)
    return max(1, shares)


def get_volatility_summary(df: pd.DataFrame) -> dict:
    """
    Get a complete volatility summary for a stock.

    Args:
        df: OHLCV DataFrame

    Returns:
        dict with volatility metrics and recommendations
    """
    atr_score = calculate_atr_volatility(df)
    rolling_vol = calculate_rolling_volatility(df)
    hold_minutes = get_hold_duration_minutes(atr_score)

    # Classify
    if atr_score >= 0.80:
        classification = "Very High"
        recommendation = "Use tight stop-loss, short hold duration"
    elif atr_score >= 0.60:
        classification = "High"
        recommendation = "Use trailing stop, moderate hold"
    elif atr_score >= 0.40:
        classification = "Moderate"
        recommendation = "Standard risk management"
    elif atr_score >= 0.20:
        classification = "Low"
        recommendation = "Can hold longer, wider stop-loss"
    else:
        classification = "Very Low"
        recommendation = "Trend-following strategy preferred"

    return {
        "atr_volatility_score": atr_score,
        "annualized_volatility": rolling_vol,
        "classification": classification,
        "recommended_hold_minutes": hold_minutes,
        "recommendation": recommendation
    }


# --- Example usage ---
if __name__ == "__main__":
    import pandas as pd
    import numpy as np

    # Simulate OHLCV data
    np.random.seed(42)
    n = 100
    prices = 1000 + np.cumsum(np.random.randn(n) * 10)
    df = pd.DataFrame({
        'open':   prices + np.random.randn(n) * 2,
        'high':   prices + abs(np.random.randn(n)) * 5,
        'low':    prices - abs(np.random.randn(n)) * 5,
        'close':  prices,
        'volume': np.random.randint(100000, 500000, n)
    })

    summary = get_volatility_summary(df)
    print("\n[CHART] Volatility Summary:")
    for k, v in summary.items():
        print(f"   {k}: {v}")

    # Position sizing example
    size = calculate_position_size(
        available_capital=100000,
        current_price=1000,
        volatility_score=summary['atr_volatility_score']
    )
    print(f"\n[MONEY] Recommended position size: {size} shares")
    print(f"   Capital deployed: INR {size * 1000:,.0f}")
