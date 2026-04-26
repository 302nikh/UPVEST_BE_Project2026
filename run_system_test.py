"""
run_system_test.py
==================
Full system test after intraday training.
Run: python run_system_test.py
"""

import sys
import os
import traceback

PASS = []
FAIL = []
WARN = []

def ok(msg):
    print(f"  PASS  {msg}")
    PASS.append(msg)

def fail(msg, err=""):
    print(f"  FAIL  {msg}")
    if err:
        print(f"        -> {err}")
    FAIL.append(msg)

def warn(msg):
    print(f"  WARN  {msg}")
    WARN.append(msg)

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ─────────────────────────────────────────────────────────────
section("TEST 1: Model Files")
# ─────────────────────────────────────────────────────────────
model_files = {
    "data/trained_models/lstm_intraday.pth":        "Intraday LSTM model",
    "data/trained_models/lstm_intraday_scaler.pkl": "Intraday scaler",
    "data/trained_models/lstm_intraday_config.pkl": "Intraday config",
}
for path, label in model_files.items():
    if os.path.exists(path):
        size_kb = os.path.getsize(path) // 1024
        ok(f"{label}: {path} ({size_kb} KB)")
    else:
        # Daily model is optional (may not be trained yet)
        fail(f"{label} MISSING: {path}")

daily_files = {
    "data/trained_models/lstm_best.pth":        "Daily LSTM model",
    "data/trained_models/lstm_best_scaler.pkl": "Daily scaler",
}
for path, label in daily_files.items():
    if os.path.exists(path):
        ok(f"{label} found")
    else:
        warn(f"{label} not found (train with: python ai_agent/model_trainer_optimized.py)")


# ─────────────────────────────────────────────────────────────
section("TEST 2: Core Imports")
# ─────────────────────────────────────────────────────────────
imports_to_test = [
    ("pandas",                    "pandas"),
    ("numpy",                     "numpy"),
    ("torch",                     "torch"),
    ("sklearn",                   "scikit-learn"),
    ("fastapi",                   "fastapi"),
    ("uvicorn",                   "uvicorn"),
    ("requests",                  "requests"),
    ("nltk",                      "nltk"),
    ("ta",                        "ta (technical analysis)"),
    ("openpyxl",                  "openpyxl"),
    ("psutil",                    "psutil"),
]
for mod, label in imports_to_test:
    try:
        __import__(mod)
        ok(label)
    except ImportError as e:
        fail(label, str(e))


# ─────────────────────────────────────────────────────────────
section("TEST 3: Project Module Imports")
# ─────────────────────────────────────────────────────────────
project_modules = [
    ("trading_mode_manager",            "TradingModeManager"),
    ("trading_execution",               "get_product_type helper"),
    ("ai_agent.feature_engineering",    "FeatureEngineer (with intraday features)"),
    ("ai_agent.models.lstm_predictor",  "LSTMPredictor"),
    ("ai_agent.ai_decision_engine",     "AIDecisionEngine (dual-model)"),
    ("strategy_engine",                 "StrategyEngine"),
    ("paper_trading_orders",            "paper_trading_orders"),
]
for mod, label in project_modules:
    try:
        __import__(mod)
        ok(label)
    except Exception as e:
        fail(label, str(e)[:120])


# ─────────────────────────────────────────────────────────────
section("TEST 4: intraday features (VWAP etc.)")
# ─────────────────────────────────────────────────────────────
try:
    import pandas as pd
    import numpy as np
    from ai_agent.feature_engineering import FeatureEngineer

    # Synthetic 30-min data (1 trading day = 13 candles, give 100 candles)
    n = 200
    prices = 1500 + np.cumsum(np.random.randn(n) * 2)
    ts = pd.date_range("2026-02-20 09:15", periods=n, freq="30min")
    df_dummy = pd.DataFrame({
        "time":   ts,
        "open":   prices - 1,
        "high":   prices + 3,
        "low":    prices - 3,
        "close":  prices,
        "volume": np.random.randint(100000, 500000, n)
    })

    fe = FeatureEngineer(lookback_period=30)

    # Daily features (is_intraday=False) - original behaviour
    df_daily = fe.prepare_features(df_dummy, is_intraday=False)
    assert "VWAP" not in df_daily.columns, "VWAP should NOT be in daily features"
    ok("Daily features: VWAP correctly excluded")

    # Intraday features (is_intraday=True) - new behaviour
    df_intra = fe.prepare_features(df_dummy, is_intraday=True)
    required = ["VWAP", "VWAP_distance", "session_hour", "session_progress", "intraday_return", "rel_volume"]
    missing = [c for c in required if c not in df_intra.columns]
    if missing:
        fail(f"Intraday features missing: {missing}")
    else:
        ok(f"Intraday features: all 6 present ({', '.join(required)})")

except Exception as e:
    fail("FeatureEngineer intraday test", traceback.format_exc(limit=3))


# ─────────────────────────────────────────────────────────────
section("TEST 5: AI Engine Dual-Model Loading")
# ─────────────────────────────────────────────────────────────
try:
    from ai_agent.ai_decision_engine import AIDecisionEngine

    engine = AIDecisionEngine()

    # Intraday model
    if engine.intraday_model is not None:
        ok("Intraday LSTM model loaded into AIDecisionEngine")
    else:
        fail("Intraday model NOT loaded (check lstm_intraday.pth)")

    # Daily model (optional)
    if engine.model is not None:
        ok("Daily LSTM model loaded into AIDecisionEngine")
    else:
        warn("Daily LSTM model not found (run model_trainer_optimized.py for daily model)")

except Exception as e:
    fail("AIDecisionEngine loading", traceback.format_exc(limit=3))


# ─────────────────────────────────────────────────────────────
section("TEST 6: Intraday Prediction (Dry Run)")
# ─────────────────────────────────────────────────────────────
try:
    from ai_agent.ai_decision_engine import AIDecisionEngine
    import pandas as pd, numpy as np

    engine = AIDecisionEngine()

    if engine.intraday_model is not None:
        # Build synthetic 30-min data (need >= 78 candles for lookback)
        n = 120
        prices = 2500 + np.cumsum(np.random.randn(n) * 3)
        ts = pd.date_range("2026-02-20 09:15", periods=n, freq="30min")
        df_test = pd.DataFrame({
            "time":   ts,
            "open":   prices - 1,
            "high":   prices + 3,
            "low":    prices - 3,
            "close":  prices,
            "volume": np.random.randint(100000, 500000, n)
        })

        result = engine.predict_price(df_test, is_intraday=True)

        if result.get("error"):
            fail(f"Intraday prediction error: {result['error']}")
        else:
            pred  = result.get("predicted_price", 0) or 0
            curr  = result.get("current_price", 0) or 0
            model = result.get("model_used", "?")
            dirn  = result.get("direction", "?")
            conf  = result.get("confidence", 0) or 0
            ok(f"Prediction OK | Model: {model} | Direction: {dirn} | Confidence: {conf:.2f}")
            ok(f"Current: {curr:.2f} | Predicted: {pred:.2f}")
    else:
        warn("Skipping intraday prediction test (model not loaded)")

except Exception as e:
    fail("Intraday prediction dry run", traceback.format_exc(limit=5))


# ─────────────────────────────────────────────────────────────
section("TEST 7: Mode Manager")
# ─────────────────────────────────────────────────────────────
try:
    from trading_mode_manager import TradingModeManager

    mgr = TradingModeManager()
    status = mgr.get_status()

    ok(f"Execution mode : {status['mode'].upper()}")
    ok(f"Strategy mode  : {status['strategy_mode'].upper()}")
    ok(f"Active interval: {status['active_interval']}")
    ok(f"Product type   : {status['product_type']}")

except Exception as e:
    fail("TradingModeManager", traceback.format_exc(limit=3))


# ─────────────────────────────────────────────────────────────
section("TEST 8: get_product_type helper")
# ─────────────────────────────────────────────────────────────
try:
    from trading_execution import get_product_type

    cases = [
        ("day",       "ma_crossover",  "D"),
        ("30minute",  "vwap",          "I"),
        ("30minute",  "ma_crossover",  "I"),
        ("day",       "vwap",          "I"),
        ("1minute",   "breakout",      "I"),
        ("day",       "rsi_reversion", "D"),
    ]
    all_ok = True
    for interval, strategy, expected in cases:
        got = get_product_type(interval, strategy)
        if got == expected:
            ok(f"interval={interval:<10} strategy={strategy:<15} -> {got} (CNC/Delivery)" if got=='D' else
               f"interval={interval:<10} strategy={strategy:<15} -> {got} (MIS/Intraday)")
        else:
            fail(f"interval={interval}, strategy={strategy}: expected {expected}, got {got}")
            all_ok = False

except Exception as e:
    fail("get_product_type", traceback.format_exc(limit=3))


# ─────────────────────────────────────────────────────────────
section("TEST 9: Backend API Health")
# ─────────────────────────────────────────────────────────────
try:
    import requests as rq
    r = rq.get("http://localhost:5000/api/status", timeout=3)
    data = r.json()
    if data.get("status") == "online":
        ok(f"Backend API online (v{data.get('version','?')})")
    else:
        fail("Backend API returned unexpected status", str(data))

    r2 = rq.get("http://localhost:5000/api/trading-mode/strategy", timeout=3)
    d2 = r2.json()
    ok(f"Strategy mode API: {d2.get('strategy_mode','?')} | "
       f"interval={d2.get('active_interval','?')} | "
       f"product={d2.get('product_type','?')}")

except Exception as e:
    fail("Backend API", str(e))


# ─────────────────────────────────────────────────────────────
section("SUMMARY")
# ─────────────────────────────────────────────────────────────
total = len(PASS) + len(FAIL) + len(WARN)
print(f"\n  PASSED : {len(PASS)}")
print(f"  FAILED : {len(FAIL)}")
print(f"  WARNINGS: {len(WARN)}")
print(f"  TOTAL  : {total}")

if FAIL:
    print("\n  FAILED TESTS:")
    for f in FAIL:
        print(f"    - {f}")

if WARN:
    print("\n  WARNINGS:")
    for w in WARN:
        print(f"    - {w}")

if not FAIL:
    print("\n  ALL TESTS PASSED!")
else:
    print("\n  SOME TESTS FAILED. See details above.")
    sys.exit(1)
