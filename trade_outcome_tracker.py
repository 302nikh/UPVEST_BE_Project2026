"""
Trade Outcome Tracker
---------------------
Tracks trade outcomes and calculates rewards for RL agent learning.
Manages open positions and converts P&L to normalized rewards.
"""

import numpy as np
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, field


@dataclass
class TradeEntry:
    """Represents an open trade position."""
    symbol: str
    action: int  # 0=HOLD, 1=BUY, 2=SELL
    state: np.ndarray  # Market state at entry
    entry_price: float
    quantity: int
    entry_time: datetime
    trade_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            'symbol': self.symbol,
            'action': self.action,
            'state': self.state.tolist() if isinstance(self.state, np.ndarray) else self.state,
            'entry_price': self.entry_price,
            'quantity': self.quantity,
            'entry_time': self.entry_time.isoformat(),
            'trade_id': self.trade_id
        }


class TradeOutcomeTracker:
    """
    Tracks trade outcomes and calculates rewards for RL agent.
    
    Manages:
    - Open positions and their entry states
    - Reward calculation from P&L
    - Experience generation for RL training
    """
    
    def __init__(
        self,
        profit_reward_scale: float = 100.0,
        hold_time_penalty_threshold: int = 5,  # days
        max_hold_time_penalty: float = 0.5
    ):
        """
        Initialize trade outcome tracker.
        
        Args:
            profit_reward_scale: Scale factor for profit-based rewards
            hold_time_penalty_threshold: Days before applying hold penalty
            max_hold_time_penalty: Maximum penalty for holding too long
        """
        self.profit_reward_scale = profit_reward_scale
        self.hold_time_penalty_threshold = hold_time_penalty_threshold
        self.max_hold_time_penalty = max_hold_time_penalty
        
        # Track open positions by symbol
        self.open_positions: Dict[str, TradeEntry] = {}
        
        # Track completed trades for analysis
        self.completed_trades: List[Dict] = []
        
        # Statistics
        self.total_trades = 0
        self.profitable_trades = 0
        self.total_profit = 0.0
    
    def record_trade_entry(
        self,
        symbol: str,
        action: int,
        state: np.ndarray,
        price: float,
        quantity: int,
        trade_id: Optional[str] = None
    ) -> bool:
        """
        Record a trade entry (BUY action).
        
        Args:
            symbol: Stock symbol
            action: Action taken (1=BUY)
            state: Market state vector at entry
            price: Entry price
            quantity: Number of shares
            trade_id: Optional trade ID from database
            
        Returns:
            True if recorded successfully
        """
        if action != 1:  # Only track BUY entries
            return False
        
        # Check if already have open position
        if symbol in self.open_positions:
            print(f"⚠️ Already have open position for {symbol}, skipping entry")
            return False
        
        entry = TradeEntry(
            symbol=symbol,
            action=action,
            state=state,
            entry_price=price,
            quantity=quantity,
            entry_time=datetime.now(),
            trade_id=trade_id
        )
        
        self.open_positions[symbol] = entry
        print(f"📝 Tracked entry: {symbol} @ ₹{price:.2f} x {quantity}")
        return True
    
    def record_trade_exit(
        self,
        symbol: str,
        exit_price: float,
        exit_time: Optional[datetime] = None
    ) -> Optional[Dict]:
        """
        Record a trade exit (SELL action) and calculate reward.
        
        Args:
            symbol: Stock symbol
            exit_price: Exit price
            exit_time: Exit timestamp (default: now)
            
        Returns:
            Experience dict with state, action, reward, next_state, done
            None if no open position found
        """
        if symbol not in self.open_positions:
            print(f"⚠️ No open position found for {symbol}")
            return None
        
        entry = self.open_positions[symbol]
        exit_time = exit_time or datetime.now()
        
        # Calculate holding time
        holding_time = (exit_time - entry.entry_time).total_seconds() / 86400  # days
        
        # Calculate reward
        reward = self.calculate_reward(
            entry_price=entry.entry_price,
            exit_price=exit_price,
            holding_time=holding_time,
            quantity=entry.quantity
        )
        
        # Calculate profit
        profit = (exit_price - entry.entry_price) * entry.quantity
        profit_pct = (exit_price - entry.entry_price) / entry.entry_price * 100
        
        # Update statistics
        self.total_trades += 1
        self.total_profit += profit
        if profit > 0:
            self.profitable_trades += 1
        
        # Create experience for RL
        experience = {
            'symbol': symbol,
            'state': entry.state,
            'action': entry.action,
            'reward': reward,
            'next_state': None,  # Will be filled by caller
            'done': True,
            'entry_price': entry.entry_price,
            'exit_price': exit_price,
            'profit': profit,
            'profit_pct': profit_pct,
            'holding_time': holding_time,
            'quantity': entry.quantity,
            'trade_id': entry.trade_id
        }
        
        # Store completed trade
        self.completed_trades.append(experience)
        
        # Remove from open positions
        del self.open_positions[symbol]
        
        print(f"✅ Tracked exit: {symbol} @ ₹{exit_price:.2f} | "
              f"P&L: ₹{profit:.2f} ({profit_pct:+.2f}%) | "
              f"Reward: {reward:.2f}")
        
        return experience
    
    def calculate_reward(
        self,
        entry_price: float,
        exit_price: float,
        holding_time: float,
        quantity: int = 1
    ) -> float:
        """
        Calculate reward from trade outcome.
        
        Reward components:
        1. Profit percentage (main component)
        2. Bonus for profitable trades
        3. Penalty for holding too long
        
        Args:
            entry_price: Entry price
            exit_price: Exit price
            holding_time: Holding time in days
            quantity: Number of shares
            
        Returns:
            Normalized reward value
        """
        # 1. Profit-based reward (percentage return)
        profit_pct = (exit_price - entry_price) / entry_price
        reward = profit_pct * self.profit_reward_scale
        
        # 2. Bonus for profitable trades
        if profit_pct > 0:
            reward += 0.5
        
        # 3. Penalty for holding too long (encourages timely exits)
        if holding_time > self.hold_time_penalty_threshold:
            excess_days = holding_time - self.hold_time_penalty_threshold
            penalty = min(excess_days * 0.1, self.max_hold_time_penalty)
            reward -= penalty
        
        return reward
    
    def get_open_position(self, symbol: str) -> Optional[TradeEntry]:
        """Get open position for a symbol."""
        return self.open_positions.get(symbol)
    
    def has_open_position(self, symbol: str) -> bool:
        """Check if there's an open position for a symbol."""
        return symbol in self.open_positions
    
    def get_statistics(self) -> Dict:
        """Get trading statistics."""
        win_rate = (self.profitable_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        avg_profit = self.total_profit / self.total_trades if self.total_trades > 0 else 0
        
        return {
            'total_trades': self.total_trades,
            'profitable_trades': self.profitable_trades,
            'losing_trades': self.total_trades - self.profitable_trades,
            'win_rate': win_rate,
            'total_profit': self.total_profit,
            'avg_profit': avg_profit,
            'open_positions': len(self.open_positions)
        }
    
    def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """Get recent completed trades."""
        return self.completed_trades[-limit:]
    
    def clear_statistics(self):
        """Clear statistics (useful for testing)."""
        self.total_trades = 0
        self.profitable_trades = 0
        self.total_profit = 0.0
        self.completed_trades = []


if __name__ == "__main__":
    print("🧪 Testing Trade Outcome Tracker...\n")
    
    tracker = TradeOutcomeTracker()
    
    # Test 1: Record profitable trade
    print("Test 1: Profitable Trade")
    state = np.random.randn(10)
    tracker.record_trade_entry('TCS', action=1, state=state, price=3500, quantity=10)
    
    # Simulate exit after 2 days with profit
    experience = tracker.record_trade_exit('TCS', exit_price=3600)
    print(f"   Reward: {experience['reward']:.2f}")
    print(f"   Profit: ₹{experience['profit']:.2f}\n")
    
    # Test 2: Record losing trade
    print("Test 2: Losing Trade")
    state = np.random.randn(10)
    tracker.record_trade_entry('INFY', action=1, state=state, price=1500, quantity=5)
    
    experience = tracker.record_trade_exit('INFY', exit_price=1450)
    print(f"   Reward: {experience['reward']:.2f}")
    print(f"   Profit: ₹{experience['profit']:.2f}\n")
    
    # Test 3: Statistics
    print("Test 3: Statistics")
    stats = tracker.get_statistics()
    print(f"   Total Trades: {stats['total_trades']}")
    print(f"   Win Rate: {stats['win_rate']:.1f}%")
    print(f"   Total Profit: ₹{stats['total_profit']:.2f}\n")
    
    print("✅ Trade Outcome Tracker tests passed!")
