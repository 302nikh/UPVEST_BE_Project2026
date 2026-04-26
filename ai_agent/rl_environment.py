"""
RL Trading Environment
-----------------------
Custom Gym environment for training reinforcement learning trading agents.
"""

import numpy as np
from typing import Dict, Tuple, Optional, List
from enum import IntEnum
from dataclasses import dataclass


class Action(IntEnum):
    """Trading actions."""
    HOLD = 0
    BUY = 1
    SELL = 2


@dataclass
class Position:
    """Represents a trading position."""
    shares: int = 0
    avg_price: float = 0.0
    unrealized_pnl: float = 0.0


class TradingEnv:
    """
    Trading environment for reinforcement learning.
    
    State Space:
        - Price features (OHLCV normalized)
        - Technical indicators (RSI, MACD, etc.)
        - Position info (holdings, unrealized P&L)
        - Time features (day of week, market session)
    
    Action Space:
        - 0: HOLD
        - 1: BUY
        - 2: SELL
    
    Reward:
        - Realized P&L from trades
        - Penalize holding losing positions
        - Bonus for profitable trades
    """
    
    def __init__(
        self,
        data: np.ndarray,
        feature_names: List[str] = None,
        initial_balance: float = 100000,
        transaction_cost: float = 0.001,  # 0.1% per trade
        max_position_size: int = 100,
        reward_scaling: float = 1.0
    ):
        """
        Initialize trading environment.
        
        Args:
            data: Price and feature data (rows=time, cols=features)
            feature_names: Names of each feature column
            initial_balance: Starting cash balance
            transaction_cost: Cost per trade as fraction (0.001 = 0.1%)
            max_position_size: Maximum shares to hold
            reward_scaling: Scale rewards for training stability
        """
        self.data = data
        self.feature_names = feature_names or []
        self.initial_balance = initial_balance
        self.transaction_cost = transaction_cost
        self.max_position_size = max_position_size
        self.reward_scaling = reward_scaling
        
        # Get price column index (assume 'close' or column 3)
        self.price_idx = self._get_price_idx()
        
        # State dimensions
        self.n_features = data.shape[1]
        self.observation_dim = self.n_features + 4  # +4 for position info
        self.action_dim = 3  # HOLD, BUY, SELL
        
        # Initialize state
        self.reset()
    
    def _get_price_idx(self) -> int:
        """Get index of close price column."""
        if 'close' in self.feature_names:
            return self.feature_names.index('close')
        return min(3, self.data.shape[1] - 1)  # Default to column 3
    
    @property
    def observation_space_shape(self) -> Tuple[int]:
        """Shape of observation space."""
        return (self.observation_dim,)
    
    @property
    def action_space_n(self) -> int:
        """Number of actions."""
        return self.action_dim
    
    def reset(self) -> np.ndarray:
        """
        Reset environment to initial state.
        
        Returns:
            Initial observation
        """
        self.current_step = 0
        self.balance = self.initial_balance
        self.position = Position()
        self.trades = []
        self.total_reward = 0.0
        self.done = False
        
        return self._get_observation()
    
    def _get_observation(self) -> np.ndarray:
        """Get current observation."""
        if self.current_step >= len(self.data):
            self.current_step = len(self.data) - 1
        
        # Market features
        market_features = self.data[self.current_step]
        
        # Position features (normalized)
        current_price = self._get_current_price()
        position_features = np.array([
            self.position.shares / self.max_position_size,  # Normalized position
            self.position.unrealized_pnl / self.initial_balance,  # Normalized PnL
            self.balance / self.initial_balance,  # Normalized balance
            1.0 if self.position.shares > 0 else 0.0  # Has position flag
        ])
        
        return np.concatenate([market_features, position_features])
    
    def _get_current_price(self) -> float:
        """Get current closing price."""
        if self.current_step >= len(self.data):
            return self.data[-1, self.price_idx]
        return self.data[self.current_step, self.price_idx]
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """
        Execute one step in the environment.
        
        Args:
            action: Action to take (0=HOLD, 1=BUY, 2=SELL)
            
        Returns:
            observation: Next state
            reward: Reward for this step
            done: Whether episode is finished
            info: Additional information
        """
        if self.done:
            return self._get_observation(), 0.0, True, {}
        
        current_price = self._get_current_price()
        reward = 0.0
        trade_info = None
        
        # Execute action
        if action == Action.BUY:
            reward, trade_info = self._execute_buy(current_price)
        elif action == Action.SELL:
            reward, trade_info = self._execute_sell(current_price)
        else:  # HOLD
            reward = self._calculate_hold_reward(current_price)
        
        # Move to next step
        self.current_step += 1
        
        # Update unrealized P&L
        if self.position.shares > 0:
            new_price = self._get_current_price()
            self.position.unrealized_pnl = (new_price - self.position.avg_price) * self.position.shares
        
        # Check if done
        if self.current_step >= len(self.data) - 1:
            self.done = True
            # Force liquidation at end
            if self.position.shares > 0:
                final_reward, _ = self._execute_sell(self._get_current_price())
                reward += final_reward
        
        # Scale reward
        scaled_reward = reward * self.reward_scaling
        self.total_reward += scaled_reward
        
        observation = self._get_observation()
        info = {
            "balance": self.balance,
            "position": self.position.shares,
            "unrealized_pnl": self.position.unrealized_pnl,
            "trade": trade_info,
            "step": self.current_step
        }
        
        return observation, scaled_reward, self.done, info
    
    def _execute_buy(self, price: float) -> Tuple[float, Optional[Dict]]:
        """Execute buy order."""
        if self.position.shares >= self.max_position_size:
            return -0.01, None  # Small penalty for invalid action
        
        # Calculate shares to buy (use 10% of balance per trade)
        trade_value = min(self.balance * 0.1, self.balance)
        shares_to_buy = max(1, int(trade_value / (price * (1 + self.transaction_cost))))
        
        if shares_to_buy <= 0 or self.balance < price * shares_to_buy * (1 + self.transaction_cost):
            return -0.01, None  # Not enough balance
        
        # Execute trade
        cost = price * shares_to_buy * (1 + self.transaction_cost)
        self.balance -= cost
        
        # Update position
        if self.position.shares == 0:
            self.position.avg_price = price
        else:
            total_shares = self.position.shares + shares_to_buy
            self.position.avg_price = (
                (self.position.avg_price * self.position.shares + price * shares_to_buy) 
                / total_shares
            )
        
        self.position.shares += shares_to_buy
        
        trade_info = {
            "action": "BUY",
            "shares": shares_to_buy,
            "price": price,
            "cost": cost
        }
        self.trades.append(trade_info)
        
        return 0.0, trade_info  # Neutral reward for buying
    
    def _execute_sell(self, price: float) -> Tuple[float, Optional[Dict]]:
        """Execute sell order."""
        if self.position.shares <= 0:
            return -0.01, None  # Penalty for invalid action
        
        shares_to_sell = self.position.shares
        
        # Calculate profit/loss
        revenue = price * shares_to_sell * (1 - self.transaction_cost)
        cost_basis = self.position.avg_price * shares_to_sell
        profit = revenue - cost_basis
        
        # Update balance
        self.balance += revenue
        
        # Calculate reward (normalized by initial balance)
        pnl_pct = profit / self.initial_balance
        reward = pnl_pct * 100  # Scale up for training
        
        # Bonus for profitable trades
        if profit > 0:
            reward += 0.1
        
        trade_info = {
            "action": "SELL",
            "shares": shares_to_sell,
            "price": price,
            "profit": profit,
            "profit_pct": (profit / cost_basis) * 100 if cost_basis > 0 else 0
        }
        self.trades.append(trade_info)
        
        # Reset position
        self.position = Position()
        
        return reward, trade_info
    
    def _calculate_hold_reward(self, current_price: float) -> float:
        """Calculate reward for holding."""
        if self.position.shares == 0:
            return 0.0  # Neutral if no position
        
        # Small reward/penalty based on unrealized P&L change
        pnl_pct = (current_price - self.position.avg_price) / self.position.avg_price
        return pnl_pct * 0.01  # Very small to encourage trading
    
    def get_portfolio_value(self) -> float:
        """Get total portfolio value."""
        current_price = self._get_current_price()
        return self.balance + (self.position.shares * current_price)
    
    def get_summary(self) -> Dict:
        """Get episode summary."""
        portfolio_value = self.get_portfolio_value()
        return {
            "initial_balance": self.initial_balance,
            "final_balance": self.balance,
            "portfolio_value": portfolio_value,
            "total_return": (portfolio_value - self.initial_balance) / self.initial_balance * 100,
            "total_trades": len(self.trades),
            "total_reward": self.total_reward,
            "position": self.position.shares
        }


def create_env_from_dataframe(df, feature_cols: List[str] = None, **kwargs) -> TradingEnv:
    """
    Create environment from pandas DataFrame.
    
    Args:
        df: DataFrame with OHLCV and features
        feature_cols: Columns to use as features
        **kwargs: Additional arguments for TradingEnv
    """
    if feature_cols is None:
        feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    data = df[feature_cols].values.astype(np.float32)
    
    # Handle NaN/inf
    data = np.nan_to_num(data, nan=0.0, posinf=0.0, neginf=0.0)
    
    return TradingEnv(data, feature_names=feature_cols, **kwargs)


if __name__ == "__main__":
    # Test the environment
    print("🎮 Testing Trading Environment...")
    
    # Create synthetic data
    np.random.seed(42)
    n_steps = 100
    prices = 100 + np.cumsum(np.random.randn(n_steps) * 0.5)
    
    # Simple features: price, returns, volatility (all same length)
    returns = np.zeros(n_steps)
    returns[1:] = np.diff(prices)
    
    volatility = np.ones(n_steps) * 0.5  # Simple constant volatility
    
    data = np.column_stack([prices, returns, volatility])
    
    env = TradingEnv(data, feature_names=['close', 'returns', 'volatility'])
    
    # Random agent test
    obs = env.reset()
    total_reward = 0
    
    for i in range(n_steps - 1):
        action = np.random.choice([0, 1, 2])  # Random action
        obs, reward, done, info = env.step(action)
        total_reward += reward
        
        if done:
            break
    
    summary = env.get_summary()
    print(f"\n📊 Episode Summary:")
    print(f"   Total Return: {summary['total_return']:.2f}%")
    print(f"   Total Trades: {summary['total_trades']}")
    print(f"   Total Reward: {summary['total_reward']:.2f}")
    print("✅ Trading Environment test passed!")
