"""
RL Learning Manager
-------------------
Manages online learning for the RL agent including:
- Experience replay buffer
- Training scheduling
- Model checkpointing
- Performance monitoring
"""

import os
import torch
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json

from ai_agent.rl_agent import DQNAgent
from rl_config import RLConfig


class RLLearningManager:
    """
    Manages online learning for RL agent.
    
    Handles:
    - Loading/saving RL agent
    - Experience replay management
    - Training scheduling
    - Performance monitoring
    - Model checkpointing
    """
    
    def __init__(
        self,
        state_dim: int = 34,  # Default from feature engineering (30 features + 4 position)
        action_dim: int = 3,
        config: RLConfig = RLConfig
    ):
        """
        Initialize RL learning manager.
        
        Args:
            state_dim: Dimension of state space
            action_dim: Number of actions (3: HOLD, BUY, SELL)
            config: Configuration object
        """
        self.config = config
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # Initialize RL agent
        self.agent = DQNAgent(
            state_dim=state_dim,
            action_dim=action_dim,
            learning_rate=config.LEARNING_RATE,
            gamma=config.GAMMA,
            epsilon=config.EPSILON_START,
            epsilon_decay=config.EPSILON_DECAY,
            epsilon_min=config.EPSILON_MIN,
            buffer_size=config.BUFFER_SIZE,
            batch_size=config.BATCH_SIZE
        )
        
        # Load existing model if available
        if config.RL_MODEL_PATH.exists():
            self.load_model()
        else:
            print("🆕 No existing RL model found. Starting fresh.")
        
        # Training state
        self.trades_since_last_train = 0
        self.trades_since_last_checkpoint = 0
        self.total_training_steps = 0
        
        # Performance tracking
        self.recent_rewards: List[float] = []
        self.recent_trades: List[Dict] = []
        
        # Checkpoint management
        self.checkpoint_history: List[str] = []
        
        print(f"✅ RL Learning Manager initialized")
        print(f"   State dim: {state_dim}, Action dim: {action_dim}")
        print(f"   Learning: {'LIVE' if config.ENABLE_LIVE_LEARNING else 'SIMULATION'}")
    
    def store_experience(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool
    ):
        """
        Store experience in replay buffer.
        
        Args:
            state: Current state
            action: Action taken
            reward: Reward received
            next_state: Next state
            done: Whether episode is done
        """
        self.agent.store_experience(state, action, reward, next_state, done)
        self.recent_rewards.append(reward)
        
        # Keep only recent rewards for monitoring
        if len(self.recent_rewards) > self.config.PERFORMANCE_WINDOW:
            self.recent_rewards.pop(0)
        
        print(f"📝 Stored experience: action={action}, reward={reward:.2f}")
    
    def train_if_ready(self) -> Optional[Dict]:
        """
        Train agent if conditions are met.
        
        Returns:
            Training metrics if training occurred, None otherwise
        """
        self.trades_since_last_train += 1
        self.trades_since_last_checkpoint += 1
        
        # Check if we should train
        if self.trades_since_last_train < self.config.TRAIN_EVERY_N_TRADES:
            return None
        
        # Check if we have enough experiences
        if len(self.agent.buffer) < self.config.MIN_EXPERIENCES_TO_START_TRAINING:
            print(f"⏳ Not enough experiences yet ({len(self.agent.buffer)}/{self.config.MIN_EXPERIENCES_TO_START_TRAINING})")
            return None
        
        # Only train if live learning is enabled
        if not self.config.ENABLE_LIVE_LEARNING and not self.config.ENABLE_SIMULATION_LEARNING:
            print("⏸️ Learning disabled in config")
            return None
        
        # Train the agent
        print(f"\n🎓 Training RL agent (buffer size: {len(self.agent.buffer)})...")
        
        losses = []
        for _ in range(self.config.TRAIN_EVERY_N_TRADES):  # Multiple training steps
            loss = self.agent.train_step_batch()
            if loss is not None:
                losses.append(loss)
        
        avg_loss = np.mean(losses) if losses else 0
        self.total_training_steps += len(losses)
        self.trades_since_last_train = 0
        
        metrics = {
            'avg_loss': avg_loss,
            'epsilon': self.agent.epsilon,
            'buffer_size': len(self.agent.buffer),
            'training_steps': self.total_training_steps,
            'avg_recent_reward': np.mean(self.recent_rewards) if self.recent_rewards else 0
        }
        
        print(f"   Loss: {avg_loss:.4f} | ε: {self.agent.epsilon:.3f} | "
              f"Avg Reward: {metrics['avg_recent_reward']:.2f}")
        
        # Save checkpoint if needed
        if self.trades_since_last_checkpoint >= self.config.SAVE_CHECKPOINT_EVERY_N_TRADES:
            self.save_checkpoint()
            self.trades_since_last_checkpoint = 0
        
        return metrics
    
    def get_action(self, state: np.ndarray, training: bool = False) -> Tuple[int, str, float]:
        """
        Get action from RL agent.
        
        Args:
            state: Current state
            training: Whether in training mode (uses epsilon-greedy)
            
        Returns:
            Tuple of (action_index, action_name, confidence)
        """
        # Get action from agent
        action_idx = self.agent.select_action(state, training=training)
        
        # Get signal and confidence
        signal, confidence = self.agent.get_action_signal(state)
        
        return action_idx, signal, confidence
    
    def save_model(self, path: Optional[Path] = None):
        """Save RL agent model."""
        path = path or self.config.RL_MODEL_PATH
        self.agent.save(str(path))
        
        # Save metadata
        metadata = {
            'state_dim': self.state_dim,
            'action_dim': self.action_dim,
            'total_training_steps': self.total_training_steps,
            'buffer_size': len(self.agent.buffer),
            'epsilon': self.agent.epsilon,
            'timestamp': datetime.now().isoformat()
        }
        
        metadata_path = path.parent / f"{path.stem}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"💾 Model saved to {path}")
    
    def load_model(self, path: Optional[Path] = None):
        """Load RL agent model."""
        path = path or self.config.RL_MODEL_PATH
        
        if not path.exists():
            print(f"⚠️ Model not found at {path}")
            return False
        
        try:
            self.agent.load(str(path))
            
            # Load metadata if available
            metadata_path = path.parent / f"{path.stem}_metadata.json"
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                self.total_training_steps = metadata.get('total_training_steps', 0)
                print(f"   Training steps: {self.total_training_steps}")
            
            print(f"✅ Model loaded from {path}")
            return True
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def save_checkpoint(self):
        """Save a checkpoint of the current model."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_name = f"rl_checkpoint_{timestamp}_step{self.total_training_steps}.pth"
        checkpoint_path = self.config.RL_CHECKPOINT_DIR / checkpoint_name
        
        self.save_model(checkpoint_path)
        self.checkpoint_history.append(str(checkpoint_path))
        
        # Clean up old checkpoints
        self._cleanup_old_checkpoints()
        
        print(f"📸 Checkpoint saved: {checkpoint_name}")
    
    def _cleanup_old_checkpoints(self):
        """Remove old checkpoints, keeping only the most recent N."""
        if len(self.checkpoint_history) > self.config.MAX_CHECKPOINTS_TO_KEEP:
            # Remove oldest checkpoint
            old_checkpoint = self.checkpoint_history.pop(0)
            try:
                os.remove(old_checkpoint)
                # Remove metadata too
                metadata_path = Path(old_checkpoint).parent / f"{Path(old_checkpoint).stem}_metadata.json"
                if metadata_path.exists():
                    os.remove(metadata_path)
                print(f"🗑️ Removed old checkpoint: {Path(old_checkpoint).name}")
            except Exception as e:
                print(f"⚠️ Error removing old checkpoint: {e}")
    
    def get_learning_metrics(self) -> Dict:
        """Get current learning metrics."""
        return {
            'epsilon': self.agent.epsilon,
            'buffer_size': len(self.agent.buffer),
            'training_steps': self.total_training_steps,
            'trades_since_last_train': self.trades_since_last_train,
            'avg_recent_reward': np.mean(self.recent_rewards) if self.recent_rewards else 0,
            'recent_reward_std': np.std(self.recent_rewards) if self.recent_rewards else 0,
            'checkpoints_saved': len(self.checkpoint_history)
        }
    
    def get_performance_summary(self) -> str:
        """Get human-readable performance summary."""
        metrics = self.get_learning_metrics()
        
        return f"""
RL Agent Performance:
====================
Training:
  - Total steps: {metrics['training_steps']}
  - Buffer size: {metrics['buffer_size']}/{self.config.BUFFER_SIZE}
  - Epsilon: {metrics['epsilon']:.3f}

Recent Performance:
  - Avg reward: {metrics['avg_recent_reward']:.2f}
  - Reward std: {metrics['recent_reward_std']:.2f}
  - Trades since train: {metrics['trades_since_last_train']}

Checkpoints: {metrics['checkpoints_saved']} saved
"""


if __name__ == "__main__":
    print("🧪 Testing RL Learning Manager...\n")
    
    # Initialize manager
    manager = RLLearningManager(state_dim=10, action_dim=3)
    
    # Test 1: Store experiences
    print("Test 1: Storing Experiences")
    for i in range(5):
        state = np.random.randn(10)
        action = np.random.randint(0, 3)
        reward = np.random.randn()
        next_state = np.random.randn(10)
        done = i == 4
        
        manager.store_experience(state, action, reward, next_state, done)
    
    # Test 2: Get action
    print("\nTest 2: Getting Action")
    test_state = np.random.randn(10)
    action_idx, signal, confidence = manager.get_action(test_state)
    print(f"   Action: {signal} (confidence: {confidence:.2%})")
    
    # Test 3: Get metrics
    print("\nTest 3: Learning Metrics")
    print(manager.get_performance_summary())
    
    print("\n✅ RL Learning Manager tests passed!")
