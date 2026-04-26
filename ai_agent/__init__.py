"""
AI Agent Module
----------------
Advanced AI trading components for intelligent decision making.

Components:
- FeatureEngineer: Technical indicator calculation
- AIDecisionEngine: Main decision engine
- SentimentAnalyzer: News sentiment analysis
- EnsembleEngine: Multi-model decision fusion
- DQNAgent: Reinforcement learning agent
- TradingEnv: RL training environment
"""

# Core components
from .feature_engineering import FeatureEngineer
from .ai_decision_engine import AIDecisionEngine

# Sentiment Analysis
from .sentiment_analyzer import SentimentAnalyzer, get_sentiment_analyzer
from .news_fetcher import NewsFetcher, get_news_fetcher

# Ensemble Engine
from .ensemble_engine import EnsembleEngine, get_ensemble_engine, ModelOutput, Signal

# Reinforcement Learning
from .rl_environment import TradingEnv, Action, create_env_from_dataframe
from .rl_agent import DQNAgent, train_agent

__all__ = [
    # Core
    'FeatureEngineer',
    'AIDecisionEngine',
    
    # Sentiment
    'SentimentAnalyzer',
    'get_sentiment_analyzer',
    'NewsFetcher',
    'get_news_fetcher',
    
    # Ensemble
    'EnsembleEngine',
    'get_ensemble_engine',
    'ModelOutput',
    'Signal',
    
    # RL
    'TradingEnv',
    'Action',
    'create_env_from_dataframe',
    'DQNAgent',
    'train_agent'
]
