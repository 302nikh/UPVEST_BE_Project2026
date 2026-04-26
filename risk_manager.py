"""
Risk Management System
=======================
Comprehensive risk controls to protect capital in live trading.

Risk Limits:
- Position sizing
- Daily loss limits
- Drawdown protection
- Trade frequency controls

Usage:
    risk_mgr = RiskManager(initial_capital =100000)
    
    # Before placing trade
    can_trade, reason = risk_mgr.validate_trade(
        symbol="RELIANCE",
        side="BUY",
        quantity=10,
        price=2450.50,
        current_portfolio_value=105000
    )
    
    if not can_trade:
        print(f"Trade blocked: {reason}")
"""

from datetime import datetime, time, date, timedelta
from typing import Tuple, Dict, Optional
import json
from pathlib import Path


class RiskManager:
    """Manages all risk controls for live trading."""
    
    def __init__(
        self,
        initial_capital: float = 100000,
        max_position_size_pct: float = 0.20,  # 20% max per stock
        max_open_positions: int = 5,
        daily_loss_limit_pct: float = 0.05,  # 5% daily loss limit
        max_drawdown_pct: float = 0.10,  # 10% max drawdown from peak
        min_trade_interval_seconds: int = 60,
        max_trades_per_day: int = 20,
        stop_loss_pct: float = 0.02  # 2% stop loss
    ):
        """
        Initialize risk manager.
        
        Args:
            initial_capital: Starting capital
            max_position_size_pct: Max % of capital per position
            max_open_positions: Max number of concurrent positions
            daily_loss_limit_pct: Max loss % per day (circuit breaker)
            max_drawdown_pct: Max drawdown from peak before pause
            min_trade_interval_seconds: Minimum time between trades
            max_trades_per_day: Maximum trades allowed per day
            stop_loss_pct: Default stop loss percentage
        """
        self.initial_capital = initial_capital
        self.max_position_size_pct = max_position_size_pct
        self.max_open_positions = max_open_positions
        self.daily_loss_limit_pct = daily_loss_limit_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.min_trade_interval_seconds = min_trade_interval_seconds
        self.max_trades_per_day = max_trades_per_day
        self.stop_loss_pct = stop_loss_pct
        
        # Track state
        self.peak_portfolio_value = initial_capital
        self.last_trade_time = None
        self.trades_today = 0
        self.today_date = date.today()
        
        # State file
        self.state_file = Path("data/risk_manager_state.json")
        self.load_state()
    
    def load_state(self):
        """Load risk manager state from file."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                
                self.peak_portfolio_value = state.get('peak_portfolio_value', self.initial_capital)
                self.trades_today = state.get('trades_today', 0)
                
                loaded_date = date.fromisoformat(state.get('today_date', date.today().isoformat()))
                if loaded_date != date.today():
                    # New day, reset daily counters
                    self.trades_today = 0
                    self.today_date = date.today()
                
                last_trade_str = state.get('last_trade_time')
                if last_trade_str:
                    self.last_trade_time = datetime.fromisoformat(last_trade_str)
                    
                print(f"[RISK] Loaded state: Peak={self.peak_portfolio_value:,.2f}, Trades today={self.trades_today}")
        except Exception as e:
            print(f"[RISK WARN] Could not load state: {e}")
    
    def save_state(self):
        """Save risk manager state to file."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            state = {
                'peak_portfolio_value': self.peak_portfolio_value,
                'trades_today': self.trades_today,
                'today_date': self.today_date.isoformat(),
                'last_trade_time': self.last_trade_time.isoformat() if self.last_trade_time else None
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"[RISK ERROR] Could not save state: {e}")
    
    def is_market_hours(self) -> Tuple[bool, str]:
        """Check if current time is within trading hours."""
        now = datetime.now().time()
        
        # Market hours: 9:15 AM - 3:30 PM
        market_open = time(9, 15)
        market_close = time(15, 30)
        
        # No trading in first/last 15 minutes
        safe_open = time(9, 30)
        safe_close = time(15, 15)
        
        if now < market_open or now > market_close:
            return False, "Market is closed (9:15 AM - 3:30 PM)"
        
        if now < safe_open:
            return False, "No trading in first 15 minutes of market"
        
        if now > safe_close:
            return False, "No trading in last 15 minutes of market"
        
        return True, "Market hours OK"
    
    def check_position_size(
        self,
        position_value: float,
        current_portfolio_value: float
    ) -> Tuple[bool, str]:
        """Check if position size is within limits."""
        position_pct = (position_value / current_portfolio_value) * 100
        
        if position_pct > (self.max_position_size_pct * 100):
            return False, f"Position size {position_pct:.1f}% exceeds limit {self.max_position_size_pct*100:.1f}%"
        
        return True, "Position size OK"
    
    def check_open_positions(self, current_positions: int) -> Tuple[bool, str]:
        """Check if we can open another position."""
        if current_positions >= self.max_open_positions:
            return False, f"Max open positions ({self.max_open_positions}) reached"
        
        return True, "Open positions OK"
    
    def check_daily_loss_limit(
        self,
        current_portfolio_value: float
    ) -> Tuple[bool, str]:
        """Check daily loss circuit breaker."""
        # Calculate today's P&L
        today_start_value = self.initial_capital  # Could track this better
        current_loss = today_start_value - current_portfolio_value
        loss_pct = (current_loss / today_start_value) * 100
        
        if loss_pct >= (self.daily_loss_limit_pct * 100):
            return False, f"Daily loss limit {self.daily_loss_limit_pct*100:.1f}% reached (current: {loss_pct:.1f}%)"
        
        return True, "Daily loss limit OK"
    
    def check_drawdown(
        self,
        current_portfolio_value: float
    ) -> Tuple[bool, str]:
        """Check max drawdown from peak."""
        # Update peak if necessary
        if current_portfolio_value > self.peak_portfolio_value:
            self.peak_portfolio_value = current_portfolio_value
            self.save_state()
        
        drawdown = (self.peak_portfolio_value - current_portfolio_value) / self.peak_portfolio_value
        
        if drawdown >= self.max_drawdown_pct:
            return False, f"Max drawdown {self.max_drawdown_pct*100:.1f}% exceeded (current: {drawdown*100:.1f}%)"
        
        return True, "Drawdown OK"
    
    def check_trade_frequency(self) -> Tuple[bool, str]:
        """Check minimum interval between trades."""
        if self.last_trade_time:
            time_since_last = (datetime.now() - self.last_trade_time).total_seconds()
            if time_since_last < self.min_trade_interval_seconds:
               return False, f"Min {self.min_trade_interval_seconds}s between trades (last trade {time_since_last:.0f}s ago)"
        
        return True, "Trade frequency OK"
    
    def check_daily_trade_limit(self) -> Tuple[bool, str]:
        """Check max trades per day."""
        # Reset if new day
        if date.today() != self.today_date:
            self.trades_today = 0
            self.today_date = date.today()
            self.save_state()
        
        if self.trades_today >= self.max_trades_per_day:
            return False, f"Daily trade limit ({self.max_trades_per_day}) reached"
        
        return True, "Daily trade count OK"
    
    def validate_trade(
        self,
        symbol: str,
        side: str,
        quantity: int,
        price: float,
        current_portfolio_value: float,
        current_open_positions: int = 0
    ) -> Tuple[bool, str]:
        """
        Validate if trade is allowed under all risk controls.
        
        Returns:
            (can_trade, reason)
        """
        # 1. Market hours
        can_trade, reason = self.is_market_hours()
        if not can_trade:
            return False, f"⏰ {reason}"
        
        # 2. Trade frequency
        can_trade, reason = self.check_trade_frequency()
        if not can_trade:
            return False, f"⏱️ {reason}"
        
        # 3. Daily trade limit
        can_trade, reason = self.check_daily_trade_limit()
        if not can_trade:
            return False, f"🔢 {reason}"
        
        # 4. Position size (for BUY orders)
        if side == "BUY":
            position_value = quantity * price
            can_trade, reason = self.check_position_size(position_value, current_portfolio_value)
            if not can_trade:
                return False, f"📊 {reason}"
            
            # 5. Open positions limit
            can_trade, reason = self.check_open_positions(current_open_positions)
            if not can_trade:
                return False, f"📈 {reason}"
        
        # 6. Daily loss limit
        can_trade, reason = self.check_daily_loss_limit(current_portfolio_value)
        if not can_trade:
            return False, f"🚨 CIRCUIT BREAKER: {reason}"
        
        # 7. Max drawdown
        can_trade, reason = self.check_drawdown(current_portfolio_value)
        if not can_trade:
            return False, f"📉 DRAWDOWN LIMIT: {reason}"
        
        return True, "All risk checks passed ✅"
    
    def record_trade(self):
        """Record that a trade was executed."""
        self.last_trade_time = datetime.now()
        self.trades_today += 1
        self.save_state()
        print(f"[RISK] Trade recorded. Total today: {self.trades_today}/{self.max_trades_per_day}")
    
    def calculate_position_size(
        self,
        price: float,
        available_capital: float,
        use_max: bool = False
    ) -> int:
        """
        Calculate safe position size.
        
        Args:
            price: Current stock price
            available_capital: Cash available
            use_max: If True, use max allowed %, else use conservative 10%
        
        Returns:
            Quantity to buy
        """
        if use_max:
            target_pct = self.max_position_size_pct
        else:
            target_pct = 0.10  # Conservative 10%
        
        target_value = available_capital * target_pct
        quantity = int(target_value / price)
        
        return max(1, quantity)  # At least 1 share
    
    def get_stop_loss_price(self, entry_price: float, side: str) -> float:
        """Calculate stop loss price for a position."""
        if side == "BUY":
            # Stop loss below entry
            return entry_price * (1 - self.stop_loss_pct)
        else:
            # Stop loss above entry (for short positions)
            return entry_price * (1 + self.stop_loss_pct)
    
    def get_status(self) -> Dict:
        """Get current risk manager status."""
        return {
            'peak_portfolio_value': self.peak_portfolio_value,
            'trades_today': self.trades_today,
            'max_trades_per_day': self.max_trades_per_day,
            'last_trade_time': self.last_trade_time.isoformat() if self.last_trade_time else None,
            'limits': {
                'max_position_size_pct': self.max_position_size_pct * 100,
                'max_open_positions': self.max_open_positions,
                'daily_loss_limit_pct': self.daily_loss_limit_pct * 100,
                'max_drawdown_pct': self.max_drawdown_pct * 100,
                'min_trade_interval_seconds': self.min_trade_interval_seconds,
                'stop_loss_pct': self.stop_loss_pct * 100
            }
        }


if __name__ == "__main__":
    # Test risk manager
    print("="*50)
    print("Risk Manager Test")
    print("="*50)
    
    risk_mgr = RiskManager(initial_capital=100000)
    
    # Test trade validation
    can_trade, reason = risk_mgr.validate_trade(
        symbol="RELIANCE",
        side="BUY",
        quantity=40,
        price=2450.50,
        current_portfolio_value=100000,
        current_open_positions=2
    )
    
    print(f"\nTrade Validation: {can_trade}")
    print(f"Reason: {reason}")
    
    if can_trade:
        risk_mgr.record_trade()
    
    # Test position sizing
    qty = risk_mgr.calculate_position_size(price=2450.50, available_capital=100000)
    print(f"\nRecommended position size: {qty} shares")
    
    # Test stop loss
    stop_price = risk_mgr.get_stop_loss_price(entry_price=2450.50, side="BUY")
    print(f"Stop loss price: ₹{stop_price:.2f}")
    
    # Show status
    print("\nRisk Manager Status:")
    print(json.dumps(risk_mgr.get_status(), indent=2))
