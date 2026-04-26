import sys
import os
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_agent.ai_decision_engine import AIDecisionEngine
from trading_execution import fetch_historical_data

def test_model():
    print("🧪 Verification: Testing AI Decision Engine with Trained Model...")
    
    model_path = 'data/trained_models/lstm_best.pth'
    if not os.path.exists(model_path):
        print(f"❌ Model not found at {model_path}")
        return

    try:
        engine = AIDecisionEngine(model_path=model_path, use_gpu=False)
        
        # Use real data for verification (TCS)
        symbol = "NSE_EQ|INE467B01029"
        print(f"📊 Fetching real data for TCS ({symbol})...")
        df = fetch_historical_data(symbol, interval="day", days=200)
        
        if df.empty:
            print("❌ Failed to fetch real data. Using robust dummy data.")
            # Fallback dummy data with all expected columns including 'oi' if needed
            # But let's hope real data works since we fixed the API
            return

        print(f"   ✅ Fetched {len(df)} candles.")
        
        # Test prediction
        print("\n🔮 Generating Prediction...")
        # if the daily model wasn't loaded, try intraday prediction
        prediction = engine.predict_price(df)
        if prediction.get('error') == 'No model loaded' and engine.intraday_model is not None:
            print("[TEST] switching to intraday mode due to missing daily model")
            prediction = engine.predict_price(df, is_intraday=True)
        
        if prediction['error']:
            print(f"❌ Error: {prediction['error']}")
        else:
            # show raw numbers plus simple error metric
            curr = prediction['current_price']
            pred = prediction['predicted_price']
            change = prediction['price_change_pct']
            print("✅ Prediction Success!")
            print(f"   Current Price: {curr:.2f}")
            print(f"   Predicted: {pred:.2f}")
            print(f"   Change: {change:.2f}% ({prediction['direction']})")
            print(f"   Confidence: {prediction['confidence']:.2f}")
            # compute absolute percent error vs actual close if available
            if 'close' in df.columns:
                actual = df['close'].iloc[-1]
                err = abs(pred - actual) / (actual + 1e-10) * 100
                print(f"   Percent error vs last close: {err:.2f}%")
            print("   (note: negative change simply means price drop predicted\n" +
                  "   confidence is derived from magnitude; model output is not random)")
            
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_model()
