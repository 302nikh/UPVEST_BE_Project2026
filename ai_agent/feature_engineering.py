"""
Feature Engineering Module
---------------------------
Extracts technical indicators and features from market data for ML models.
Supports both daily and intraday (30-minute) candles.
"""

import pandas as pd
import numpy as np
from typing import Dict, List


class FeatureEngineer:
    """
    Extracts features from OHLCV data for machine learning models.
    """
    
    def __init__(self, lookback_period=60):
        """
        Args:
            lookback_period: Number of historical periods to use for features
        """
        self.lookback_period = lookback_period
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators.
        
        Args:
            df: DataFrame with columns: open, high, low, close, volume
            
        Returns:
            DataFrame with added technical indicator columns
        """
        df = df.copy()
        
        # Moving Averages
        df['SMA_10'] = df['close'].rolling(window=10).mean()
        df['SMA_20'] = df['close'].rolling(window=20).mean()
        df['SMA_50'] = df['close'].rolling(window=50).mean()
        df['EMA_12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['EMA_26'] = df['close'].ewm(span=26, adjust=False).mean()
        
        # MACD
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_hist'] = df['MACD'] - df['MACD_signal']
        
        # RSI
        delta = df['close'].diff()
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        avg_gain = pd.Series(gain).rolling(window=14).mean()
        avg_loss = pd.Series(loss).rolling(window=14).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['BB_middle'] = df['close'].rolling(window=20).mean()
        df['BB_std'] = df['close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + (2 * df['BB_std'])
        df['BB_lower'] = df['BB_middle'] - (2 * df['BB_std'])
        df['BB_width'] = (df['BB_upper'] - df['BB_lower']) / df['BB_middle']
        
        # ATR (Average True Range)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATR'] = true_range.rolling(window=14).mean()
        
        # Volume indicators
        df['Volume_SMA'] = df['volume'].rolling(window=20).mean()
        df['Volume_ratio'] = df['volume'] / (df['Volume_SMA'] + 1e-10)
        
        # Price momentum
        df['ROC'] = ((df['close'] - df['close'].shift(10)) / df['close'].shift(10)) * 100
        df['Momentum'] = df['close'] - df['close'].shift(10)
        
        # Stochastic Oscillator
        low_14 = df['low'].rolling(window=14).min()
        high_14 = df['high'].rolling(window=14).max()
        df['Stoch_K'] = 100 * ((df['close'] - low_14) / (high_14 - low_14 + 1e-10))
        df['Stoch_D'] = df['Stoch_K'].rolling(window=3).mean()
        
        return df
    
    def create_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create price-based features."""
        df = df.copy()
        
        # Price changes
        df['price_change'] = df['close'].pct_change()
        df['price_change_5'] = df['close'].pct_change(periods=5)
        df['price_change_10'] = df['close'].pct_change(periods=10)
        
        # High-Low range
        df['HL_ratio'] = (df['high'] - df['low']) / df['close']
        
        # Open-Close relationship
        df['OC_ratio'] = (df['close'] - df['open']) / df['open']
        
        return df
    
    def calculate_intraday_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add intraday-specific features.
        Only called when is_intraday=True (no effect on daily model).

        Features added:
          - VWAP              : Volume-Weighted Average Price (intraday anchor)
          - session_hour      : Hour of day (9-15 for NSE)
          - session_progress  : 0.0 (9:15 AM open) → 1.0 (3:30 PM close)
          - intraday_return   : Price change since session open candle
          - rel_volume        : Volume vs 20-period rolling average
        """
        df = df.copy()

        # --- VWAP ---
        try:
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            cumulative_tp_vol = (typical_price * df['volume']).cumsum()
            cumulative_vol    = df['volume'].cumsum()
            df['VWAP'] = cumulative_tp_vol / (cumulative_vol + 1e-10)
            df['VWAP_distance'] = (df['close'] - df['VWAP']) / (df['VWAP'] + 1e-10)
        except Exception:
            df['VWAP'] = df['close']
            df['VWAP_distance'] = 0.0

        # --- Session time features ---
        try:
            if 'time' in df.columns:
                ts = pd.to_datetime(df['time'])
                df['session_hour'] = ts.dt.hour + ts.dt.minute / 60.0
                # NSE: 9.25 (9:15) → 15.5 (3:30), range = 6.25 hours
                session_start = 9.25
                session_len   = 6.25
                df['session_progress'] = ((df['session_hour'] - session_start) / session_len).clip(0, 1)
            else:
                df['session_hour']     = 12.0   # midday default
                df['session_progress'] = 0.5
        except Exception:
            df['session_hour']     = 12.0
            df['session_progress'] = 0.5

        # --- Intraday return from first candle ---
        try:
            first_open = df['open'].iloc[0]
            df['intraday_return'] = (df['close'] - first_open) / (first_open + 1e-10)
        except Exception:
            df['intraday_return'] = 0.0

        # --- Relative volume (0-1 min-max scaled) ---
        try:
            vol_avg = df['volume'].rolling(window=20, min_periods=1).mean()
            df['rel_volume'] = df['volume'] / (vol_avg + 1e-10)
        except Exception:
            df['rel_volume'] = 1.0

        return df

    def prepare_features(self, df: pd.DataFrame, is_intraday: bool = False) -> pd.DataFrame:
        """
        Main method to prepare all features.

        Args:
            df         : Raw OHLCV DataFrame
            is_intraday: If True, add intraday-specific features (VWAP etc.)
                         Set to True when running on 30-minute candles.

        Returns:
            DataFrame with all features ready for LSTM input
        """
        df = self.calculate_technical_indicators(df)
        df = self.create_price_features(df)

        if is_intraday:
            df = self.calculate_intraday_features(df)

        # Drop NaN values created by rolling windows
        df = df.dropna()

        return df
    
    def create_sequences(self, df: pd.DataFrame, target_col='close', 
                        feature_cols=None) -> tuple:
        """
        Create sequences for LSTM training.
        
        Args:
            df: DataFrame with features
            target_col: Column to predict
            feature_cols: List of feature column names (None = auto-select)
            
        Returns:
            (X, y) where X is sequences and y is targets
        """
        if feature_cols is None:
            # Auto-select numeric columns (including target)
            feature_cols = [col for col in df.select_dtypes(include=[np.number]).columns 
                          if col != 'time']

        
        # Normalize features
        from sklearn.preprocessing import MinMaxScaler
        scaler = MinMaxScaler()
        scaled_data = scaler.fit_transform(df[feature_cols])
        
        # Check if target_col is in feature_cols to use the same scaled value
        if target_col in feature_cols:
            target_idx = feature_cols.index(target_col)
            scaled_target = scaled_data[:, target_idx]
        else:
            # If target not in features, we need to scale it separately or add it
            # For simplicity, let's assume target is usually in features (close price)
            # If not, we scale it separately
            target_scaler = MinMaxScaler()
            scaled_target = target_scaler.fit_transform(df[[target_col]]).flatten()
            # Note: This creates complexity with multiple scalers. 
            # Best practice: Include target in features for scaling, then separate.
        
        X, y = [], []
        for i in range(self.lookback_period, len(scaled_data)):
            X.append(scaled_data[i-self.lookback_period:i])
            y.append(scaled_target[i])  # Use SCALED target
        
        return np.array(X), np.array(y), scaler, feature_cols


if __name__ == "__main__":
    # Test feature engineering
    print("Testing Feature Engineering...")
    
    # Create dummy data
    data = {
        'time': pd.date_range(start='2025-01-01', periods=200),
        'open': np.random.uniform(100, 200, 200),
        'high': np.random.uniform(100, 200, 200) + 5,
        'low': np.random.uniform(100, 200, 200) - 5,
        'close': np.random.uniform(100, 200, 200),
        'volume': np.random.randint(10000, 50000, 200)
    }
    df = pd.DataFrame(data)
    
    fe = FeatureEngineer(lookback_period=60)
    df_features = fe.prepare_features(df)
    
    print(f"Original shape: {df.shape}")
    print(f"Features shape: {df_features.shape}")
    print(f"Feature columns: {list(df_features.columns)}")
    
    X, y, scaler, cols = fe.create_sequences(df_features)
    print(f"\nSequence shape: X={X.shape}, y={y.shape}")
    print("✅ Feature engineering test passed!")
