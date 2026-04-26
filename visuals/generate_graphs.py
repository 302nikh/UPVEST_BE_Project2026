import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ensure path index for imports
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai_agent.ai_decision_engine import AIDecisionEngine
from trading_execution import fetch_historical_data


def generate_lstm_vs_actual(symbol='NSE_EQ|INE467B01029', interval='day', days=365):
    # fetch a larger history to ensure we can overcome dropna lag
    print(f"Fetching historical data for {symbol}")
    df = fetch_historical_data(symbol, interval=interval, days=days)
    if df.empty:
        print("No data available, generating synthetic data for demo.")
        dates = pd.date_range(end=pd.Timestamp.today(), periods=200)
        prices = np.cumsum(np.random.randn(200)) + 100
        df = pd.DataFrame({'time': dates, 'open': prices, 'high': prices*1.01,
                           'low': prices*0.99, 'close': prices, 'volume': np.random.randint(1000,5000,200)})

    engine = AIDecisionEngine(use_gpu=False)
    # choose lookback based on which model will run (daily vs intraday)
    is_intraday = engine.model is None and engine.intraday_model is not None
    if is_intraday:
        fe = engine.intraday_feature_engineer
    else:
        fe = engine.feature_engineer
    lookback = fe.lookback_period

    # window must be bigger than lookback due to dropna effects from indicators
    extra_padding = 50
    window_size = lookback + extra_padding

    preds = []
    actual = []
    times = []
    for i in range(window_size, len(df)):
        window = df.iloc[i-window_size:i].copy()
        result = engine.predict_price(window)
        if result.get('error'):
            print(f"[DEBUG] prediction error at index {i}: {result['error']}")
            continue
        preds.append(result['predicted_price'])
        actual.append(df['close'].iloc[i])
        times.append(df['time'].iloc[i])

    if not preds:
        print("No predictions could be generated.")
        return

    plt.figure(figsize=(10,6))
    plt.plot(times, actual, label='Actual Close')
    plt.plot(times, preds, label='LSTM Prediction')
    plt.title('LSTM Predicted vs Actual Price')
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.legend()
    os.makedirs('plots', exist_ok=True)
    out = 'plots/lstm_vs_actual.png'
    plt.savefig(out)
    print(f"Saved LSTM graph to {out}")


def generate_agent_confidence(symbol='NSE_EQ|INE467B01029', interval='day', days=200):
    df = fetch_historical_data(symbol, interval=interval, days=days)
    if df.empty:
        print("No data; using synthetic for agent demo.")
        dates = pd.date_range(end=pd.Timestamp.today(), periods=200)
        prices = np.cumsum(np.random.randn(200)) + 100
        df = pd.DataFrame({'time': dates, 'open': prices, 'high': prices*1.01,
                           'low': prices*0.99, 'close': prices, 'volume': np.random.randint(1000,5000,200)})

    engine = AIDecisionEngine(use_gpu=False)
    is_intraday = engine.model is None and engine.intraday_model is not None
    if is_intraday:
        fe = engine.intraday_feature_engineer
    else:
        fe = engine.feature_engineer
    lookback = fe.lookback_period

    extra_padding = 50
    window_size = lookback + extra_padding

    confidences = []
    signals = []
    times = []
    # use a dummy constant strategy signal
    strategy_signal = 'BUY'
    for i in range(window_size, len(df)):
        window = df.iloc[i-window_size:i].copy()
        decision = engine.make_decision(window, strategy_signal=strategy_signal, strategy_name='constant')
        if decision.get('reason', '').startswith('AI error'):
            print(f"[DEBUG] decision error at index {i}: {decision.get('reason')}")
        confidences.append(decision.get('confidence', 0))
        signals.append(decision.get('signal', 'HOLD'))
        times.append(df['time'].iloc[i])

    plt.figure(figsize=(10,4))
    plt.plot(times, confidences, marker='o')
    plt.title('Agent Decision Confidence Over Time')
    plt.xlabel('Time')
    plt.ylabel('Confidence')
    os.makedirs('plots', exist_ok=True)
    out = 'plots/agent_confidence.png'
    plt.savefig(out)
    print(f"Saved agent confidence graph to {out}")


if __name__ == '__main__':
    generate_lstm_vs_actual()
    generate_agent_confidence()
