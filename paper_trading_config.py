"""
Paper Trading Configuration
----------------------------
Configuration settings for paper (demo) trading mode.
Set PAPER_TRADING_MODE = True to trade with virtual money.
"""

from pathlib import Path


class PaperTradingConfig:
    """Configuration for paper trading system."""
    
    # ========================================
    # Enable/Disable Paper Trading
    # ========================================
    PAPER_TRADING_MODE = True  # Set to False for live trading with real money
    
    # ========================================
    # Virtual Account Settings
    # ========================================
    INITIAL_VIRTUAL_CAPITAL = 100000.0  # Rs 1,00,000 starting capital
    VIRTUAL_BALANCE_FILE = Path(__file__).parent / 'data' / 'paper_trading_balance.json'
    
    # ========================================
    # Simulated Execution Settings
    # ========================================
    SIMULATE_SLIPPAGE = True  # Add realistic slippage to orders
    SLIPPAGE_PERCENT = 0.05  # 0.05% slippage on execution
    SIMULATE_DELAY = True  # Add execution delay
    EXECUTION_DELAY_MS = 500  # 500ms delay to simulate real execution
    
    # ========================================
    # Risk Management (Paper Trading)
    # ========================================
    MAX_POSITION_SIZE_PCT = 10.0  # Max 10% of capital per position
    MAX_DAILY_LOSS_PCT = 5.0  # Stop trading if daily loss exceeds 5%
    MAX_OPEN_POSITIONS = 5  # Maximum 5 concurrent positions

    # thresholds for automatic exits (expressed as fraction of entry price)
    PROFIT_TARGET_PCT = 0.01    # 1% gain before booking profit
    STOP_LOSS_PCT   = 0.01    # 1% loss before cutting position (set 0 to exit immediately on any loss)
    
    # ========================================
    # Logging Settings
    # ========================================
    LOG_PAPER_TRADES = True  # Log paper trades to database
    PAPER_TRADE_PREFIX = '[PAPER]'  # Prefix for console logs
    
    # ========================================
    # Performance Tracking
    # ========================================
    TRACK_PERFORMANCE = True  # Track win rate, profit factor, etc.
    PERFORMANCE_WINDOW = 50  # Number of trades to track
    
    @classmethod
    def get_mode_display(cls) -> str:
        """Get human-readable trading mode."""
        if cls.PAPER_TRADING_MODE:
            return "PAPER TRADING (Virtual Money)"
        else:
            return "LIVE TRADING (Real Money)"
    
    @classmethod
    def get_config_summary(cls) -> str:
        """Get configuration summary."""
        return f"""
Paper Trading Configuration:
============================
Mode: {cls.get_mode_display()}
Virtual Capital: Rs {cls.INITIAL_VIRTUAL_CAPITAL:,.2f}
Slippage Simulation: {'Enabled' if cls.SIMULATE_SLIPPAGE else 'Disabled'} ({cls.SLIPPAGE_PERCENT}%)
Execution Delay: {'Enabled' if cls.SIMULATE_DELAY else 'Disabled'} ({cls.EXECUTION_DELAY_MS}ms)

Risk Limits:
- Max Position Size: {cls.MAX_POSITION_SIZE_PCT}%
- Max Daily Loss: {cls.MAX_DAILY_LOSS_PCT}%
- Max Open Positions: {cls.MAX_OPEN_POSITIONS}

Balance File: {cls.VIRTUAL_BALANCE_FILE}
"""


if __name__ == "__main__":
    print(PaperTradingConfig.get_config_summary())
