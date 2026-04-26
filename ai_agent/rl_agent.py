"""
DQN Trading Agent
------------------
Deep Q-Network agent for learning optimal trading decisions.
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
import random
from typing import List, Tuple, Optional
import os


class DQNetwork(nn.Module):
    """Deep Q-Network architecture."""
    
    def __init__(self, state_dim: int, action_dim: int, hidden_dims: List[int] = [128, 64]):
        """
        Initialize DQN.
        
        Args:
            state_dim: Dimension of state space
            action_dim: Number of actions
            hidden_dims: Hidden layer dimensions
        """
        super(DQNetwork, self).__init__()
        
        layers = []
        prev_dim = state_dim
        
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.1)
            ])
            prev_dim = hidden_dim
        
        layers.append(nn.Linear(prev_dim, action_dim))
        
        self.network = nn.Sequential(*layers)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass."""
        return self.network(x)


class ReplayBuffer:
    """Experience replay buffer."""
    
    def __init__(self, capacity: int = 10000):
        self.buffer = deque(maxlen=capacity)
    
    def push(self, state, action, reward, next_state, done):
        """Add experience to buffer."""
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size: int) -> Tuple:
        """Sample a batch of experiences."""
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        return (
            np.array(states),
            np.array(actions),
            np.array(rewards),
            np.array(next_states),
            np.array(dones)
        )
    
    def __len__(self) -> int:
        return len(self.buffer)


class DQNAgent:
    """
    Deep Q-Network trading agent.
    
    Uses double DQN with experience replay for stable learning.
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int = 3,
        learning_rate: float = 0.001,
        gamma: float = 0.99,
        epsilon: float = 1.0,
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.01,
        buffer_size: int = 10000,
        batch_size: int = 64,
        target_update_freq: int = 10,
        device: str = None
    ):
        """
        Initialize DQN agent.
        
        Args:
            state_dim: Dimension of state space
            action_dim: Number of actions (3: HOLD, BUY, SELL)
            learning_rate: Learning rate for optimizer
            gamma: Discount factor for future rewards
            epsilon: Initial exploration rate
            epsilon_decay: Decay rate for epsilon
            epsilon_min: Minimum epsilon value
            buffer_size: Size of replay buffer
            batch_size: Training batch size
            target_update_freq: How often to update target network
            device: 'cuda' or 'cpu'
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq
        
        # Device
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)
        
        # Networks
        self.policy_net = DQNetwork(state_dim, action_dim).to(self.device)
        self.target_net = DQNetwork(state_dim, action_dim).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()
        
        # Optimizer
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=learning_rate)
        self.criterion = nn.MSELoss()
        
        # Replay buffer
        self.buffer = ReplayBuffer(buffer_size)
        
        # Training stats
        self.train_step = 0
        self.episode_rewards = []
    
    def select_action(self, state: np.ndarray, training: bool = True) -> int:
        """
        Select action using epsilon-greedy policy.
        
        Args:
            state: Current state
            training: If True, use epsilon-greedy; else use greedy
            
        Returns:
            Action index (0=HOLD, 1=BUY, 2=SELL)
        """
        if training and random.random() < self.epsilon:
            return random.randint(0, self.action_dim - 1)
        
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_values = self.policy_net(state_tensor)
            return q_values.argmax().item()
    
    def store_experience(self, state, action, reward, next_state, done):
        """Store experience in replay buffer."""
        self.buffer.push(state, action, reward, next_state, done)
    
    def train_step_batch(self) -> Optional[float]:
        """
        Perform one training step.
        
        Returns:
            Loss value if trained, None otherwise
        """
        if len(self.buffer) < self.batch_size:
            return None
        
        # Sample batch
        states, actions, rewards, next_states, dones = self.buffer.sample(self.batch_size)
        
        # Convert to tensors
        states = torch.FloatTensor(states).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        next_states = torch.FloatTensor(next_states).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)
        
        # Current Q values
        current_q = self.policy_net(states).gather(1, actions.unsqueeze(1))
        
        # Target Q values (Double DQN)
        with torch.no_grad():
            # Select actions using policy network
            next_actions = self.policy_net(next_states).argmax(1)
            # Evaluate using target network
            next_q = self.target_net(next_states).gather(1, next_actions.unsqueeze(1)).squeeze()
            target_q = rewards + (1 - dones) * self.gamma * next_q
        
        # Compute loss
        loss = self.criterion(current_q.squeeze(), target_q)
        
        # Backpropagate
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()
        
        # Update target network
        self.train_step += 1
        if self.train_step % self.target_update_freq == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())
        
        # Decay epsilon
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        
        return loss.item()
    
    def get_action_signal(self, state: np.ndarray) -> Tuple[str, float]:
        """
        Get trading signal for integration with ensemble.
        
        Args:
            state: Current market state
            
        Returns:
            Tuple of (signal: "BUY"/"SELL"/"HOLD", confidence: 0-1)
        """
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_values = self.policy_net(state_tensor).squeeze()
            
            # Softmax for confidence
            probs = torch.softmax(q_values, dim=0)
            
            action = q_values.argmax().item()
            confidence = probs[action].item()
        
        action_names = ["HOLD", "BUY", "SELL"]
        return action_names[action], confidence
    
    def save(self, path: str):
        """Save agent to file."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save({
            'policy_net': self.policy_net.state_dict(),
            'target_net': self.target_net.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'train_step': self.train_step,
            'state_dim': self.state_dim,
            'action_dim': self.action_dim
        }, path)
        print(f"✅ Agent saved to {path}")
    
    def load(self, path: str):
        """Load agent from file."""
        checkpoint = torch.load(path, map_location=self.device)
        self.policy_net.load_state_dict(checkpoint['policy_net'])
        self.target_net.load_state_dict(checkpoint['target_net'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.epsilon = checkpoint.get('epsilon', self.epsilon_min)
        self.train_step = checkpoint.get('train_step', 0)
        print(f"✅ Agent loaded from {path}")


def train_agent(
    env,
    agent: DQNAgent,
    episodes: int = 100,
    max_steps: int = 1000,
    verbose: bool = True
) -> List[float]:
    """
    Train DQN agent on environment.
    
    Args:
        env: Trading environment
        agent: DQN agent
        episodes: Number of training episodes
        max_steps: Maximum steps per episode
        verbose: Print progress
        
    Returns:
        List of episode rewards
    """
    episode_rewards = []
    
    for episode in range(episodes):
        state = env.reset()
        episode_reward = 0
        losses = []
        
        for step in range(max_steps):
            # Select action
            action = agent.select_action(state, training=True)
            
            # Take action
            next_state, reward, done, info = env.step(action)
            
            # Store experience
            agent.store_experience(state, action, reward, next_state, done)
            
            # Train
            loss = agent.train_step_batch()
            if loss is not None:
                losses.append(loss)
            
            episode_reward += reward
            state = next_state
            
            if done:
                break
        
        episode_rewards.append(episode_reward)
        agent.episode_rewards.append(episode_reward)
        
        if verbose and (episode + 1) % 10 == 0:
            avg_reward = np.mean(episode_rewards[-10:])
            avg_loss = np.mean(losses) if losses else 0
            summary = env.get_summary()
            print(f"Episode {episode+1}/{episodes} | "
                  f"Reward: {episode_reward:.2f} | "
                  f"Avg10: {avg_reward:.2f} | "
                  f"Return: {summary['total_return']:.2f}% | "
                  f"ε: {agent.epsilon:.3f}")
    
    return episode_rewards


if __name__ == "__main__":
    # Test the DQN agent
    print("🤖 Testing DQN Agent...")
    
    # Create simple test
    state_dim = 10
    action_dim = 3
    
    agent = DQNAgent(state_dim, action_dim)
    
    # Test action selection
    test_state = np.random.randn(state_dim)
    action = agent.select_action(test_state, training=True)
    print(f"\n   Random action: {action}")
    
    # Test signal generation
    signal, confidence = agent.get_action_signal(test_state)
    print(f"   Signal: {signal} (confidence: {confidence:.2%})")
    
    print("\n✅ DQN Agent test passed!")
