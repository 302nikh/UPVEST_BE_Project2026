"""
Ensemble Decision Engine
------------------------
Combines multiple AI models for robust trading decisions.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np


class Signal(Enum):
    """Trading signals."""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"
    NO_ACTION = "NO_ACTION"


@dataclass
class ModelOutput:
    """Standard output format for each model."""
    signal: str  # "BUY", "SELL", "HOLD"
    confidence: float  # 0.0 to 1.0
    prediction: Optional[float] = None  # Price prediction if applicable
    reason: str = ""


class EnsembleEngine:
    """
    Combines predictions from multiple AI models using weighted voting.
    
    Models:
    - LSTM Price Predictor (40%)
    - Sentiment Analyzer (25%)
    - Technical Strategy (20%)
    - RL Agent (15%) - when available
    """
    
    def __init__(self):
        """Initialize ensemble with default weights."""
        # Model weights (must sum to 1.0)
        self.weights = {
            "lstm": 0.40,       # Price prediction
            "sentiment": 0.25,  # News sentiment
            "strategy": 0.20,   # Technical strategy
            "rl_agent": 0.15    # RL agent (when available)
        }
        
        # Confidence thresholds
        self.strong_signal_threshold = 0.75  # Confidence for STRONG signals
        self.action_threshold = 0.50         # Minimum confidence to act
        
        # Signal value mapping for voting
        self.signal_values = {
            "BUY": 1.0,
            "STRONG_BUY": 1.5,
            "HOLD": 0.0,
            "SELL": -1.0,
            "STRONG_SELL": -1.5,
            "NO_ACTION": 0.0
        }
    
    def set_weights(self, weights: Dict[str, float]):
        """
        Update model weights.
        
        Args:
            weights: Dict with model names and their weights
        """
        total = sum(weights.values())
        if abs(total - 1.0) > 0.01:
            # Normalize weights
            weights = {k: v / total for k, v in weights.items()}
        
        self.weights.update(weights)
    
    def _normalize_signal(self, signal: str) -> str:
        """Normalize signal strings."""
        signal = signal.upper().strip()
        
        if signal in ["BUY", "LONG", "BULLISH"]:
            return "BUY"
        elif signal in ["SELL", "SHORT", "BEARISH"]:
            return "SELL"
        elif signal in ["HOLD", "WAIT", "NEUTRAL"]:
            return "HOLD"
        else:
            return "HOLD"
    
    def _sentiment_to_signal(self, sentiment: str, score: float) -> ModelOutput:
        """Convert sentiment analysis result to trading signal."""
        sentiment = sentiment.lower()
        
        if sentiment == "bullish" or (sentiment == "positive" and score > 0.3):
            signal = "BUY"
            confidence = min(0.5 + score, 0.9)
        elif sentiment == "bearish" or (sentiment == "negative" and score < -0.3):
            signal = "SELL"
            confidence = min(0.5 + abs(score), 0.9)
        else:
            signal = "HOLD"
            confidence = 0.5
        
        return ModelOutput(
            signal=signal,
            confidence=confidence,
            reason=f"Sentiment: {sentiment} (score: {score:.2f})"
        )
    
    def _price_to_signal(self, current_price: float, predicted_price: float, 
                         confidence: float = 0.7) -> ModelOutput:
        """Convert price prediction to trading signal."""
        if current_price <= 0:
            return ModelOutput(signal="HOLD", confidence=0.5, reason="Invalid price")
        
        pct_change = (predicted_price - current_price) / current_price * 100
        
        if pct_change > 3.0:  # Predicted to rise >3%
            signal = "BUY"
            adj_confidence = min(confidence * (1 + abs(pct_change) / 10), 0.95)
        elif pct_change < -3.0:  # Predicted to fall >3%
            signal = "SELL"
            adj_confidence = min(confidence * (1 + abs(pct_change) / 10), 0.95)
        elif pct_change > 1.0:  # Small rise
            signal = "BUY"
            adj_confidence = confidence * 0.7
        elif pct_change < -1.0:  # Small fall
            signal = "SELL"
            adj_confidence = confidence * 0.7
        else:
            signal = "HOLD"
            adj_confidence = confidence * 0.5
        
        return ModelOutput(
            signal=signal,
            confidence=adj_confidence,
            prediction=predicted_price,
            reason=f"Predicted {pct_change:+.2f}% move to ₹{predicted_price:.2f}"
        )
    
    def combine_signals(
        self,
        lstm_output: Optional[ModelOutput] = None,
        sentiment_output: Optional[ModelOutput] = None,
        strategy_output: Optional[ModelOutput] = None,
        rl_output: Optional[ModelOutput] = None
    ) -> Dict:
        """
        Combine signals from all available models.
        
        Args:
            lstm_output: LSTM price prediction signal
            sentiment_output: Sentiment analysis signal
            strategy_output: Technical strategy signal
            rl_output: RL agent signal (optional)
            
        Returns:
            Dict with final decision and details
        """
        available_models = []
        weighted_sum = 0.0
        total_weight = 0.0
        all_reasons = []
        
        # Process each model
        models = [
            ("lstm", lstm_output, self.weights["lstm"]),
            ("sentiment", sentiment_output, self.weights["sentiment"]),
            ("strategy", strategy_output, self.weights["strategy"]),
            ("rl_agent", rl_output, self.weights["rl_agent"])
        ]
        
        for model_name, output, weight in models:
            if output is None:
                continue
            
            available_models.append(model_name)
            signal_value = self.signal_values.get(output.signal, 0.0)
            
            # Weight by both model importance and confidence
            effective_weight = weight * output.confidence
            weighted_sum += signal_value * effective_weight
            total_weight += effective_weight
            
            all_reasons.append(f"{model_name}: {output.signal} ({output.confidence:.0%})")
        
        if total_weight == 0:
            return {
                "final_signal": Signal.NO_ACTION.value,
                "confidence": 0.0,
                "action": "HOLD",
                "reason": "No model outputs available",
                "models_used": [],
                "details": {}
            }
        
        # Calculate final score (-1.5 to +1.5)
        final_score = weighted_sum / total_weight
        
        # Determine final signal
        if final_score >= 1.0:
            final_signal = Signal.STRONG_BUY
            action = "BUY"
        elif final_score >= 0.4:
            final_signal = Signal.BUY
            action = "BUY"
        elif final_score <= -1.0:
            final_signal = Signal.STRONG_SELL
            action = "SELL"
        elif final_score <= -0.4:
            final_signal = Signal.SELL
            action = "SELL"
        else:
            final_signal = Signal.HOLD
            action = "HOLD"
        
        # Calculate overall confidence
        confidence = min(abs(final_score) / 1.5, 1.0)
        
        # Check if confidence is sufficient
        if confidence < self.action_threshold and action != "HOLD":
            final_signal = Signal.HOLD
            action = "HOLD"
            all_reasons.append(f"Low confidence ({confidence:.0%})")
        
        return {
            "final_signal": final_signal.value,
            "confidence": round(confidence, 3),
            "action": action,
            "score": round(final_score, 3),
            "reason": " | ".join(all_reasons),
            "models_used": available_models,
            "should_trade": action in ["BUY", "SELL"] and confidence >= self.action_threshold,
            "details": {
                "lstm": lstm_output.__dict__ if lstm_output else None,
                "sentiment": sentiment_output.__dict__ if sentiment_output else None,
                "strategy": strategy_output.__dict__ if strategy_output else None,
                "rl_agent": rl_output.__dict__ if rl_output else None
            }
        }
    
    def get_trading_decision(
        self,
        current_price: float,
        predicted_price: Optional[float] = None,
        lstm_confidence: float = 0.7,
        sentiment: Optional[str] = None,
        sentiment_score: float = 0.0,
        strategy_signal: Optional[str] = None,
        strategy_confidence: float = 0.5,
        rl_signal: Optional[str] = None,
        rl_confidence: float = 0.5
    ) -> Dict:
        """
        Convenience method to get trading decision from raw inputs.
        
        Args:
            current_price: Current stock price
            predicted_price: LSTM predicted price
            lstm_confidence: LSTM model confidence
            sentiment: Sentiment ("bullish"/"bearish"/"neutral")
            sentiment_score: Sentiment score (-1 to +1)
            strategy_signal: Technical strategy signal
            strategy_confidence: Strategy confidence
            rl_signal: RL agent signal
            rl_confidence: RL agent confidence
            
        Returns:
            Final trading decision dict
        """
        # Convert inputs to ModelOutput objects
        lstm_output = None
        if predicted_price is not None:
            lstm_output = self._price_to_signal(current_price, predicted_price, lstm_confidence)
        
        sentiment_output = None
        if sentiment is not None:
            sentiment_output = self._sentiment_to_signal(sentiment, sentiment_score)
        
        strategy_output = None
        if strategy_signal is not None:
            strategy_output = ModelOutput(
                signal=self._normalize_signal(strategy_signal),
                confidence=strategy_confidence,
                reason=f"Strategy: {strategy_signal}"
            )
        
        rl_output = None
        if rl_signal is not None:
            rl_output = ModelOutput(
                signal=self._normalize_signal(rl_signal),
                confidence=rl_confidence,
                reason=f"RL Agent: {rl_signal}"
            )
        
        return self.combine_signals(lstm_output, sentiment_output, strategy_output, rl_output)


# Singleton
_engine_instance = None

def get_ensemble_engine() -> EnsembleEngine:
    """Get or create ensemble engine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = EnsembleEngine()
    return _engine_instance


if __name__ == "__main__":
    # Test the ensemble engine
    print("🎯 Testing Ensemble Decision Engine...")
    
    engine = EnsembleEngine()
    
    # Test case 1: All signals agree (BUY)
    result = engine.get_trading_decision(
        current_price=100.0,
        predicted_price=108.0,  # +8% predicted
        lstm_confidence=0.8,
        sentiment="bullish",
        sentiment_score=0.6,
        strategy_signal="BUY",
        strategy_confidence=0.7
    )
    
    print(f"\n📊 Test Case 1 (All BUY):")
    print(f"   Final Signal: {result['final_signal']}")
    print(f"   Action: {result['action']}")
    print(f"   Confidence: {result['confidence']:.0%}")
    print(f"   Should Trade: {result['should_trade']}")
    
    # Test case 2: Mixed signals
    result = engine.get_trading_decision(
        current_price=100.0,
        predicted_price=102.0,  # +2% predicted
        lstm_confidence=0.6,
        sentiment="bearish",
        sentiment_score=-0.4,
        strategy_signal="HOLD",
        strategy_confidence=0.5
    )
    
    print(f"\n📊 Test Case 2 (Mixed signals):")
    print(f"   Final Signal: {result['final_signal']}")
    print(f"   Action: {result['action']}")
    print(f"   Confidence: {result['confidence']:.0%}")
    print(f"   Reason: {result['reason']}")
