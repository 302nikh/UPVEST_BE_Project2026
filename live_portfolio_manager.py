"""
Live Portfolio Manager
======================
Manages real portfolio using Upstox API for live trading.
Mirrors the PaperPortfolioManager interface for easy switching.

Uses:
    - trading_execution.py: place_order(), get_available_funds()
    - standalone_login_auth.py: load_token_from_file()
    - risk_manager.py: RiskManager for trade validation
"""

import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Import existing modules
from standalone_login_auth import load_token_from_file
from trading_execution import get_product_type   # MIS/CNC helper


class LivePortfolioManager:
    """
    Manages real Upstox portfolio for live trading.
    Provides the same interface as PaperPortfolioManager so the agent
    can switch between modes seamlessly.
    """

    def __init__(self, capital_allocation_pct: float = 100.0):
        """
        Initialize live portfolio manager.

        Args:
            capital_allocation_pct: Percentage of real capital to use (10-100)
        """
        self.capital_allocation_pct = max(10.0, min(100.0, capital_allocation_pct))
        self.trade_history = []
        self.state_file = Path("data/live_portfolio_state.json")
        self._load_state()
        print(f"[LIVE PORTFOLIO] Initialized with {self.capital_allocation_pct:.0f}% capital allocation")

    def _get_headers(self) -> dict:
        """Get authorization headers using stored access token."""
        token_info = load_token_from_file()
        if not token_info or "access_token" not in token_info:
            raise ConnectionError("No valid Upstox access token found. Please authenticate first.")
        return {
            "Authorization": f"Bearer {token_info['access_token']}",
            "Content-Type": "application/json",
            "accept": "application/json",
            "Api-Version": "2.0"
        }

    def _load_state(self):
        """Load trade history from file."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                self.trade_history = data.get("trade_history", [])
        except Exception as e:
            print(f"[LIVE PORTFOLIO] Warning: Could not load state: {e}")
            self.trade_history = []

    def _save_state(self):
        """Save trade history to file."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump({
                    "trade_history": self.trade_history[-200:],  # Keep last 200 trades
                    "last_updated": datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"[LIVE PORTFOLIO] Warning: Could not save state: {e}")

    def get_balance(self) -> float:
        """
        Fetch real available balance from Upstox.

        Returns:
            Available margin/funds in the account
        """
        try:
            headers = self._get_headers()
            url = "https://api.upstox.com/v2/user/get-funds-and-margin?segment=SEC"
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    margin_data = data.get("data", {})
                    available = float(margin_data.get("equity", {}).get("available_margin", 0))
                    # Apply capital allocation percentage
                    usable = available * (self.capital_allocation_pct / 100.0)
                    print(f"[LIVE PORTFOLIO] Available: Rs.{available:,.2f}, "
                          f"Usable ({self.capital_allocation_pct:.0f}%): Rs.{usable:,.2f}")
                    return usable
            
            print(f"[LIVE PORTFOLIO] Failed to fetch balance: {response.status_code}")
            return 0.0
        except ConnectionError as e:
            print(f"[LIVE PORTFOLIO] Auth error: {e}")
            return 0.0
        except Exception as e:
            print(f"[LIVE PORTFOLIO] Error fetching balance: {e}")
            return 0.0

    def get_positions(self) -> List[Dict]:
        """
        Fetch real positions from Upstox.

        Returns:
            List of position dictionaries
        """
        try:
            headers = self._get_headers()
            url = "https://api.upstox.com/v2/portfolio/short-term-positions"
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    positions = data.get("data", [])
                    if positions is None:
                        positions = []
                    print(f"[LIVE PORTFOLIO] Fetched {len(positions)} positions")
                    return positions

            print(f"[LIVE PORTFOLIO] Failed to fetch positions: {response.status_code}")
            return []
        except Exception as e:
            print(f"[LIVE PORTFOLIO] Error fetching positions: {e}")
            return []

    def get_holdings(self) -> List[Dict]:
        """
        Fetch holdings (delivery positions) from Upstox.

        Returns:
            List of holding dictionaries
        """
        try:
            headers = self._get_headers()
            url = "https://api.upstox.com/v2/portfolio/long-term-holdings"
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    holdings = data.get("data", [])
                    if holdings is None:
                        holdings = []
                    return holdings

            return []
        except Exception as e:
            print(f"[LIVE PORTFOLIO] Error fetching holdings: {e}")
            return []

    def execute_buy(self, symbol: str, qty: int, price: float,
                    stock_name: str = "", strategy: str = "AI", **kwargs) -> Tuple[bool, str]:
        """
        Place a real BUY order on Upstox.
        Pass interval=... kwarg to use MIS for intraday trades.
        """
        if qty <= 0:
            return False, "Quantity must be positive"

        try:
            headers = self._get_headers()
            url = "https://api.upstox.com/v2/order/place"

            product = get_product_type(kwargs.get("interval", "day"), strategy)
            product_label = "MIS (Intraday)" if product == "I" else "CNC (Delivery)"
            print(f"[LIVE BUY] Product: {product_label}")

            payload = {
                "instrument_token": symbol,
                "quantity": qty,
                "order_type": "MARKET",
                "transaction_type": "BUY",
                "product": product,
                "duration": "DAY"
            }

            response = requests.post(url, headers=headers, json=payload)
            result = response.json()

            if result.get("status") == "success":
                order_id = result.get("data", {}).get("order_id", "N/A")
                msg = f"BUY {qty} {stock_name or symbol} @ Rs.{price:.2f} | Order ID: {order_id}"
                print(f"[LIVE BUY] {msg}")

                # Record trade
                self._record_trade("BUY", symbol, stock_name, qty, price, order_id, "SUCCESS", strategy)
                return True, msg
            else:
                err = result.get("errors", [{}])
                err_msg = err[0].get("message", str(result)) if err else str(result)
                msg = f"BUY failed for {stock_name or symbol}: {err_msg}"
                print(f"[LIVE BUY FAILED] {msg}")
                self._record_trade("BUY", symbol, stock_name, qty, price, None, "FAILED", strategy)
                return False, msg

        except ConnectionError as e:
            msg = f"Auth error: {e}"
            print(f"[LIVE BUY ERROR] {msg}")
            return False, msg
        except Exception as e:
            msg = f"Order error: {e}"
            print(f"[LIVE BUY ERROR] {msg}")
            self._record_trade("BUY", symbol, stock_name, qty, price, None, "ERROR", strategy)
            return False, msg

    def execute_sell(self, symbol: str, qty: int, price: float,
                     stock_name: str = "", strategy: str = "AI", **kwargs) -> Tuple[bool, str]:
        """
        Place a real SELL order on Upstox.
        Pass interval=... kwarg to use MIS for intraday trades.
        """
        if qty <= 0:
            return False, "Quantity must be positive"

        try:
            headers = self._get_headers()
            url = "https://api.upstox.com/v2/order/place"

            product = get_product_type(kwargs.get("interval", "day"), strategy)
            product_label = "MIS (Intraday)" if product == "I" else "CNC (Delivery)"
            print(f"[LIVE SELL] Product: {product_label}")

            payload = {
                "instrument_token": symbol,
                "quantity": qty,
                "order_type": "MARKET",
                "transaction_type": "SELL",
                "product": product,
                "duration": "DAY"
            }

            response = requests.post(url, headers=headers, json=payload)
            result = response.json()

            if result.get("status") == "success":
                order_id = result.get("data", {}).get("order_id", "N/A")
                msg = f"SELL {qty} {stock_name or symbol} @ Rs.{price:.2f} | Order ID: {order_id}"
                print(f"[LIVE SELL] {msg}")

                self._record_trade("SELL", symbol, stock_name, qty, price, order_id, "SUCCESS", strategy)
                return True, msg
            else:
                err = result.get("errors", [{}])
                err_msg = err[0].get("message", str(result)) if err else str(result)
                msg = f"SELL failed for {stock_name or symbol}: {err_msg}"
                print(f"[LIVE SELL FAILED] {msg}")
                self._record_trade("SELL", symbol, stock_name, qty, price, None, "FAILED", strategy)
                return False, msg

        except ConnectionError as e:
            msg = f"Auth error: {e}"
            print(f"[LIVE SELL ERROR] {msg}")
            return False, msg
        except Exception as e:
            msg = f"Order error: {e}"
            print(f"[LIVE SELL ERROR] {msg}")
            self._record_trade("SELL", symbol, stock_name, qty, price, None, "ERROR", strategy)
            return False, msg

    def _record_trade(self, side: str, symbol: str, stock_name: str, qty: int,
                      price: float, order_id: Optional[str], status: str, strategy: str):
        """Record a trade to history and database."""
        trade = {
            "timestamp": datetime.now().isoformat(),
            "side": side,
            "symbol": symbol,
            "stock_name": stock_name or symbol,
            "quantity": qty,
            "price": price,
            "order_id": order_id or "",
            "status": status,
            "strategy": strategy,
            "mode": "LIVE"
        }
        self.trade_history.append(trade)
        self._save_state()

        # Also log to database
        try:
            from database_manager import log_trade
            log_trade({
                'timestamp': datetime.now(),
                'symbol': symbol,
                'stock_name': stock_name or symbol.split('|')[0],
                'strategy': strategy,
                'signal': side,
                'quantity': qty,
                'price': price,
                'order_id': order_id or '',
                'status': status,
                'ai_enabled': True,
                'confidence': None,
                'models_used': ''
            })
        except Exception as e:
            print(f"[LIVE PORTFOLIO] DB logging failed: {e}")

    def get_portfolio_value(self) -> float:
        """
        Get total portfolio value from Upstox.

        Returns:
            Total equity value
        """
        try:
            headers = self._get_headers()
            url = "https://api.upstox.com/v2/user/get-funds-and-margin?segment=SEC"
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    margin = data.get("data", {})
                    equity = margin.get("equity", {})
                    # Total = used margin + available margin
                    used = float(equity.get("used_margin", 0))
                    available = float(equity.get("available_margin", 0))
                    total = used + available
                    return total

            return 0.0
        except Exception as e:
            print(f"[LIVE PORTFOLIO] Error getting portfolio value: {e}")
            return 0.0

    def get_open_position_count(self) -> int:
        """Get number of open positions."""
        positions = self.get_positions()
        # Filter for positions with non-zero quantity
        open_positions = [p for p in positions if p.get("quantity", 0) != 0]
        return len(open_positions)

    def get_statistics(self) -> dict:
        """Get trade statistics."""
        if not self.trade_history:
            return {
                "total_trades": 0,
                "successful_trades": 0,
                "failed_trades": 0,
                "win_rate": 0.0,
                "mode": "LIVE"
            }

        successful = [t for t in self.trade_history if t["status"] == "SUCCESS"]
        failed = [t for t in self.trade_history if t["status"] != "SUCCESS"]

        return {
            "total_trades": len(self.trade_history),
            "successful_trades": len(successful),
            "failed_trades": len(failed),
            "win_rate": (len(successful) / len(self.trade_history) * 100) if self.trade_history else 0,
            "mode": "LIVE"
        }

    def get_order_history(self) -> List[Dict]:
        """
        Fetch order history from Upstox.

        Returns:
            List of order dictionaries
        """
        try:
            headers = self._get_headers()
            url = "https://api.upstox.com/v2/order/retrieve-all"
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return data.get("data", [])

            return []
        except Exception as e:
            print(f"[LIVE PORTFOLIO] Error fetching orders: {e}")
            return []

    def square_off_all(self) -> List[Tuple[bool, str]]:
        """
        Square off (close) all open positions.

        Returns:
            List of (success, message) tuples for each position closed
        """
        results = []
        positions = self.get_positions()

        for pos in positions:
            qty = pos.get("quantity", 0)
            symbol = pos.get("instrument_token", "")
            stock_name = pos.get("tradingsymbol", symbol)

            if qty > 0:
                # Long position - SELL to close
                result = self.execute_sell(symbol, abs(qty), pos.get("last_price", 0),
                                           stock_name, "SQUARE_OFF")
                results.append(result)
            elif qty < 0:
                # Short position - BUY to close
                result = self.execute_buy(symbol, abs(qty), pos.get("last_price", 0),
                                          stock_name, "SQUARE_OFF")
                results.append(result)

        if not positions:
            print("[LIVE PORTFOLIO] No open positions to square off")

        return results


if __name__ == "__main__":
    print("=" * 50)
    print("Live Portfolio Manager - Status Check")
    print("=" * 50)

    try:
        manager = LivePortfolioManager(capital_allocation_pct=100)

        # Check balance
        balance = manager.get_balance()
        print(f"\nAvailable Balance: Rs.{balance:,.2f}")

        # Check positions
        positions = manager.get_positions()
        print(f"Open Positions: {len(positions)}")

        # Check portfolio value
        value = manager.get_portfolio_value()
        print(f"Portfolio Value: Rs.{value:,.2f}")

        # Stats
        stats = manager.get_statistics()
        print(f"\nTrade Statistics: {json.dumps(stats, indent=2)}")

    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have a valid Upstox access token.")
