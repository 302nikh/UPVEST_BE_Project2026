"""
Trailing Stop-Loss Manager
===========================
Automatically moves stop-loss prices up as positions become profitable,
locking in gains while allowing upside to continue.

Author: UPVEST Team
"""

class TrailingStopManager:
    """
    Manages trailing stop-loss for all open positions.
    
    How it works:
    1. Waits for position to become profitable by trigger_percent
    2. Once triggered, tracks the peak price
    3. Sets stop-loss at trail_percent below the peak
    4. As price rises, stop moves up (never down)
    5. If price falls to stop level, signals to sell
    """
    
    def __init__(self, trail_percent=0.02, trigger_percent=0.03):
        """
        Initialize trailing stop manager.
        
        Args:
            trail_percent: Distance below peak to set stop (default 2%)
            trigger_percent: Minimum profit before activating trail (default 3%)
        
        Example:
            If stock bought at Rs 100:
            - Waits until Rs 103 (3% profit) to activate
            - If price hits Rs 110, sets stop at Rs 107.80 (2% below)
            - If price rises to Rs 115, stop moves to Rs 112.70
            - If price drops to Rs 112.70, triggers SELL
        """
        self.trail_percent = trail_percent
        self.trigger_percent = trigger_percent
        
        # Track peak prices for each symbol
        self.peak_prices = {}  # symbol -> highest_price_seen
        
        # Track current stop prices
        self.stop_prices = {}  # symbol -> current_stop_price
        
        # Track if trailing is active
        self.active = {}  # symbol -> True/False
        
    def update(self, symbol, current_price, entry_price):
        """
        Update trailing stop for a position.
        
        Args:
            symbol: Stock symbol
            current_price: Current market price
            entry_price: Price at which position was entered
            
        Returns:
            dict with status info or None if not activated yet
        """
        # Calculate current profit percentage
        profit_pct = (current_price - entry_price) / entry_price
        
        # Check if profitable enough to activate trailing
        if profit_pct < self.trigger_percent:
            # Not profitable enough yet, don't activate
            return None
        
        # Mark as active
        if symbol not in self.active:
            self.active[symbol] = True
            self.peak_prices[symbol] = current_price
            print(f"   [SHIELD] Trailing stop ACTIVATED for {symbol} at INR {current_price:,.2f}")
        
        # Update peak price if current is higher
        if current_price > self.peak_prices.get(symbol, 0):
            self.peak_prices[symbol] = current_price
        
        # Calculate stop price (trail_percent below peak)
        peak = self.peak_prices[symbol]
        new_stop = peak * (1 - self.trail_percent)
        
        # Only update stop if it's higher than before (never move down)
        old_stop = self.stop_prices.get(symbol, 0)
        if new_stop > old_stop:
            self.stop_prices[symbol] = new_stop
            
        return {
            'active': True,
            'entry_price': entry_price,
            'current_price': current_price,
            'peak_price': peak,
            'stop_price': self.stop_prices[symbol],
            'profit_pct': profit_pct * 100,
            'locked_profit_pct': ((self.stop_prices[symbol] - entry_price) / entry_price) * 100
        }
    
    def check_stop_hit(self, symbol, current_price):
        """
        Check if current price has hit the trailing stop.
        
        Args:
            symbol: Stock symbol
            current_price: Current market price
            
        Returns:
            (stop_hit, stop_price) tuple
            - stop_hit: True if stop was hit, False otherwise
            - stop_price: The stop price that was hit, or None
        """
        if symbol not in self.stop_prices:
            return False, None
        
        stop_price = self.stop_prices[symbol]
        
        # Check if current price dropped to or below stop
        if current_price <= stop_price:
            return True, stop_price
        
        return False, None
    
    def get_stop_info(self, symbol):
        """
        Get current stop information for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            dict with stop info or None if not active
        """
        if symbol not in self.active or not self.active[symbol]:
            return None
        
        return {
            'stop_price': self.stop_prices.get(symbol),
            'peak_price': self.peak_prices.get(symbol),
            'active': True
        }
    
    def clear(self, symbol):
        """
        Remove trailing stop after position is closed.
        
        Args:
            symbol: Stock symbol
        """
        self.peak_prices.pop(symbol, None)
        self.stop_prices.pop(symbol, None)
        self.active.pop(symbol, None)
    
    def clear_all(self):
        """Clear all trailing stops (e.g., end of day)."""
        self.peak_prices.clear()
        self.stop_prices.clear()
        self.active.clear()
    
    def get_all_active(self):
        """
        Get all symbols with active trailing stops.
        
        Returns:
            list of symbols
        """
        return [symbol for symbol, active in self.active.items() if active]
    
    def display_status(self, symbol, current_price, entry_price):
        """
        Display trailing stop status for debugging.
        
        Args:
            symbol: Stock symbol
            current_price: Current price
            entry_price: Entry price
        """
        info = self.update(symbol, current_price, entry_price)
        
        if info is None:
            profit_pct = ((current_price - entry_price) / entry_price) * 100
            trigger_needed = self.trigger_percent * 100
            print(f"   [INFO] Trailing stop not active yet (Profit: {profit_pct:.2f}%, Need: {trigger_needed:.1f}%)")
        else:
            print(f"   [SHIELD] Trailing Stop Status:")
            print(f"            Peak: INR {info['peak_price']:,.2f}")
            print(f"            Stop: INR {info['stop_price']:,.2f}")
            print(f"            Current Profit: {info['profit_pct']:.2f}%")
            print(f"            Locked Profit: {info['locked_profit_pct']:.2f}%")


# Example usage
if __name__ == "__main__":
    # Create manager with 2% trail, 3% trigger
    manager = TrailingStopManager(trail_percent=0.02, trigger_percent=0.03)
    
    # Simulate a profitable trade
    symbol = "NIFTY 50"
    entry = 22000
    
    prices = [22000, 22100, 22200, 22300, 22500, 22700, 22650, 22600]
    
    print(f"\\nSimulating trade for {symbol} entered at INR {entry:,.2f}\\n")
    
    for price in prices:
        print(f"\\nPrice: INR {price:,.2f}")
        info = manager.update(symbol, price, entry)
        
        if info:
            manager.display_status(symbol, price, entry)
            
            # Check if stop hit
            hit, stop_price = manager.check_stop_hit(symbol, price)
            if hit:
                print(f"   [ALERT] STOP HIT! Sell at INR {price:,.2f} (Stop was INR {stop_price:,.2f})")
                break
        else:
            profit = ((price - entry) / entry) * 100
            print(f"   [INFO] Profit: {profit:.2f}% (Trailing not active yet)")
