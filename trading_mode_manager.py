"""
Trading Mode Manager
====================
Manages two independent mode axes:

  1. Execution Mode  : "paper" | "live"   — where orders go (simulated vs real money)
  2. Strategy Mode   : "stock" | "intraday" — how the bot trades

       stock    → daily candles, CNC (delivery) orders, holds overnight
       intraday → 30-min candles, MIS orders, auto square-off at 3:20 PM

All settings persist to data/trading_mode.json.

Usage:
    from trading_mode_manager import TradingModeManager

    mgr = TradingModeManager()
    mgr.set_strategy_mode("intraday")   # switch to intraday
    mgr.set_strategy_mode("stock")      # switch back to stock
    mgr.set_mode("live")                # switch to live execution
    mgr.set_capital_allocation(75)      # use 75% of capital
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple


CONFIG_FILE = Path("data/trading_mode.json")

DEFAULT_CONFIG = {
    "mode": "paper",            # "paper" or "live"
    "strategy_mode": "stock",   # "stock" or "intraday"  ← NEW
    "capital_allocation_pct": 100.0,
    "last_switched": None,
    "last_switched_by": "system",
    "live_trading_confirmed": False,
}

# ── Strategy-mode constants (read by execution scripts) ──────────────────────
STRATEGY_MODE_STOCK     = "stock"
STRATEGY_MODE_INTRADAY  = "intraday"

# Intraday candle interval used when strategy_mode == "intraday"
INTRADAY_INTERVAL  = "30minute"
DELIVERY_INTERVAL  = "day"


class TradingModeManager:
    """
    Manages trading mode switching and capital allocation.
    """

    def __init__(self):
        """Initialize and load saved configuration."""
        self.config = self._load_config()
        strat = self.config.get("strategy_mode", "stock").upper()
        print(f"[MODE] Execution: {self.config['mode'].upper()} "
              f"| Strategy: {strat} "
              f"| Capital: {self.config['capital_allocation_pct']:.0f}%")

    def _load_config(self) -> dict:
        """Load configuration from file."""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r') as f:
                    saved = json.load(f)
                # Merge with defaults for any missing keys
                config = {**DEFAULT_CONFIG, **saved}
                return config
        except Exception as e:
            print(f"[MODE] Warning: Could not load config: {e}")

        return DEFAULT_CONFIG.copy()

    def _save_config(self):
        """Save configuration to file."""
        try:
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"[MODE] Warning: Could not save config: {e}")

    def get_mode(self) -> str:
        """Get current execution mode ('paper' or 'live')."""
        return self.config["mode"]

    def get_strategy_mode(self) -> str:
        """Get current strategy mode ('stock' or 'intraday')."""
        return self.config.get("strategy_mode", "stock")

    def is_intraday_mode(self) -> bool:
        """Convenience: True when running in intraday mode."""
        return self.get_strategy_mode() == STRATEGY_MODE_INTRADAY

    def get_active_interval(self) -> str:
        """
        Returns the candle interval appropriate for the current strategy mode.
          stock    → 'day'
          intraday → '30minute'
        """
        return INTRADAY_INTERVAL if self.is_intraday_mode() else DELIVERY_INTERVAL

    def set_strategy_mode(self, mode: str) -> tuple:
        """
        Switch between 'stock' and 'intraday' strategy modes.

        stock    → daily candles, product=D (CNC), holds overnight
        intraday → 30-min candles, product=I (MIS), squares off at 3:20 PM

        Returns: (success: bool, message: str)
        """
        mode = mode.lower().strip()
        if mode not in (STRATEGY_MODE_STOCK, STRATEGY_MODE_INTRADAY):
            return False, "Invalid strategy mode. Use 'stock' or 'intraday'."

        if mode == self.config.get("strategy_mode", "stock"):
            return True, f"Already in {mode} strategy mode."

        old = self.config.get("strategy_mode", "stock")
        self.config["strategy_mode"] = mode
        self.config["last_switched"] = datetime.now().isoformat()
        self._save_config()

        interval = INTRADAY_INTERVAL if mode == STRATEGY_MODE_INTRADAY else DELIVERY_INTERVAL
        product  = "I (MIS)" if mode == STRATEGY_MODE_INTRADAY else "D (CNC)"
        msg = (
            f"Strategy mode switched: {old.upper()} → {mode.upper()} | "
            f"Interval: {interval} | Product: {product}"
        )
        print(f"[MODE] {msg}")
        return True, msg

    def get_capital_allocation(self) -> float:
        """Get current capital allocation percentage (10-100)."""
        return self.config["capital_allocation_pct"]

    def set_capital_allocation(self, pct: float) -> Tuple[bool, str]:
        """
        Set capital allocation percentage.

        Args:
            pct: Percentage (10-100)

        Returns:
            (success, message)
        """
        if pct < 10 or pct > 100:
            return False, "Capital allocation must be between 10% and 100%"

        self.config["capital_allocation_pct"] = float(pct)
        self._save_config()
        msg = f"Capital allocation set to {pct:.0f}%"
        print(f"[MODE] {msg}")
        return True, msg

    def can_switch_to_live(self) -> Tuple[bool, str]:
        """
        Check if prerequisites for live trading are met.

        Returns:
            (can_switch, reason)
        """
        issues = []

        # Check 1: Access token exists
        token_file = Path("access_token.json")
        if not token_file.exists():
            issues.append("No Upstox access token. Please connect your Demat account first.")
        else:
            try:
                with open(token_file, 'r') as f:
                    token = json.load(f)
                if not token.get("access_token"):
                    issues.append("Access token is empty. Please re-authenticate with Upstox.")
            except Exception:
                issues.append("Access token file is corrupted. Please re-authenticate.")

        # Check 2: Credentials exist
        creds_file = Path("creds.json")
        if not creds_file.exists():
            issues.append("No credentials file found. Please set up API credentials.")

        if issues:
            return False, " | ".join(issues)

        return True, "All prerequisites met. Ready for live trading."

    def set_mode(self, mode: str, confirmed: bool = False) -> Tuple[bool, str]:
        """
        Switch trading mode.

        Args:
            mode: 'paper' or 'live'
            confirmed: Must be True to switch to live (safety check)

        Returns:
            (success, message)
        """
        mode = mode.lower().strip()

        if mode not in ("paper", "live"):
            return False, "Invalid mode. Use 'paper' or 'live'."

        if mode == self.config["mode"]:
            return True, f"Already in {mode} mode."

        if mode == "live":
            # Check prerequisites
            can_switch, reason = self.can_switch_to_live()
            if not can_switch:
                return False, f"Cannot switch to live: {reason}"

            # Require explicit confirmation
            if not confirmed:
                return False, ("CONFIRMATION REQUIRED: Live trading uses REAL MONEY. "
                               "Please confirm to proceed.")

        # Switch mode
        old_mode = self.config["mode"]
        self.config["mode"] = mode
        self.config["last_switched"] = datetime.now().isoformat()
        self.config["live_trading_confirmed"] = (mode == "live")
        self._save_config()

        msg = f"Switched from {old_mode.upper()} to {mode.upper()} mode"
        print(f"[MODE] {msg}")
        return True, msg

    def get_status(self) -> dict:
        """Get full status including mode, capital allocation, and prerequisites."""
        can_live, live_reason = self.can_switch_to_live()
        strat = self.get_strategy_mode()

        return {
            "mode": self.config["mode"],
            "strategy_mode": strat,
            "active_interval": self.get_active_interval(),
            "product_type": "I (MIS)" if strat == STRATEGY_MODE_INTRADAY else "D (CNC)",
            "capital_allocation_pct": self.config["capital_allocation_pct"],
            "last_switched": self.config.get("last_switched"),
            "can_switch_to_live": can_live,
            "live_prerequisites": live_reason,
            "live_confirmed": self.config.get("live_trading_confirmed", False)
        }

    def reset_to_paper(self):
        """Emergency reset to paper trading mode."""
        self.config["mode"] = "paper"
        self.config["live_trading_confirmed"] = False
        self.config["last_switched"] = datetime.now().isoformat()
        self._save_config()
        print("[MODE] Emergency reset to PAPER mode")


# Singleton instance
_instance = None


def get_mode_manager() -> TradingModeManager:
    """Get or create singleton TradingModeManager instance."""
    global _instance
    if _instance is None:
        _instance = TradingModeManager()
    return _instance


if __name__ == "__main__":
    import sys

    mgr = TradingModeManager()

    # Allow quick CLI switching:  python trading_mode_manager.py stock
    #                             python trading_mode_manager.py intraday
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ("stock", "intraday"):
            ok, msg = mgr.set_strategy_mode(arg)
            print(f"{'✅' if ok else '❌'} {msg}")
        elif arg in ("paper", "live"):
            ok, msg = mgr.set_mode(arg, confirmed=(arg == "paper"))
            print(f"{'✅' if ok else '❌'} {msg}")
        else:
            print(f"Unknown argument: {arg}")
            print("Usage: python trading_mode_manager.py [stock|intraday|paper|live]")
        sys.exit(0)

    # Default: show status
    print("=" * 55)
    print("         Trading Mode Manager - Status")
    print("=" * 55)
    status = mgr.get_status()
    print(f"\n  Execution Mode : {status['mode'].upper()}")
    print(f"  Strategy Mode  : {status['strategy_mode'].upper()}")
    print(f"  Candle Interval: {status['active_interval']}")
    print(f"  Order Product  : {status['product_type']}")
    print(f"  Capital        : {status['capital_allocation_pct']:.0f}%")
    print(f"  Can Go Live    : {'Yes' if status['can_switch_to_live'] else 'No'}")
    print(f"  Prerequisites  : {status['live_prerequisites']}")
    print(f"  Last Switched  : {status['last_switched'] or 'Never'}")
    print()
    print("  Quick switch commands:")
    print("    python trading_mode_manager.py stock     ← daily candles, CNC")
    print("    python trading_mode_manager.py intraday  ← 30-min candles, MIS")
    print("    python trading_mode_manager.py paper     ← paper trading")
    print("    python trading_mode_manager.py live      ← live trading")
