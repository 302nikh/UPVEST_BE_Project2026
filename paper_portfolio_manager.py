"""
Paper Portfolio Manager
-----------------------
Manages virtual portfolio for paper trading mode.
Tracks positions, cash balance, and trade history.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class PaperPortfolioManager:
    """Manages virtual portfolio for paper trading."""
    
    def __init__(self, initial_capital: float = 100000.0, balance_file: Optional[Path] = None):
        """
        Initialize paper portfolio manager.
        
        Args:
            initial_capital: Starting virtual capital
            balance_file: Path to save portfolio state
        """
        self.initial_capital = initial_capital
        self.balance_file = balance_file or Path('data/paper_trading_balance.json')
        
        # Portfolio state
        self.cash = initial_capital
        self.positions = {}  # {symbol: {qty, avg_price, current_price, stock_name}}
        self.trade_history = []
        
        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0.0
        self.total_loss = 0.0
        
        # Load existing portfolio if available
        self.load_portfolio()
    
    def load_portfolio(self):
        """Load portfolio from file if exists."""
        if self.balance_file.exists():
            try:
                with open(self.balance_file, 'r') as f:
                    data = json.load(f)
                    self.cash = data.get('cash', self.initial_capital)
                    self.positions = data.get('positions', {})
                    self.trade_history = data.get('trade_history', [])
                    self.total_trades = data.get('total_trades', 0)
                    self.winning_trades = data.get('winning_trades', 0)
                    self.losing_trades = data.get('losing_trades', 0)
                    self.total_profit = data.get('total_profit', 0.0)
                    self.total_loss = data.get('total_loss', 0.0)
                print(f"[PAPER] Loaded portfolio from {self.balance_file}")
            except Exception as e:
                print(f"[PAPER] Error loading portfolio: {e}")
                self.reset_portfolio()
        else:
            print(f"[PAPER] No existing portfolio found. Starting fresh.")
            self.save_portfolio()
    
    def save_portfolio(self):
        """Save portfolio to file."""
        try:
            self.balance_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.balance_file, 'w') as f:
                json.dump({
                    'cash': self.cash,
                    'positions': self.positions,
                    'trade_history': self.trade_history,
                    'total_trades': self.total_trades,
                    'winning_trades': self.winning_trades,
                    'losing_trades': self.losing_trades,
                    'total_profit': self.total_profit,
                    'total_loss': self.total_loss,
                    'initial_capital': self.initial_capital,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"[PAPER] Error saving portfolio: {e}")
    
    def reset_portfolio(self):
        """Reset portfolio to initial state."""
        self.cash = self.initial_capital
        self.positions = {}
        self.trade_history = []
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0.0
        self.total_loss = 0.0
        self.save_portfolio()
        print(f"[PAPER] Portfolio reset to Rs {self.initial_capital:,.2f}")
    
    def execute_buy(self, symbol: str, qty: int, price: float, stock_name: str = "") -> Tuple[bool, str]:
        """
        Execute virtual BUY order.
        
        Args:
            symbol: Stock symbol
            qty: Quantity to buy
            price: Execution price
            stock_name: Display name
            
        Returns:
            (success, message)
        """
        cost = qty * price
        
        # Check if sufficient funds
        if cost > self.cash:
            return False, f"Insufficient virtual funds. Need Rs {cost:,.2f}, have Rs {self.cash:,.2f}"
        
        # Deduct cash
        self.cash -= cost
        
        # Update position
        if symbol in self.positions:
            # Average down/up
            old_qty = self.positions[symbol]['qty']
            old_price = self.positions[symbol]['avg_price']
            new_avg = ((old_qty * old_price) + (qty * price)) / (old_qty + qty)
            self.positions[symbol]['qty'] += qty
            self.positions[symbol]['avg_price'] = new_avg
            self.positions[symbol]['current_price'] = price
        else:
            self.positions[symbol] = {
                'qty': qty,
                'avg_price': price,
                'current_price': price,
                'stock_name': stock_name or symbol.split('|')[0]
            }
        
        # Record trade
        self.trade_history.append({
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'stock_name': stock_name,
            'side': 'BUY',
            'qty': qty,
            'price': price,
            'cost': cost,
            'balance_after': self.cash
        })
        
        self.save_portfolio()
        return True, f"Paper BUY executed: {qty} @ Rs {price:.2f} (Cost: Rs {cost:,.2f})"
    
    def execute_sell(self, symbol: str, qty: int, price: float, stock_name: str = "") -> Tuple[bool, str]:
        """
        Execute virtual SELL order.
        
        Args:
            symbol: Stock symbol
            qty: Quantity to sell
            price: Execution price
            stock_name: Display name
            
        Returns:
            (success, message)
        """
        # Check if position exists
        if symbol not in self.positions:
            return False, f"No position in {symbol} to sell"
        
        # Check if sufficient quantity
        if self.positions[symbol]['qty'] < qty:
            available = self.positions[symbol]['qty']
            return False, f"Insufficient quantity. Want to sell {qty}, have {available}"
        
        # Calculate P&L
        avg_price = self.positions[symbol]['avg_price']
        proceeds = qty * price
        cost_basis = qty * avg_price
        pnl = proceeds - cost_basis
        
        # Update cash
        self.cash += proceeds
        
        # Update position
        self.positions[symbol]['qty'] -= qty
        self.positions[symbol]['current_price'] = price
        
        # Remove position if fully closed
        if self.positions[symbol]['qty'] == 0:
            del self.positions[symbol]
        
        # Update performance tracking
        self.total_trades += 1
        if pnl > 0:
            self.winning_trades += 1
            self.total_profit += pnl
        else:
            self.losing_trades += 1
            self.total_loss += abs(pnl)
        
        # Record trade
        self.trade_history.append({
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'stock_name': stock_name,
            'side': 'SELL',
            'qty': qty,
            'price': price,
            'proceeds': proceeds,
            'pnl': pnl,
            'balance_after': self.cash
        })
        
        self.save_portfolio()
        pnl_str = f"+Rs {pnl:.2f}" if pnl >= 0 else f"-Rs {abs(pnl):.2f}"
        return True, f"Paper SELL executed: {qty} @ Rs {price:.2f} (P&L: {pnl_str})"
    
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """
        Calculate total portfolio value.
        
        Args:
            current_prices: {symbol: current_price}
            
        Returns:
            Total portfolio value
        """
        position_value = 0.0
        for symbol, pos in self.positions.items():
            current_price = current_prices.get(symbol, pos['current_price'])
            position_value += pos['qty'] * current_price
        
        return self.cash + position_value
    
    def get_pnl(self, current_prices: Dict[str, float]) -> float:
        """
        Calculate total P&L.
        
        Args:
            current_prices: {symbol: current_price}
            
        Returns:
            Total P&L
        """
        current_value = self.get_portfolio_value(current_prices)
        return current_value - self.initial_capital
    
    def get_statistics(self) -> Dict:
        """Get performance statistics."""
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        profit_factor = (self.total_profit / self.total_loss) if self.total_loss > 0 else 0
        
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'total_profit': self.total_profit,
            'total_loss': self.total_loss,
            'total_pnl': self.total_profit - self.total_loss,
            'profit_factor': profit_factor,
            'open_positions': len(self.positions),
            'cash': self.cash
        }
    
    def get_position_pnl(self, symbol: str, current_price: float) -> float:
        """Get unrealized P&L for a position."""
        if symbol not in self.positions:
            return 0.0
        
        pos = self.positions[symbol]
        return (current_price - pos['avg_price']) * pos['qty']


if __name__ == "__main__":
    # Test the portfolio manager
    portfolio = PaperPortfolioManager(initial_capital=100000.0)
    print(f"Initial Balance: Rs {portfolio.cash:,.2f}")
    
    # Test buy
    success, msg = portfolio.execute_buy("NSE_INDEX|Nifty 50", 10, 22000.0, "NIFTY50")
    print(msg)
    
    # Test sell
    success, msg = portfolio.execute_sell("NSE_INDEX|Nifty 50", 5, 22100.0, "NIFTY50")
    print(msg)
    
    # Get stats
    stats = portfolio.get_statistics()
    print(f"\nStatistics:")
    print(f"Win Rate: {stats['win_rate']:.1f}%")
    print(f"Total Profit: Rs {stats['total_profit']:.2f}")
