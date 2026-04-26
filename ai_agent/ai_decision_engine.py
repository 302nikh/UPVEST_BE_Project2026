"""
AI Decision Engine
------------------
Combines LSTM predictions with technical strategies for intelligent trading decisions.
"""

import pandas as pd
import numpy as np
import torch
from typing import Dict, Optional
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_agent.feature_engineering import FeatureEngineer
from ai_agent.models.lstm_predictor import LSTMPredictor, LSTMTrainer


class AIDecisionEngine:
    """
    Main AI decision engine that combines ML predictions with rule-based strategies.

    Supports two LSTM models:
      lstm_best.pth      -> trained on daily candles (60-day lookback)
      lstm_intraday.pth  -> trained on 30-min candles (78-candle lookback, VWAP/session feats)

    The correct model is selected automatically based on the is_intraday flag.
    """

    DAILY_MODEL_PATH    = 'data/trained_models/lstm_best.pth'
    INTRADAY_MODEL_PATH = 'data/trained_models/lstm_intraday.pth'
    OFFLINE_INTRADAY_MODEL_PATH = 'data/trained_models/lstm_offline_intraday.pth'

    def __init__(self, model_path=None, use_gpu=False):
        """
        Args:
            model_path: Optional explicit path (overrides auto-detection)
            use_gpu   : Whether to use CUDA for inference
        """
        self.device = 'cuda' if use_gpu and torch.cuda.is_available() else 'cpu'

        # Daily model components
        self.feature_engineer = FeatureEngineer(lookback_period=60)
        self.model        = None
        self.trainer      = None
        self.scaler       = None
        self.feature_cols = None

        # Intraday model components (separate)
        self.intraday_feature_engineer = FeatureEngineer(lookback_period=78)
        self.intraday_model        = None
        self.intraday_trainer      = None
        self.intraday_scaler       = None
        self.intraday_feature_cols = None

        # Load daily model
        explicit = model_path or self.DAILY_MODEL_PATH
        if os.path.exists(explicit):
            self._load_daily_model(explicit)

        # Load intraday model (prioritizing the advanced offline-trained weights)
        if os.path.exists(self.OFFLINE_INTRADAY_MODEL_PATH):
            self._load_intraday_model(self.OFFLINE_INTRADAY_MODEL_PATH)
        elif os.path.exists(self.INTRADAY_MODEL_PATH):
            self._load_intraday_model(self.INTRADAY_MODEL_PATH)
        else:
            print("[AI] No intraday model found yet. "
                  "Run: python ai_agent/model_trainer_optimized.py intraday")

        # if daily model failed to load but intraday is available, we don't
        # copy it over here; predict_price() will automatically switch to
        # intraday mode when self.model is None.
        if self.model is None and self.intraday_model is not None:
            print("[AI] Daily model unavailable; intraday model ready for use")

    # ------------------------------------------------------------------
    # Model loading helpers
    # ------------------------------------------------------------------

    def _load_model_from_path(self, model_path, hidden=256, layers=3):
        """Generic model loader. Returns (model, trainer, scaler, feature_cols)."""
        checkpoint = torch.load(model_path, map_location=self.device)

        input_size = 30  # default fallback
        config_path = model_path.replace('.pth', '_config.pkl')
        if os.path.exists(config_path):
            import pickle
            with open(config_path, 'rb') as f:
                cfg = pickle.load(f)
                input_size = cfg.get('input_size', input_size)
                hidden     = cfg.get('hidden_size', hidden)
                layers     = cfg.get('num_layers',  layers)

        scaler = None
        feature_cols = None
        scaler_path = model_path.replace('.pth', '_scaler.pkl')
        if os.path.exists(scaler_path):
            import pickle
            with open(scaler_path, 'rb') as f:
                data = pickle.load(f)
                scaler       = data.get('scaler')
                feature_cols = data.get('feature_cols')

        mdl = LSTMPredictor(input_size=input_size, hidden_size=hidden, num_layers=layers)
        trn = LSTMTrainer(mdl, device=self.device)
        trn.load_model(model_path)
        return mdl, trn, scaler, feature_cols

    def _load_daily_model(self, path):
        """Load daily LSTM model."""
        try:
            self.model, self.trainer, self.scaler, self.feature_cols = \
                self._load_model_from_path(path)
            print(f"[AI] Daily model loaded: {path}")
        except Exception as e:
            print(f"[AI] Could not load daily model: {e}")

    def _load_intraday_model(self, path):
        """Load intraday LSTM model."""
        try:
            self.intraday_model, self.intraday_trainer, \
            self.intraday_scaler, self.intraday_feature_cols = \
                self._load_model_from_path(path)
            print(f"[AI] Intraday model loaded: {path}")
        except Exception as e:
            print(f"[AI] Could not load intraday model: {e}")

    def load_model(self, model_path):
        """Public method kept for backward compatibility."""
        self._load_daily_model(model_path)
    
    def predict_price(self, df: pd.DataFrame, horizon: int = 1,
                      is_intraday: bool = False) -> Dict:
        """
        Predict future price using LSTM.

        Args:
            df          : Historical OHLCV data
            horizon     : Number of periods ahead to predict
            is_intraday : Use the intraday model + features when True

        Returns:
            Dictionary with prediction and confidence
        """
        # if daily model not loaded but we do have an intraday model, switch
        # automatically rather than returning error to caller
        if not is_intraday and self.model is None and self.intraday_model is not None:
            print("[AI] daily model missing, using intraday model automatically")
            is_intraday = True

        # Select model components based on mode
        if is_intraday and self.intraday_model is not None:
            model_ok   = True
            fe         = self.intraday_feature_engineer
            trainer    = self.intraday_trainer
            scaler     = self.intraday_scaler
            feat_cols  = self.intraday_feature_cols
            model_name = "Intraday-LSTM"
        elif self.model is not None:
            model_ok   = True
            fe         = self.feature_engineer
            trainer    = self.trainer
            scaler     = self.scaler
            feat_cols  = self.feature_cols
            model_name = "Daily-LSTM"
        else:
            return {'predicted_price': None, 'confidence': 0.0,
                    'direction': 'HOLD', 'error': 'No model loaded'}

        if is_intraday and self.intraday_model is None:
            # Intraday model not trained yet, warn and fall back
            print("[AI] Intraday model not trained yet, falling back to daily model.")
            model_name = "Daily-LSTM (fallback)"

        try:
            # Prepare features (with intraday extras when applicable)
            df_features = fe.prepare_features(df, is_intraday=is_intraday)

            if len(df_features) < fe.lookback_period:
                return {
                    'predicted_price': None,
                    'confidence': 0.0,
                    'direction': 'HOLD',
                    'error': 'Insufficient data'
                }

            if scaler and feat_cols:
                valid_cols  = [c for c in feat_cols if c in df_features.columns]
                scaled_data = scaler.transform(df_features[valid_cols])
                last_seq    = scaled_data[-fe.lookback_period:]
                X_tensor    = torch.FloatTensor(last_seq).unsqueeze(0).to(self.device)
            else:
                return {'predicted_price': None, 'confidence': 0.0,
                        'direction': 'HOLD', 'error': 'Scaler not loaded'}

            # Predict
            prediction      = trainer.predict(X_tensor)
            scaled_pred     = float(prediction[0][0])

            # Inverse transform
            target_col  = 'close'
            dummy_row   = np.zeros((1, len(valid_cols)))
            if target_col in valid_cols:
                target_idx = valid_cols.index(target_col)
                dummy_row[0, target_idx] = scaled_pred
                inv_row         = scaler.inverse_transform(dummy_row)
                predicted_price = inv_row[0, target_idx]
            else:
                predicted_price = scaled_pred

            current_price    = df['close'].iloc[-1]
            price_change_pct = ((predicted_price - current_price) / current_price) * 100

            if price_change_pct > 0.5:
                direction  = 'BUY'
                confidence = min(abs(price_change_pct) / 2.0, 1.0)
            elif price_change_pct < -0.5:
                direction  = 'SELL'
                confidence = min(abs(price_change_pct) / 2.0, 1.0)
            else:
                direction  = 'HOLD'
                confidence = 0.5

            return {
                'predicted_price':  predicted_price,
                'current_price':    current_price,
                'price_change_pct': price_change_pct,
                'confidence':       confidence,
                'direction':        direction,
                'model_used':       model_name,
                'error':            None
            }

        except Exception as e:
            return {'predicted_price': None, 'confidence': 0.0,
                    'direction': 'HOLD', 'error': str(e)}
    
    def make_decision(self, df: pd.DataFrame, strategy_signal: str,
                      strategy_name: str, is_intraday: bool = False) -> Dict:
        """Combine LSTM prediction with strategy signal for final decision."""
        ai_prediction = self.predict_price(df, is_intraday=is_intraday)

        if ai_prediction['error']:
            return {
                'signal':        strategy_signal,
                'confidence':    0.5,
                'source':        'strategy_only',
                'ai_prediction': None,
                'reason':        f"AI error: {ai_prediction['error']}"
            }

        ai_signal      = ai_prediction['direction']
        ai_confidence  = ai_prediction['confidence']

        if ai_signal == strategy_signal and ai_signal != 'HOLD':
            final_signal      = ai_signal
            final_confidence  = min(ai_confidence * 1.2, 1.0)
            reason = f"AI and {strategy_name} agree ({ai_prediction.get('model_used', 'LSTM')})"
        elif ai_signal == 'HOLD' or strategy_signal == 'HOLD':
            final_signal      = 'HOLD'
            final_confidence  = 0.3
            reason = "Conflicting signals - holding"
        elif ai_signal != strategy_signal:
            if ai_confidence > 0.7:
                final_signal      = ai_signal
                final_confidence  = ai_confidence * 0.8
                reason = f"AI override ({ai_prediction.get('model_used','LSTM')} conf:{ai_confidence:.2f})"
            else:
                final_signal      = 'HOLD'
                final_confidence  = 0.2
                reason = "AI and strategy disagree - holding"
        else:
            final_signal      = strategy_signal
            final_confidence  = 0.6
            reason = "Default to strategy"

        return {
            'signal':           final_signal,
            'confidence':       final_confidence,
            'source':           'ai_enhanced',
            'ai_prediction':    ai_prediction,
            'strategy_signal':  strategy_signal,
            'reason':           reason
        }
    
    def make_ensemble_decision(
        self,
        df: pd.DataFrame,
        strategy_signal: str,
        strategy_name: str,
        stock_name: str = None,
        use_sentiment: bool = True,
        use_rl: bool = False,
        rl_agent = None,
        is_intraday: bool = False       # <-- NEW: drives model + feature selection
    ) -> Dict:
        """
        Make trading decision using ensemble of all AI models.

        When is_intraday=True:
          - Uses lstm_intraday.pth (trained on 30-min candles)
          - Passes is_intraday=True to feature engineering (adds VWAP etc.)
          - Falls back to daily model if intraday model not yet trained

        Weights: LSTM 40% | Sentiment 25% | Strategy 20% | RL 15%
        """
        from .ensemble_engine import get_ensemble_engine, ModelOutput

        ensemble = get_ensemble_engine()

        # 1. LSTM Prediction (intraday or daily model)
        ai_prediction = self.predict_price(df, is_intraday=is_intraday)
        lstm_output   = None
        
        if not ai_prediction.get('error'):
            current_price = df['close'].iloc[-1] if 'close' in df else 0
            predicted_price = ai_prediction.get('predicted_price', current_price)
            lstm_output = ModelOutput(
                signal=ai_prediction.get('direction', 'HOLD'),
                confidence=ai_prediction.get('confidence', 0.5),
                prediction=predicted_price,
                reason=f"LSTM: {ai_prediction.get('confidence', 0):.0%} conf"
            )
        
        # 2. Sentiment Analysis
        sentiment_output = None
        if use_sentiment:
            try:
                from .sentiment_analyzer import get_sentiment_analyzer
                from .news_fetcher import get_news_fetcher
                
                fetcher = get_news_fetcher()
                analyzer = get_sentiment_analyzer(use_finbert=False)  # Use VADER for speed
                
                query = stock_name or "india stock market nifty"
                headlines = fetcher.get_headlines_only(query)
                
                if headlines:
                    mood, score = analyzer.get_market_mood(headlines)
                    
                    # Convert mood to signal
                    if mood == "bullish":
                        sent_signal = "BUY"
                    elif mood == "bearish":
                        sent_signal = "SELL"
                    else:
                        sent_signal = "HOLD"
                    
                    sentiment_output = ModelOutput(
                        signal=sent_signal,
                        confidence=abs(score) if score else 0.5,
                        reason=f"Sentiment: {mood} ({score:.2f})"
                    )
            except Exception as e:
                print(f"⚠️ Sentiment analysis failed: {e}")
        
        # 3. Strategy Signal
        strategy_output = ModelOutput(
            signal=strategy_signal.upper(),
            confidence=0.6,  # Default confidence for strategy
            reason=f"Strategy: {strategy_name}"
        )
        
        # 4. RL Agent (if available)
        rl_output = None
        if use_rl and rl_agent is not None:
            try:
                # Prepare state for RL agent
                features = self.feature_engineer.prepare_features(df)
                if len(features) > 0:
                    state = features.iloc[-1].values
                    rl_signal, rl_conf = rl_agent.get_action_signal(state)
                    rl_output = ModelOutput(
                        signal=rl_signal,
                        confidence=rl_conf,
                        reason=f"RL Agent: {rl_signal}"
                    )
            except Exception as e:
                print(f"⚠️ RL agent failed: {e}")
        
        # 5. Combine with Ensemble Engine
        result = ensemble.combine_signals(
            lstm_output=lstm_output,
            sentiment_output=sentiment_output,
            strategy_output=strategy_output,
            rl_output=rl_output
        )
        
        # Add legacy fields for compatibility
        result['ai_prediction'] = ai_prediction
        result['strategy_signal'] = strategy_signal
        
        return result


if __name__ == "__main__":
    print("Testing AI Decision Engine...")
    
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
    
    # Test without model (should fallback gracefully)
    engine = AIDecisionEngine()
    decision = engine.make_decision(df, strategy_signal='BUY', strategy_name='MA_Crossover')
    
    print(f"Decision: {decision['signal']}")
    print(f"Confidence: {decision['confidence']:.2f}")
    print(f"Reason: {decision['reason']}")
    print("[*] AI Decision Engine test passed!")
