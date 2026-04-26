import unittest
import pandas as pd
import numpy as np
from strategy_engine import StrategyEngine

class TestStrategies(unittest.TestCase):

    def setUp(self):
        # Create dummy data
        dates = pd.date_range(start='2025-01-01', periods=200)
        self.df = pd.DataFrame({
            'time': dates,
            'open': np.random.uniform(100, 200, 200),
            'high': np.random.uniform(100, 200, 200) + 5,
            'low': np.random.uniform(100, 200, 200) - 5,
            'close': np.random.uniform(100, 200, 200),
            'volume': np.random.randint(1000, 5000, 200)
        })

    def test_ma_crossover(self):
        engine = StrategyEngine("ma_crossover")
        res = engine.run_strategy(self.df.copy())
        self.assertIn('signal', res.columns)
        self.assertTrue(set(res['signal'].unique()).issubset({'BUY', 'SELL', 'HOLD'}))

    def test_rsi_reversion(self):
        engine = StrategyEngine("rsi_reversion")
        # Manipulate data to force signals
        df = self.df.copy()
        # Force low RSI
        df.loc[190:, 'close'] = df.loc[190:, 'close'] * 0.5 
        res = engine.run_strategy(df)
        self.assertIn('signal', res.columns)

    def test_breakout(self):
        engine = StrategyEngine("breakout")
        res = engine.run_strategy(self.df.copy())
        self.assertIn('Rolling_Max', res.columns)
        self.assertIn('signal', res.columns)

    def test_vwap(self):
        engine = StrategyEngine("vwap")
        res = engine.run_strategy(self.df.copy())
        self.assertIn('VWAP', res.columns)
        self.assertIn('signal', res.columns)

    def test_bollinger(self):
        engine = StrategyEngine("bollinger")
        res = engine.run_strategy(self.df.copy())
        self.assertIn('Upper_Band', res.columns)
        self.assertIn('signal', res.columns)

if __name__ == '__main__':
    unittest.main()
