"""
RL Configuration
----------------
Configuration settings for reinforcement learning system.
"""

from pathlib import Path


class RLConfig:
    """Configuration for RL learning system."""
    
    # ========================================
    # Learning Modes
    # ========================================
    ENABLE_LIVE_LEARNING = False  # Set True to learn from real trades (CAUTION!)
    ENABLE_SIMULATION_LEARNING = True  # Learn from historical data
    
    # ========================================
    # Training Schedule
    # ========================================
    TRAIN_EVERY_N_TRADES = 10  # Train after every N completed trades
    SAVE_CHECKPOINT_EVERY_N_TRADES = 50  # Save model checkpoint frequency
    MIN_EXPERIENCES_TO_START_TRAINING = 64  # Minimum experiences before training starts
    
    # ========================================
    # RL Hyperparameters
    # ========================================
    LEARNING_RATE = 0.0001  # Lower for stability in production
    GAMMA = 0.99  # Discount factor for future rewards
    EPSILON_START = 0.3  # Initial exploration rate (lower for production)
    EPSILON_DECAY = 0.995  # Decay rate per training step
    EPSILON_MIN = 0.05  # Minimum exploration rate
    
    # ========================================
    # Experience Replay
    # ========================================
    BUFFER_SIZE = 10000  # Maximum experiences to store
    BATCH_SIZE = 64  # Training batch size
    
    # ========================================
    # Reward Shaping
    # ========================================
    PROFIT_REWARD_SCALE = 100.0  # Scale factor for profit-based rewards
    HOLD_TIME_PENALTY_THRESHOLD = 5  # Days before applying hold penalty
    MAX_HOLD_TIME_PENALTY = 0.5  # Maximum penalty for holding too long
    
    # ========================================
    # Model Paths
    # ========================================
    BASE_DIR = Path(__file__).parent / "data" / "trained_models"
    RL_MODEL_PATH = BASE_DIR / "rl_agent_live.pth"
    RL_CHECKPOINT_DIR = BASE_DIR / "rl_checkpoints"
    
    # Ensure directories exist
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    RL_CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    
    # ========================================
    # Ensemble Weights (when RL is enabled)
    # ========================================
    ENSEMBLE_WEIGHTS = {
        'lstm': 0.35,      # LSTM prediction weight
        'sentiment': 0.25,  # Sentiment analysis weight
        'strategy': 0.25,   # Technical strategy weight
        'rl': 0.15         # RL agent weight (start conservative)
    }
    
    # ========================================
    # Safety Limits
    # ========================================
    MAX_RL_CAPITAL_ALLOCATION = 0.2  # Max 20% of capital for RL-influenced trades
    MIN_RL_CONFIDENCE = 0.6  # Minimum confidence to execute RL trade
    MAX_DAILY_LOSS_PCT = 2.0  # Stop trading if daily loss exceeds this %
    
    # ========================================
    # Performance Monitoring
    # ========================================
    PERFORMANCE_WINDOW = 50  # Number of trades to monitor for performance
    MIN_WIN_RATE_THRESHOLD = 0.45  # Alert if win rate drops below this
    AUTO_DISABLE_ON_POOR_PERFORMANCE = True  # Auto-disable RL if performance poor
    
    # ========================================
    # Checkpoint Management
    # ========================================
    MAX_CHECKPOINTS_TO_KEEP = 5  # Keep last N checkpoints
    
    @classmethod
    def get_config_summary(cls) -> str:
        """Get human-readable configuration summary."""
        return f"""
RL Configuration Summary:
========================
Learning Mode:
  - Live Learning: {'ENABLED ⚠️' if cls.ENABLE_LIVE_LEARNING else 'DISABLED ✓'}
  - Simulation Learning: {'ENABLED' if cls.ENABLE_SIMULATION_LEARNING else 'DISABLED'}

Training:
  - Train every: {cls.TRAIN_EVERY_N_TRADES} trades
  - Save checkpoint every: {cls.SAVE_CHECKPOINT_EVERY_N_TRADES} trades
  - Batch size: {cls.BATCH_SIZE}

Hyperparameters:
  - Learning rate: {cls.LEARNING_RATE}
  - Epsilon: {cls.EPSILON_START} → {cls.EPSILON_MIN}
  - Gamma: {cls.GAMMA}

Safety:
  - Max RL capital: {cls.MAX_RL_CAPITAL_ALLOCATION * 100}%
  - Min confidence: {cls.MIN_RL_CONFIDENCE}
  - Max daily loss: {cls.MAX_DAILY_LOSS_PCT}%

Model Path: {cls.RL_MODEL_PATH}
"""


if __name__ == "__main__":
    print(RLConfig.get_config_summary())
