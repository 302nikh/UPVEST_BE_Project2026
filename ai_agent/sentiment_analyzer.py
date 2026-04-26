"""
Sentiment Analyzer Module
--------------------------
Analyzes financial news headlines for market sentiment using FinBERT or VADER.
"""

import os
from typing import List, Dict, Tuple, Optional
from datetime import datetime


class SentimentAnalyzer:
    """
    Analyzes sentiment of financial news using FinBERT or VADER.
    
    FinBERT is preferred for financial text, but VADER is used as fallback
    when transformers library is not available.
    """
    
    def __init__(self, use_finbert: bool = True):
        """
        Initialize the sentiment analyzer.
        
        Args:
            use_finbert: If True, try to use FinBERT. Falls back to VADER if unavailable.
        """
        self.model = None
        self.tokenizer = None
        self.model_type = None
        self.vader = None
        
        if use_finbert:
            self._init_finbert()
        
        if self.model is None:
            self._init_vader()
    
    def _init_finbert(self):
        """Initialize FinBERT model for financial sentiment."""
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
            
            print("🔄 Loading FinBERT model (first time may take a minute)...")
            
            # Use ProsusAI/finbert - trained on financial data
            model_name = "ProsusAI/finbert"
            
            self.pipeline = pipeline(
                "sentiment-analysis",
                model=model_name,
                tokenizer=model_name,
                device=-1  # CPU
            )
            
            self.model_type = "finbert"
            print("✅ FinBERT model loaded successfully!")
            
        except ImportError:
            print("⚠️ transformers library not installed. Install with: pip install transformers")
            self.model = None
        except Exception as e:
            print(f"⚠️ Failed to load FinBERT: {e}")
            self.model = None
    
    def _init_vader(self):
        """Initialize VADER as fallback sentiment analyzer."""
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            self.vader = SentimentIntensityAnalyzer()
            self.model_type = "vader"
            print("✅ Using VADER sentiment analyzer (fallback)")
        except ImportError:
            print("⚠️ VADER not available. Using rule-based fallback.")
            self.model_type = "basic"
    
    def analyze_text(self, text: str) -> Dict:
        """
        Analyze sentiment of a single text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict with 'label' (positive/negative/neutral), 'score' (confidence)
        """
        if not text or len(text.strip()) < 5:
            return {"label": "neutral", "score": 0.5}
        
        if self.model_type == "finbert":
            return self._analyze_finbert(text)
        elif self.model_type == "vader":
            return self._analyze_vader(text)
        else:
            return self._analyze_basic(text)
    
    def _analyze_finbert(self, text: str) -> Dict:
        """Analyze using FinBERT."""
        try:
            # Truncate to max length
            text = text[:512]
            result = self.pipeline(text)[0]
            
            label = result["label"].lower()
            score = result["score"]
            
            # Normalize label
            if label in ["positive", "pos"]:
                label = "positive"
            elif label in ["negative", "neg"]:
                label = "negative"
            else:
                label = "neutral"
            
            return {"label": label, "score": score}
            
        except Exception as e:
            print(f"⚠️ FinBERT error: {e}")
            return {"label": "neutral", "score": 0.5}
    
    def _analyze_vader(self, text: str) -> Dict:
        """Analyze using VADER."""
        try:
            scores = self.vader.polarity_scores(text)
            compound = scores["compound"]
            
            if compound >= 0.05:
                label = "positive"
            elif compound <= -0.05:
                label = "negative"
            else:
                label = "neutral"
            
            # Convert compound to confidence score (0-1)
            confidence = abs(compound)
            
            return {"label": label, "score": confidence}
            
        except Exception as e:
            print(f"⚠️ VADER error: {e}")
            return {"label": "neutral", "score": 0.5}
    
    def _analyze_basic(self, text: str) -> Dict:
        """Basic rule-based sentiment (fallback)."""
        text_lower = text.lower()
        
        positive_words = [
            "rally", "surge", "gain", "profit", "growth", "bullish", "rise",
            "up", "positive", "strong", "outperform", "beat", "exceed",
            "optimistic", "boost", "advance", "climb", "soar", "record high"
        ]
        
        negative_words = [
            "fall", "drop", "loss", "decline", "bearish", "crash", "plunge",
            "down", "negative", "weak", "underperform", "miss", "concern",
            "pessimistic", "slump", "tumble", "sink", "low", "crisis", "fear"
        ]
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            return {"label": "positive", "score": min(0.5 + pos_count * 0.1, 0.9)}
        elif neg_count > pos_count:
            return {"label": "negative", "score": min(0.5 + neg_count * 0.1, 0.9)}
        else:
            return {"label": "neutral", "score": 0.5}
    
    def analyze_headlines(self, headlines: List[str]) -> Dict:
        """
        Analyze multiple headlines and return aggregate sentiment.
        
        Args:
            headlines: List of news headlines
            
        Returns:
            Dict with:
                - overall_sentiment: "bullish", "bearish", "neutral"
                - sentiment_score: Float from -1 (bearish) to +1 (bullish)
                - confidence: Average confidence
                - details: Individual headline analysis
        """
        if not headlines:
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0,
                "confidence": 0.5,
                "details": [],
                "headlines_analyzed": 0
            }
        
        details = []
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        total_score = 0.0
        
        for headline in headlines[:20]:  # Limit to 20 headlines
            result = self.analyze_text(headline)
            
            label = result["label"]
            score = result["score"]
            
            if label == "positive":
                positive_count += 1
                total_score += score
            elif label == "negative":
                negative_count += 1
                total_score -= score
            else:
                neutral_count += 1
            
            details.append({
                "headline": headline[:100],
                "sentiment": label,
                "confidence": score
            })
        
        total = len(headlines[:20])
        
        # Calculate overall sentiment
        if positive_count > negative_count + neutral_count:
            overall = "bullish"
        elif negative_count > positive_count + neutral_count:
            overall = "bearish"
        else:
            overall = "neutral"
        
        # Sentiment score: -1 (fully bearish) to +1 (fully bullish)
        sentiment_score = total_score / total if total > 0 else 0.0
        sentiment_score = max(-1.0, min(1.0, sentiment_score))  # Clamp
        
        # Average confidence
        avg_confidence = sum(d["confidence"] for d in details) / total if total > 0 else 0.5
        
        return {
            "overall_sentiment": overall,
            "sentiment_score": round(sentiment_score, 3),
            "confidence": round(avg_confidence, 3),
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "headlines_analyzed": total,
            "details": details[:5],  # Return top 5 for brevity
            "model_used": self.model_type
        }
    
    def get_market_mood(self, headlines: List[str]) -> Tuple[str, float]:
        """
        Get simple market mood for trading decisions.
        
        Args:
            headlines: List of news headlines
            
        Returns:
            Tuple of (mood: "bullish"/"bearish"/"neutral", score: -1 to +1)
        """
        result = self.analyze_headlines(headlines)
        return result["overall_sentiment"], result["sentiment_score"]


# Singleton instance
_analyzer_instance = None

def get_sentiment_analyzer(use_finbert: bool = True) -> SentimentAnalyzer:
    """Get or create sentiment analyzer instance."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = SentimentAnalyzer(use_finbert=use_finbert)
    return _analyzer_instance


if __name__ == "__main__":
    # Test the sentiment analyzer
    print("🧠 Testing Sentiment Analyzer...")
    
    analyzer = SentimentAnalyzer(use_finbert=False)  # Use VADER for quick test
    
    test_headlines = [
        "TCS shares surge 5% on strong quarterly earnings",
        "Market crash fears as global uncertainty rises",
        "Nifty 50 holds steady amid mixed signals",
        "IT sector outlook remains positive for Q4",
        "Banking stocks under pressure due to NPA concerns"
    ]
    
    print(f"\n📰 Analyzing {len(test_headlines)} headlines...")
    result = analyzer.analyze_headlines(test_headlines)
    
    print(f"\n📊 Results:")
    print(f"   Overall Sentiment: {result['overall_sentiment'].upper()}")
    print(f"   Sentiment Score: {result['sentiment_score']} (-1 to +1)")
    print(f"   Confidence: {result['confidence']}")
    print(f"   Positive: {result['positive_count']}, Negative: {result['negative_count']}, Neutral: {result['neutral_count']}")
    print(f"   Model Used: {result['model_used']}")
