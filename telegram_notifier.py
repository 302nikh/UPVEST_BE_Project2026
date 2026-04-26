"""
Telegram Notification Module
=============================
Sends trading notifications to Telegram for key events:
- Trade Started
- Trade Ended  
- Overall P&L
- Market Closed
- Out of Time
"""

import os
import json
import requests
from datetime import datetime
from typing import Optional


class TelegramNotifier:
    """
    Handles Telegram notifications for trading events.
    
    Setup:
    1. Create a Telegram bot via @BotFather
    2. Get your chat_id by messaging the bot and visiting:
       https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
    3. Store credentials in telegram_config.json
    """
    
    CONFIG_FILE = "telegram_config.json"
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """
        Initialize the notifier with bot credentials.
        
        Args:
            bot_token: Telegram Bot API token (optional if config file exists)
            chat_id: Your Telegram chat ID (optional if config file exists)
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = False
        
        # Try loading from config if credentials not provided
        if not self.bot_token or not self.chat_id:
            self._load_config()
        
        if self.bot_token and self.chat_id:
            self.enabled = True
            self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        else:
            print("⚠️ Telegram notifications disabled. Configure telegram_config.json to enable.")
    
    def _load_config(self):
        """Load bot credentials from config file."""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.bot_token = config.get('bot_token', '')
                    self.chat_id = config.get('chat_id', '')
            except Exception as e:
                print(f"⚠️ Failed to load Telegram config: {e}")
    
    def _send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Send a message via Telegram Bot API.
        
        Args:
            message: The message text to send
            parse_mode: Message format (HTML or Markdown)
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.enabled:
            return False
            
        try:
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            response = requests.post(self.api_url, json=payload, timeout=10)
            result = response.json()
            
            if result.get("ok"):
                return True
            else:
                print(f"⚠️ Telegram API error: {result.get('description', 'Unknown error')}")
                return False
        except requests.exceptions.Timeout:
            print("⚠️ Telegram notification timeout")
            return False
        except Exception as e:
            print(f"⚠️ Telegram notification failed: {e}")
            return False
    
    # ========== Trading Event Notifications ==========
    
    def notify_trade_started(self, symbol: str, side: str, quantity: int, 
                             price: float, strategy: str = "", confidence: float = 0.0):
        """
        Send notification when a trade is initiated.
        
        Args:
            symbol: Stock symbol
            side: BUY or SELL
            quantity: Number of shares
            price: Trade price
            strategy: Strategy name used
            confidence: AI confidence level
        """
        emoji = "🟢" if side == "BUY" else "🔴"
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        message = (
            f"{emoji} <b>TRADE STARTED</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"📊 <b>Symbol:</b> {symbol}\n"
            f"📈 <b>Action:</b> {side}\n"
            f"🔢 <b>Quantity:</b> {quantity}\n"
            f"💰 <b>Price:</b> ₹{price:.2f}\n"
            f"🎯 <b>Strategy:</b> {strategy}\n"
            f"📊 <b>Confidence:</b> {confidence:.0%}\n"
            f"⏰ <b>Time:</b> {timestamp}"
        )
        
        success = self._send_message(message)
        if success:
            print(f"📱 Trade notification sent: {side} {symbol}")
        return success
    
    def notify_trade_ended(self, symbol: str, side: str, quantity: int,
                           entry_price: float, exit_price: float, pnl: float):
        """
        Send notification when a trade is closed.
        
        Args:
            symbol: Stock symbol
            side: Original side (BUY/SELL)
            quantity: Number of shares
            entry_price: Entry price
            exit_price: Exit price
            pnl: Profit/Loss amount
        """
        is_profit = pnl >= 0
        emoji = "💰" if is_profit else "📉"
        pnl_icon = "+" if is_profit else ""
        pnl_color = "profit" if is_profit else "loss"
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        pct_change = ((exit_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
        pct_icon = "+" if pct_change >= 0 else ""
        
        message = (
            f"{emoji} <b>TRADE ENDED</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"📊 <b>Symbol:</b> {symbol}\n"
            f"📈 <b>Position:</b> {side}\n"
            f"🔢 <b>Quantity:</b> {quantity}\n"
            f"🔹 <b>Entry:</b> ₹{entry_price:.2f}\n"
            f"🔸 <b>Exit:</b> ₹{exit_price:.2f} ({pct_icon}{pct_change:.2f}%)\n"
            f"💵 <b>P&L:</b> {pnl_icon}₹{pnl:.2f}\n"
            f"⏰ <b>Time:</b> {timestamp}"
        )
        
        success = self._send_message(message)
        if success:
            print(f"📱 Trade close notification sent: {symbol} P&L: {pnl_icon}₹{pnl:.2f}")
        return success
    
    def notify_daily_pnl(self, total_pnl: float, trades_count: int, 
                         starting_balance: float, ending_balance: float,
                         open_positions: int = 0, mode: str = "AI-Enhanced"):
        """
        Send daily P&L summary notification.
        
        Args:
            total_pnl: Total profit/loss for the day
            trades_count: Number of trades executed
            starting_balance: Balance at start of day
            ending_balance: Balance at end of day
            open_positions: Number of open positions
            mode: Trading mode (AI-Enhanced/Rule-Based)
        """
        is_profit = total_pnl >= 0
        emoji = "📈" if is_profit else "📉"
        pnl_icon = "+" if is_profit else ""
        date_str = datetime.now().strftime("%d-%b-%Y")
        
        pct_return = ((ending_balance - starting_balance) / starting_balance * 100) if starting_balance > 0 else 0
        pct_icon = "+" if pct_return >= 0 else ""
        
        message = (
            f"{emoji} <b>DAILY P&L SUMMARY</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"📅 <b>Date:</b> {date_str}\n"
            f"🤖 <b>Mode:</b> {mode}\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"💵 <b>Day's P&L:</b> {pnl_icon}₹{total_pnl:.2f}\n"
            f"📊 <b>Return:</b> {pct_icon}{pct_return:.2f}%\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>Starting:</b> ₹{starting_balance:.2f}\n"
            f"💰 <b>Ending:</b> ₹{ending_balance:.2f}\n"
            f"✅ <b>Trades:</b> {trades_count}\n"
            f"📂 <b>Open Positions:</b> {open_positions}"
        )
        
        success = self._send_message(message)
        if success:
            print(f"📱 Daily P&L notification sent: {pnl_icon}₹{total_pnl:.2f}")
        return success
    
    def notify_market_closed(self, reason: str = "Market is closed"):
        """
        Send notification when market is closed.
        
        Args:
            reason: Reason for market closure (e.g., "Holiday", "Weekend", "Outside trading hours")
        """
        timestamp = datetime.now().strftime("%d-%b-%Y %H:%M")
        
        message = (
            f"🔒 <b>MARKET CLOSED</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"📋 <b>Reason:</b> {reason}\n"
            f"⏰ <b>Time:</b> {timestamp}\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"🔔 Trading agent is on standby.\n"
            f"📱 You will be notified when market opens."
        )
        
        success = self._send_message(message)
        if success:
            print(f"📱 Market closed notification sent")
        return success
    
    def notify_out_of_time(self, cutoff_time: str = "15:15"):
        """
        Send notification when trading time window has ended.
        
        Args:
            cutoff_time: The cutoff time for trading
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        message = (
            f"⏰ <b>OUT OF TRADING TIME</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"🕐 <b>Current Time:</b> {timestamp}\n"
            f"🚫 <b>Cutoff:</b> {cutoff_time}\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"📊 No new trades will be placed.\n"
            f"💤 Trading agent entering standby mode."
        )
        
        success = self._send_message(message)
        if success:
            print(f"📱 Out of time notification sent")
        return success
    
    def notify_agent_started(self, mode: str = "AI-Enhanced"):
        """
        Send notification when trading agent starts.
        
        Args:
            mode: Trading mode
        """
        timestamp = datetime.now().strftime("%d-%b-%Y %H:%M:%S")
        
        message = (
            f"🚀 <b>TRADING AGENT STARTED</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"🤖 <b>Mode:</b> {mode}\n"
            f"⏰ <b>Started:</b> {timestamp}\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"✅ All systems initialized.\n"
            f"📊 Monitoring markets..."
        )
        
        success = self._send_message(message)
        if success:
            print(f"📱 Agent started notification sent")
        return success
    
    def notify_error(self, error_message: str, component: str = "Trading Agent"):
        """
        Send notification for critical errors.
        
        Args:
            error_message: Error description
            component: Component that failed
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        message = (
            f"🚨 <b>ERROR ALERT</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"⚙️ <b>Component:</b> {component}\n"
            f"❌ <b>Error:</b> {error_message}\n"
            f"⏰ <b>Time:</b> {timestamp}\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"⚠️ Please check the system."
        )
        
        success = self._send_message(message)
        if success:
            print(f"📱 Error notification sent")
        return success


# Global notifier instance
_notifier = None

def get_notifier() -> TelegramNotifier:
    """Get or create the global TelegramNotifier instance."""
    global _notifier
    if _notifier is None:
        _notifier = TelegramNotifier()
    return _notifier


# Convenience functions for direct use
def send_trade_started(symbol: str, side: str, quantity: int, price: float, 
                       strategy: str = "", confidence: float = 0.0):
    """Send trade started notification."""
    return get_notifier().notify_trade_started(symbol, side, quantity, price, strategy, confidence)

def send_trade_ended(symbol: str, side: str, quantity: int, 
                     entry_price: float, exit_price: float, pnl: float):
    """Send trade ended notification."""
    return get_notifier().notify_trade_ended(symbol, side, quantity, entry_price, exit_price, pnl)

def send_daily_pnl(total_pnl: float, trades_count: int, starting_balance: float, 
                   ending_balance: float, open_positions: int = 0, mode: str = "AI-Enhanced"):
    """Send daily P&L summary."""
    return get_notifier().notify_daily_pnl(total_pnl, trades_count, starting_balance, 
                                            ending_balance, open_positions, mode)

def send_market_closed(reason: str = "Market is closed"):
    """Send market closed notification."""
    return get_notifier().notify_market_closed(reason)

def send_out_of_time(cutoff_time: str = "15:15"):
    """Send out of trading time notification."""
    return get_notifier().notify_out_of_time(cutoff_time)

def send_agent_started(mode: str = "AI-Enhanced"):
    """Send agent started notification."""
    return get_notifier().notify_agent_started(mode)

def send_error(error_message: str, component: str = "Trading Agent"):
    """Send error notification."""
    return get_notifier().notify_error(error_message, component)


if __name__ == "__main__":
    # Test the notifier
    print("🧪 Testing Telegram Notifier...")
    
    notifier = TelegramNotifier()
    
    if notifier.enabled:
        print("✅ Telegram is configured. Sending test message...")
        success = notifier._send_message("🧪 <b>Test Message</b>\nTelegram notifications are working!")
        if success:
            print("✅ Test message sent successfully!")
        else:
            print("❌ Failed to send test message")
    else:
        print("⚠️ Telegram is not configured.")
        print("\nTo configure, create telegram_config.json with:")
        print(json.dumps({"bot_token": "YOUR_BOT_TOKEN", "chat_id": "YOUR_CHAT_ID"}, indent=2))
