import argparse
import time
import traceback
import os
import atexit
from pathlib import Path
from datetime import datetime, time as dt_time

# ── PID file: lets the dashboard detect this bot process ──────────────────────
_PID_FILE = Path("data/bot.pid")

def _write_pid():
    _PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    _PID_FILE.write_text(str(os.getpid()))

def _remove_pid():
    try:
        _PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass

# ──────────────────────────────────────────────────────────────────────────────
from trading_execution_ai import main_ai_enhanced
from paper_trading_config import PaperTradingConfig
import paper_trading_orders
from paper_portfolio_manager import PaperPortfolioManager
from market_data_fetcher import get_market_data

# parse command line arguments so the backend can override mode/capital
parser = argparse.ArgumentParser(description="Start live/paper trading bot")
parser.add_argument("--mode", choices=["paper", "live"], default="paper",
                    help="Operating mode. 'paper' for virtual trades, 'live' for real orders.")
parser.add_argument("--capital", type=float, default=1.0,
                    help="Capital allocation percentage (0.0 - 1.0) for paper mode."
                    + " Used to scale virtual capital.")
args, _ = parser.parse_known_args()

# ── Mode-specific setup ───────────────────────────────────────────────────────
if args.mode == "paper":
    # Ensure the class constant stays True so place_order_ai routes to paper
    PaperTradingConfig.PAPER_TRADING_MODE = True

    # Scale virtual capital by the requested allocation fraction
    pct = max(0.0, min(args.capital, 1.0))
    PaperTradingConfig.INITIAL_VIRTUAL_CAPITAL = int(PaperTradingConfig.INITIAL_VIRTUAL_CAPITAL * pct)

    # Initialise the paper portfolio (shared module-level instance)
    if not hasattr(paper_trading_orders, 'paper_portfolio') or paper_trading_orders.paper_portfolio is None:
        paper_trading_orders.paper_portfolio = PaperPortfolioManager(
            initial_capital=PaperTradingConfig.INITIAL_VIRTUAL_CAPITAL,
            balance_file=PaperTradingConfig.VIRTUAL_BALANCE_FILE
        )

else:  # live mode
    # CRITICAL: flip the class flag so place_order_ai() routes to place_live_order()
    PaperTradingConfig.PAPER_TRADING_MODE = False

    # Verify that an Upstox access token is present before going any further.
    # Failing early with a clear message is much better than crashing mid-trade.
    try:
        from standalone_login_auth import load_token_from_file
        _token = load_token_from_file()
        if not _token or not _token.get("access_token"):
            print("[BOT] ❌ LIVE mode requires a valid Upstox access token.")
            print("[BOT]    Connect your Demat account from the dashboard first.")
            raise SystemExit(1)
        print("[BOT] ✅ Upstox access token found — live orders enabled.")
    except SystemExit:
        raise
    except Exception as _e:
        print(f"[BOT] ❌ Could not verify Upstox token: {_e}")
        raise SystemExit(1)

print(f"[BOT] Starting in {args.mode.upper()} mode with capital allocation {args.capital*100:.0f}%")

# ── Constants ─────────────────────────────────────────────────────────────────
TRADE_INTERVAL = 300  # seconds between cycles (5 minutes)
PROFIT_TARGET_PCT = PaperTradingConfig.PROFIT_TARGET_PCT
STOP_LOSS_PCT     = PaperTradingConfig.STOP_LOSS_PCT

MARKET_OPEN  = dt_time(9, 15)
MARKET_CLOSE = dt_time(15, 30)


def is_market_open():
    """Return True if the Indian equity market is currently open."""
    now = datetime.now().time()
    is_weekday = datetime.now().weekday() < 5
    return is_weekday and MARKET_OPEN <= now <= MARKET_CLOSE


def _get_current_balance() -> str:
    """
    Return a formatted balance string appropriate for the current mode.

    - Paper mode  : uses the in-memory paper portfolio cash balance.
    - Live mode   : fetches the real available margin from Upstox so the
                    loop header always shows accurate real-money figures.
    """
    if args.mode == "paper":
        portfolio = paper_trading_orders.paper_portfolio
        if portfolio is not None:
            return f"₹{portfolio.cash:,.2f} (virtual)"
        return "N/A"
    else:
        # Live mode — pull real balance from Upstox
        try:
            from live_portfolio_manager import LivePortfolioManager
            mgr = LivePortfolioManager(capital_allocation_pct=args.capital * 100)
            balance = mgr.get_balance()
            return f"₹{balance:,.2f} (real)"
        except Exception as _e:
            return f"(balance unavailable: {_e})"


def auto_manage_positions():
    """
    Monitor open positions in **paper mode** and auto-exit on target/stop.

    In live mode Upstox handles the positions natively, so this function
    is intentionally skipped (see run_continuous_trading).
    """
    portfolio = paper_trading_orders.paper_portfolio

    if not portfolio or not portfolio.positions:
        print("\n[MONITOR] No open positions to track.")
        return

    print(f"\n[MONITOR] Tracking {len(portfolio.positions)} open positions for exits...")
    positions_to_sell = []

    for symbol, pos in list(portfolio.positions.items()):
        entry_price = pos['avg_price']
        qty = pos.get('qty', 0)
        stock_name = pos.get('stock_name', symbol)

        # Get real-time price
        current_price, _ = get_market_data(symbol, interval="5minute", days=1)
        if not current_price:
            print(f"   ⚠️ Could not fetch real-time price for {stock_name}")
            continue

        pnl_pct   = (current_price - entry_price) / entry_price
        pnl_in_rs = (current_price - entry_price) * qty

        status_color = "🟢" if pnl_pct >= 0 else "🔴"
        print(f"   {status_color} {stock_name}: Entry=₹{entry_price:.2f} | "
              f"Current=₹{current_price:.2f} | P&L={pnl_pct:.2%} (₹{pnl_in_rs:.2f})")

        if pnl_pct >= PROFIT_TARGET_PCT:
            print(f"   🎯 PROFIT TARGET HIT (+{pnl_pct:.2%})! Queuing sell order...")
            positions_to_sell.append((symbol, qty, current_price, stock_name, "Take Profit"))
        elif pnl_pct <= -STOP_LOSS_PCT:
            print(f"   🛑 STOP LOSS HIT ({pnl_pct:.2%})! Queuing sell order...")
            positions_to_sell.append((symbol, qty, current_price, stock_name, "Stop Loss"))

    # Execute queued sells
    for symbol, qty, price, stock_name, reason in positions_to_sell:
        success, msg = portfolio.execute_sell(symbol, qty, price, stock_name)
        if success:
            print(f"   ✅ [AUTO-EXIT] Sold {qty} {stock_name} @ ₹{price:.2f} (Reason: {reason})")
        else:
            print(f"   ❌ [AUTO-EXIT FAILED] {msg}")


def run_continuous_trading():
    """Main continuous trading loop — works in both paper and live modes."""
    print("=" * 70)
    mode_label = "PAPER" if args.mode == "paper" else "LIVE ⚠️  (REAL MONEY)"
    print(f"🤖 REAL-TIME INTRADAY {mode_label} TRADING BOT")
    print("=" * 70)
    print(f"• Loop Interval     : {TRADE_INTERVAL} seconds")
    print(f"• Auto Profit Target: +{PROFIT_TARGET_PCT*100:.1f}%")
    print(f"• Auto Stop Loss    : -{STOP_LOSS_PCT*100:.1f}%")
    if args.mode == "paper":
        print(f"• Virtual Capital   : ₹{PaperTradingConfig.INITIAL_VIRTUAL_CAPITAL:,.2f}")
    else:
        print("• Orders            : REAL orders placed on Upstox")

    iteration = 0
    while True:
        iteration += 1
        balance_str = _get_current_balance()
        print(f"\n{'='*70}")
        print(f"🔄 CYCLE #{iteration} | Time: {datetime.now().strftime('%H:%M:%S')} | Balance: {balance_str}")
        print(f"{'='*70}")

        try:
            # 1. Quick market-hours gate — skip everything when closed.
            if not is_market_open():
                print("\n⏸️ Market is currently closed. Checking again in 1 minute...")
                time.sleep(60)
                continue

            # 2. Paper mode only — check positions for auto take-profit / stop-loss.
            #    Only runs inside market hours so prices are live, not stale.
            if args.mode == "paper":
                auto_manage_positions()

            # 3. Run the main AI enhanced trading logic.
            print("\n[AI_ENGINE] Scanning NIFTY 50 universe for entry setups...")
            success = main_ai_enhanced()

            if not success:
                print("⚠️ AI Engine returned unsuccessful execution. (Could be market closed/holiday).")

        except KeyboardInterrupt:
            print("\n🛑 Stopped by User.")
            break
        except Exception as e:
            print(f"\n❌ CRITICAL LOOP ERROR: {e}")
            traceback.print_exc()

        print(f"\n⏳ Cycle {iteration} complete. Resting for {TRADE_INTERVAL} seconds...")
        time.sleep(TRADE_INTERVAL)


if __name__ == "__main__":
    _write_pid()
    atexit.register(_remove_pid)
    run_continuous_trading()
