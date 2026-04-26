import os
import sys
# ensure workspace root is on path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from trading_execution import fetch_historical_data
from ai_agent.ai_decision_engine import AIDecisionEngine

symbol='NSE_EQ|INE467B01029'
df = fetch_historical_data(symbol, interval='day', days=200)
print('df length', len(df))
engine = AIDecisionEngine(use_gpu=False)
lookback = engine.intraday_feature_engineer.lookback_period
print('intraday lookback', lookback)

for i in range(lookback, len(df)):
    window = df.iloc[i-lookback:i].copy()
    df_feat = engine.intraday_feature_engineer.prepare_features(window, is_intraday=True)
    print('i', i, 'window', window.shape, 'feat rows', len(df_feat))
    if len(df_feat) >= lookback:
        print('OK at index', i)
        break
