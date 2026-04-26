"""
AI-Enhanced Trading Execution
------------------------------
Integrates AI decision engine with existing trading strategies.
"""

# ensure console uses UTF-8 encoding immediately so early emojis don't crash
import sys, io
if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True
    )
if hasattr(sys.stderr, 'encoding') and sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True
    )

import json
import requests
import pandas as pd
import time
import os
from datetime import datetime
from strategy_engine import StrategyEngine
from pre_startup_checks import run_pre_startup_checks
# Safe token loader \u2014 returns empty dict in paper mode (no real credentials needed)
def load_token_from_file():
    try:
        from standalone_login_auth import load_token_from_file as _load
        return _load() or {}
    except Exception:
        return {}

# upstox helpers \u2014 wrapped to avoid crash when no token present
try:
    from upstox import upstox_margin, upstox_positions
except Exception:
    def upstox_margin(c): return c
    def upstox_positions(c): return c
from database_manager import initialize_database, log_trade, update_daily_summary, store_rl_experience

# Import Paper Trading components
try:
    from paper_trading_config import PaperTradingConfig
    from paper_portfolio_manager import PaperPortfolioManager
    PAPER_TRADING_AVAILABLE = True
    print(f"📝 Paper Trading: {PaperTradingConfig.get_mode_display()}")
except Exception as e:
    PAPER_TRADING_AVAILABLE = False
    print(f"⚠️ Paper trading not available: {e}")

# Import AI components
try:
    from ai_agent.ai_decision_engine import AIDecisionEngine
    AI_ENABLED = True
    print("🤖 AI Agent loaded successfully!")
except Exception as e:
    AI_ENABLED = False
    print(f"⚠️ AI Agent not available: {e}")
    print("   Running in rule-based mode only.")

# Import self-learning components
try:
    from rl_learning_manager import RLLearningManager
    from trade_outcome_tracker import TradeOutcomeTracker
    from rl_config import RLConfig
    import numpy as np
    RL_LEARNING_ENABLED = True
    print("🧠 Self-learning components loaded!")
except Exception as e:
    RL_LEARNING_ENABLED = False
    print(f"⚠️ Self-learning not available: {e}")

# Import Telegram notification module
try:
    from telegram_notifier import (
        send_trade_started, send_trade_ended, send_daily_pnl,
        send_market_closed, send_out_of_time, send_agent_started, send_error
    )
    TELEGRAM_ENABLED = True
    print("📱 Telegram notifications loaded!")
except Exception as e:
    TELEGRAM_ENABLED = False
    print(f"⚠️ Telegram notifications not available: {e}")


# Import functions from original trading_execution
from trading_execution import (
    fetch_historical_data,
    get_available_funds,
    calculate_quantity,
    get_pnL_summary,
    get_product_type,          # dynamic MIS/CNC selection
)

# Import mode manager to read strategy_mode at runtime
try:
    from trading_mode_manager import TradingModeManager
    _mode_mgr = TradingModeManager()
except Exception as _e:
    _mode_mgr = None
    print(f"⚠️ TradingModeManager unavailable: {_e}")

# Global paper portfolio instance
paper_portfolio = None


def place_order_ai(symbol, side, qty, price, strategy="unknown", stock_name="",
                   ai_enabled=False, confidence=None, models_used="", interval="day"):
    """
    Place an order via Upstox REST API and log to database with AI metadata.
    When paper trading is enabled this will delegate to the paper trading
    module (which itself handles live orders when paper mode is off).
    Product type (MIS/CNC) is decided automatically from interval + strategy.
    """
    # route through paper trading helper if available
    if PAPER_TRADING_AVAILABLE and PaperTradingConfig.PAPER_TRADING_MODE:
        try:
            # import inside function to avoid circular import during startup
            from paper_trading_orders import place_order_ai as _paper_place_order
            return _paper_place_order(
                symbol, side, qty, price,
                strategy=strategy,
                stock_name=stock_name,
                ai_enabled=ai_enabled,
                confidence=confidence,
                models_used=models_used,
                interval=interval
            )
        except Exception as e:
            print(f"⚠️ Failed to route to paper order module: {e}")
            # fallback to live below

    if qty <= 0:
        print(f"⚠️ Quantity is 0. Skipping order for {symbol}.")
        return

    token_info = load_token_from_file()
    access_token = token_info.get("access_token")

    url = "https://api.upstox.com/v2/order/place"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    product = get_product_type(interval, strategy)
    product_label = "MIS (Intraday)" if product == "I" else "CNC (Delivery)"
    print(f"   📦 Product type: {product_label}")

    payload = {
        "instrument_token": symbol,
        "quantity": qty,
        "order_type": "MARKET",
        "transaction_type": side,
        "product": product,
        "duration": "DAY"
    }

    order_id = None
    status = "FAILED"
    
    try:
        r = requests.post(url, headers=headers, json=payload)
        response = r.json()
        
        if response.get("status") == "success":
            order_id = response.get('data', {}).get('order_id')
            status = "SUCCESS"
            msg = f"ORDER EXECUTED: {side} {qty} {symbol} @ ₹{price:.2f} | ID: {order_id}"
            print(f"✅ {msg}")
        else:
             err_msg = f"❌ Order Failed: {response}"
             print(err_msg)
    except Exception as e:
        print(f"❌ Order Exception: {e}")
    
    # Log trade to database with AI metadata
    try:
        trade_data = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'stock_name': stock_name if stock_name else symbol.split('|')[0],
            'strategy': strategy,
            'signal': side,
            'quantity': qty,
            'price': price,
            'order_id': order_id if order_id else '',
            'status': status,
            'ai_enabled': ai_enabled,
            'confidence': confidence,
            'models_used': models_used
        }
        log_trade(trade_data)
    except Exception as e:
        print(f"⚠️ Failed to log trade to database: {e}")


def main_ai_enhanced():
    """
    AI-enhanced trading execution with self-learning capabilities.
    """
    print("\n🚀 Starting AI-Enhanced Trading Execution (Self-Learning Mode)...\n")
    
    # ── Read strategy mode from mode manager ──────────────────────────────────
    is_intraday = _mode_mgr.is_intraday_mode() if _mode_mgr else False
    active_interval = _mode_mgr.get_active_interval() if _mode_mgr else "day"

    mode_label = "INTRADAY (30-min, MIS)" if is_intraday else "STOCK (Daily, CNC)"
    print(f"\n📋 Strategy Mode : {mode_label}")

    notification_mode = "AI-Enhanced (Self-Learning)" if RL_LEARNING_ENABLED else ("AI-Enhanced" if AI_ENABLED else "Rule-Based")
    notification_mode += f" [{mode_label}]"
    
    # Send bot started notification
    if TELEGRAM_ENABLED:
        send_agent_started(mode=notification_mode)
    
    # Initialize database
    initialize_database()

    # Step 1: Check market status
    if not run_pre_startup_checks():
        print("❌ Pre-checks failed. Aborting startup.")
        # Send market closed notification
        if TELEGRAM_ENABLED:
            send_market_closed(reason="Pre-startup checks failed - Market may be closed or holiday")
        return False
    
    # Record starting balance
    starting_balance = get_available_funds()

    # Step 2a: Initialize Risk Manager (soft guard — never blocks startup)
    risk_mgr = None
    try:
        from risk_manager import RiskManager
        risk_mgr = RiskManager(initial_capital=max(starting_balance, 1.0))
        print("[✅ RISK] Risk manager active.")
    except Exception as _re:
        print(f"[⚠️ RISK] Risk manager unavailable: {_re}. Continuing without risk checks.")

    # Step 2: Initialize AI engine (if available)
    ai_engine = None
    model_path = 'data/trained_models/lstm_best.pth'
    
    if AI_ENABLED and os.path.exists(model_path):
        print("🤖 Loading AI model...")
        try:
            ai_engine = AIDecisionEngine(model_path=model_path, use_gpu=False)
            print("✅ AI model loaded successfully!")
        except Exception as e:
            print(f"⚠️ AI model loading failed: {e}")
            print("   Falling back to rule-based strategies.")
            ai_engine = None
    elif AI_ENABLED:
        print(f"⚠️ AI model not found at {model_path}")
        print("   Run 'python ai_agent/model_trainer.py' to train the model first.")
        print("   Falling back to rule-based strategies.")
    
    # Step 2.5: Initialize self-learning components
    rl_manager = None
    outcome_tracker = None
    
    if RL_LEARNING_ENABLED:
        try:
            print("\n🧠 Initializing Self-Learning System...")
            rl_manager = RLLearningManager(state_dim=34, action_dim=3)
            outcome_tracker = TradeOutcomeTracker(
                profit_reward_scale=RLConfig.PROFIT_REWARD_SCALE,
                hold_time_penalty_threshold=RLConfig.HOLD_TIME_PENALTY_THRESHOLD
            )
            print(RLConfig.get_config_summary())
            print("✅ Self-learning system initialized!")
        except Exception as e:
            print(f"⚠️ Self-learning initialization failed: {e}")
            rl_manager = None
            outcome_tracker = None
    
    # Load watchlist from stock_universe.py (100+ stocks)
    # Falls back to a minimal hardcoded list if the module is unavailable
    try:
        from stock_universe import get_watchlist
        if is_intraday:
            # Intraday mode: only pick stocks with shorter intervals
            portfolio = get_watchlist(
                include_nifty50=True,
                include_next50=False,
                include_momentum=False,
                include_intraday=True,
                risk_levels=["low", "medium", "high"],
                max_stocks=50
            )
            # Force every stock to 30-minute interval for intraday
            for item in portfolio:
                item["interval"] = "30minute"
            print(f"[UNIVERSE] Intraday mode: loaded {len(portfolio)} stocks (30-min candles)")
        else:
            # Stock mode: use full universe with daily candles (original behaviour)
            portfolio = get_watchlist(
                include_nifty50=True,
                include_next50=True,
                include_momentum=True,
                include_intraday=True,
                risk_levels=["low", "medium", "high"],
                max_stocks=100
            )
            print(f"[UNIVERSE] Stock mode: loaded {len(portfolio)} stocks (daily candles)")
    except Exception as e:
        print(f"[WARN] Could not load stock_universe.py: {e}. Using fallback watchlist.")
        portfolio = [
            {"symbol": "NSE_EQ|INE467B01029", "name": "TCS",      "strategy": "ma_crossover",  "interval": active_interval},
            {"symbol": "NSE_EQ|INE002A01018", "name": "RELIANCE", "strategy": "rsi_reversion", "interval": active_interval},
            {"symbol": "NSE_EQ|INE009A01021", "name": "INFY",     "strategy": "breakout",      "interval": active_interval},
        ]

    print(f"📋 Processing {len(portfolio)} strategies...")
    trades_taken = 0

    for item in portfolio:
        symbol = item["symbol"]
        strategy = item["strategy"]
        interval = item["interval"]
        name = item["name"]

        print(f"\n🔎 Analyzing {name} ({strategy})...")
        
        # Step 3: Fetch data
        # Daily data is always fetched for AI daily context / fallback
        df_ai = fetch_historical_data(symbol, interval="day", days=200)

        # For intraday mode, fetch 30-min candles for both strategies AND AI
        if is_intraday or interval != "day":
            df = fetch_historical_data(symbol, interval="30minute", days=30)
            df_for_ai = df           # use intraday candles for AI too
        else:
            df = df_ai               # reuse daily data for both
            df_for_ai = df_ai

        if df.empty or df_ai.empty:
            continue

        # Step 4: Run ALL Strategies for Aggregated Signal
        print(f"   📊 Running 19 strategies...")
        try:
            aggregated = StrategyEngine.get_all_signals(df)
            strategy_signal = aggregated['consensus']
            strategy_confidence = aggregated['confidence']
            current_price = df.iloc[-1]["close"]
            
            print(f"   📊 Strategy Consensus: {strategy_signal} ({aggregated['buy_count']}B/{aggregated['sell_count']}S/{aggregated['hold_count']}H)")

            # Step 5: AI Enhancement (if available)
            final_signal = strategy_signal
            confidence = strategy_confidence
            ai_decision = None   # sentinel — avoids UnboundLocalError if AI block is skipped

            if ai_engine:
                try:
                    # Full Ensemble Mode: LSTM (40%) + Sentiment (25%) + Strategy (35%) [boosted]
                    stock_name = symbol.split('|')[0].replace('NSE_EQ:', '')
                    
                    # Enable RL if self-learning is active
                    use_rl_agent = rl_manager is not None and RLConfig.ENABLE_LIVE_LEARNING
                    
                    ai_decision = ai_engine.make_ensemble_decision(
                        df_for_ai,           # 30-min in intraday mode, daily in stock mode
                        strategy_signal,
                        f"aggregated_{aggregated['buy_count']}B_{aggregated['sell_count']}S",
                        stock_name=stock_name,
                        use_sentiment=True,
                        use_rl=use_rl_agent,
                        rl_agent=rl_manager.agent if rl_manager else None,
                        is_intraday=is_intraday   # <-- routes to intraday LSTM if trained
                    )
                    
                    # Ensemble decision
                    ensemble_signal = ai_decision.get('action', ai_decision.get('signal', strategy_signal))
                    ensemble_confidence = ai_decision['confidence']
                    
                    # FIRM DECISION: Combine ensemble with aggregated strategy voting
                    # If both agree, boost confidence significantly
                    if ensemble_signal == strategy_signal and ensemble_signal in ['BUY', 'SELL']:
                        final_signal = ensemble_signal
                        confidence = min((ensemble_confidence + strategy_confidence) / 1.5, 0.95)
                        print(f"   🎯 FIRM DECISION: {final_signal} (AI + 15 Strategies AGREE)")
                    elif aggregated['buy_count'] >= 10 or aggregated['sell_count'] >= 10:
                        # Strong strategy consensus (10+ strategies agree)
                        final_signal = strategy_signal
                        confidence = strategy_confidence
                        print(f"   🎯 FIRM DECISION: {final_signal} (Strong Strategy Consensus: {max(aggregated['buy_count'], aggregated['sell_count'])}/15)")
                    else:
                        # Trust ensemble when signals differ
                        final_signal = ensemble_signal
                        confidence = ensemble_confidence * 0.8  # Slightly reduce for disagreement
                        print(f"   🎯 Ensemble Decision: {final_signal} (confidence: {confidence:.0%})")
                    
                    print(f"      Models: {', '.join(ai_decision.get('models_used', []))}")
                    print(f"      Reason: {ai_decision['reason']}")
                    
                    if ai_decision.get('ai_prediction'):
                        pred = ai_decision['ai_prediction']
                        if pred.get('predicted_price'):
                            print(f"      Predicted Price: ₹{pred['predicted_price']:.2f} ({pred.get('price_change_pct', 0):+.2f}%)")
                except Exception as e:
                    print(f"   ⚠️ AI decision error: {e}")
                    print(f"   Using aggregated strategy signal: {strategy_signal}")

            # Step 6: Execute with confidence threshold
            MIN_CONFIDENCE = 0.35  # Paper mode: trade if confidence > 35%
            
            # final_signal is determined above; note that there is no hard cap on the
            # number of trades per cycle – we will attempt an order for every symbol
            # whose strategy/AI output returns BUY/SELL.  Qty is computed using
            # capital_allocation_pct which by default is 100%, so the first trade can
            # consume most of the cash and may leave insufficient funds for later
            # symbols.  This is why you often only see a single trade: the remainder of
            # the universe either produced HOLD signals or there wasn’t enough cash left.
            if final_signal in ["BUY", "SELL"] and confidence >= MIN_CONFIDENCE:
                # Divide capital by max concurrent positions so the first BUY
                # does not consume all cash, leaving later symbols with qty=0.
                _max_pos = PaperTradingConfig.MAX_OPEN_POSITIONS if PAPER_TRADING_AVAILABLE else 5
                capital_pct = (
                    _mode_mgr.config.get('capital_allocation_pct', 75) / 100.0 / _max_pos
                    if _mode_mgr else 0.15
                )
                qty = calculate_quantity(symbol, current_price, capital_per_trade=capital_pct)
                if qty > 0:
                    # --- Risk check (non-blocking: skip trade if limits exceeded) ---
                    if risk_mgr is not None:
                        try:
                            _port_val = get_available_funds()
                            _can_trade, _risk_reason = risk_mgr.validate_trade(
                                symbol=name,
                                side=final_signal,
                                quantity=qty,
                                price=current_price,
                                current_portfolio_value=max(_port_val, 1.0)
                            )
                            if not _can_trade:
                                print(f"   🚫 Risk check blocked: {_risk_reason}")
                                continue
                        except Exception as _re:
                            print(f"   ⚠️ Risk manager error (skipping check): {_re}")
                    # --- End risk check ---
                    print(f"   ✅ Executing {final_signal} order for {symbol} @ ₹{current_price:.2f} (confidence: {confidence:.0%})")
                    
                    # Prepare AI metadata for logging
                    models_list = ai_decision.get('models_used', []) if ai_decision is not None else []
                    models_str = ','.join(models_list) if models_list else ''
                    
                    place_order_ai(
                        symbol, final_signal, qty, current_price,
                        strategy=f"aggregated_{aggregated['buy_count']}B_{aggregated['sell_count']}S",
                        stock_name=name,
                        ai_enabled=bool(ai_engine),
                        confidence=confidence,
                        models_used=models_str,
                        interval=interval          # ← pass interval for MIS/CNC decision
                    )
                    trades_taken += 1
                    
                    # Send Telegram notification for trade started
                    if TELEGRAM_ENABLED:
                        send_trade_started(
                            symbol=name,
                            side=final_signal,
                            quantity=qty,
                            price=current_price,
                            strategy=f"aggregated_{aggregated['buy_count']}B_{aggregated['sell_count']}S",
                            confidence=confidence
                        )
                    
                    # SELF-LEARNING: Track BUY entry for feedback loop
                    if outcome_tracker and rl_manager and final_signal == 'BUY':
                        try:
                            if ai_engine and hasattr(ai_engine, 'feature_engineer'):
                                features = ai_engine.feature_engineer.prepare_features(df_ai)
                                if len(features) > 0:
                                    state = features.iloc[-1].values
                                    action = 1  # BUY
                                    outcome_tracker.record_trade_entry(
                                        symbol=symbol,
                                        action=action,
                                        state=state,
                                        price=current_price,
                                        quantity=qty
                                    )
                                    print(f"   🧠 Tracked entry for self-learning")
                        except Exception as e:
                            print(f"   ⚠️ Self-learning tracking error: {e}")

                    # SELF-LEARNING: Record SELL exit for RL feedback loop
                    # (moved here from 'else/No Action' branch where it was unreachable)
                    if outcome_tracker and rl_manager and final_signal == 'SELL':
                        if outcome_tracker.has_open_position(symbol):
                            try:
                                experience = outcome_tracker.record_trade_exit(
                                    symbol=symbol,
                                    exit_price=current_price
                                )
                                if experience:
                                    if ai_engine and hasattr(ai_engine, 'feature_engineer'):
                                        features = ai_engine.feature_engineer.prepare_features(df_ai)
                                        if len(features) > 0:
                                            next_state = features.iloc[-1].values
                                            experience['next_state'] = next_state
                                            rl_manager.store_experience(
                                                state=experience['state'],
                                                action=experience['action'],
                                                reward=experience['reward'],
                                                next_state=next_state,
                                                done=True
                                            )
                                            store_rl_experience(experience)
                                            metrics = rl_manager.train_if_ready()
                                            if metrics:
                                                print(f"   🎓 RL Training: Loss={metrics['avg_loss']:.4f}, ε={metrics['epsilon']:.3f}")
                                            print(f"   🧠 Self-learning: Learned from trade outcome")
                                            if TELEGRAM_ENABLED:
                                                entry_price = experience.get('entry_price', 0)
                                                exit_pnl = experience.get('profit', 0)
                                                send_trade_ended(
                                                    symbol=outcome_tracker.open_positions.get(symbol, {}).get('stock_name', symbol),
                                                    side='BUY',
                                                    quantity=experience.get('quantity', 0),
                                                    entry_price=entry_price,
                                                    exit_price=current_price,
                                                    pnl=exit_pnl
                                                )
                            except Exception as e:
                                print(f"   ⚠️ Self-learning feedback error: {e}")
                else:
                    print("   ⚠️ Insufficient funds for trade.")
            elif confidence < MIN_CONFIDENCE:
                print(f"   ⏳ Confidence too low ({confidence:.0%} < {MIN_CONFIDENCE:.0%}). Skipping trade.")
            else:
                print("   ⏳ No Action.")
                
                
        except Exception as e:
            print(f"   ❌ Strategy Error: {e}")

    # Step 7: Final Report and Database Logging
    print("\n📊 Generating P&L Report...")
    pnl, open_pos = get_pnL_summary()
    ending_balance = get_available_funds()
    
    mode = "AI-Enhanced (Self-Learning)" if (ai_engine and rl_manager) else ("AI-Enhanced" if ai_engine else "Rule-Based")
    summary_msg = (
        f"💰 Daily Summary ({mode} Mode)\n"
        f"------------------\n"
        f"💵 Balance: ₹{ending_balance:.2f}\n"
        f"📉 Open Pos: {open_pos}\n"
        f"📊 Day's P&L: {'+' if pnl >=0 else ''}₹{pnl:.2f}\n"
        f"✅ Trades: {trades_taken}"
    )
    print(summary_msg)
    
    # Send Telegram daily P&L notification
    if TELEGRAM_ENABLED:
        send_daily_pnl(
            total_pnl=pnl,
            trades_count=trades_taken,
            starting_balance=starting_balance,
            ending_balance=ending_balance,
            open_positions=open_pos,
            mode=mode
        )
    
    # Display self-learning statistics
    if outcome_tracker and rl_manager:
        print("\n🧠 Self-Learning Statistics:")
        stats = outcome_tracker.get_statistics()
        metrics = rl_manager.get_learning_metrics()
        print(f"   Tracked Trades: {stats['total_trades']}")
        print(f"   Win Rate: {stats['win_rate']:.1f}%")
        print(f"   Total Profit: ₹{stats['total_profit']:.2f}")
        print(f"   Open Positions: {stats['open_positions']}")
        print(f"   RL Buffer: {metrics['buffer_size']}/{RLConfig.BUFFER_SIZE}")
        print(f"   Training Steps: {metrics['training_steps']}")
        print(f"   Epsilon: {metrics['epsilon']:.3f}")
        print(f"   Avg Reward: {metrics['avg_recent_reward']:.2f}")
        if RLConfig.ENABLE_LIVE_LEARNING:
            print("   ⚠️ LIVE LEARNING ENABLED")
        else:
            print("   ✓ Learning disabled (safe mode)")
    
    # Log daily summary to database
    try:
        from datetime import date
        summary_data = {
            'date': date.today(),
            'starting_balance': starting_balance,
            'ending_balance': ending_balance,
            'total_pnl': pnl,
            'realized_pnl': 0,
            'unrealized_pnl': pnl,
            'total_trades': trades_taken,
            'buy_trades': trades_taken, # Since we only count entries in this loop
            'sell_trades': 0, # Exits are handled separately by RL logic but not counted in this simple loop variable
            'total_capital_used': 0,
            'open_positions': open_pos,
            'ai_trades': trades_taken if ai_engine else 0,
            'rule_based_trades': 0 if ai_engine else trades_taken,
            'notes': f"{mode} mode"
        }
        update_daily_summary(summary_data)
    except Exception as e:
        print(f"⚠️ Failed to log daily summary: {e}")

    print("\n✅ All strategies executed.\n")
    return True


if __name__ == "__main__":
    main_ai_enhanced()
