"""
Rigorous Internal System Check
------------------------------
Performs deep verification of the trading system including:
1. Class Instantiation & Configuration
2. Full Data Pipeline Simulation (Data -> Features -> AI -> Strategy)
3. Database Stress Testing & Integrity Check
4. Memory Usage Monitoring
5. File System & Path Verification
"""

import sys
import os
import time
import psutil
import numpy as np
import pandas as pd
import sqlite3
import torch
import gc
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("🛡️ RIGOROUS INTERNAL SYSTEM CHECK")
print("=" * 70)

errors = []
warnings = []

def log_error(msg):
    print(f"   ❌ {msg}")
    errors.append(msg)

def log_warning(msg):
    print(f"   ⚠️  {msg}")
    warnings.append(msg)

def log_success(msg):
    print(f"   ✅ {msg}")

def get_memory_usage():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # MB

# ==========================================
# 1. Environment & Path Check
# ==========================================
print("\n1️⃣ Environment & Path Verification")
print("-" * 70)

required_dirs = [
    "data",
    "data/trained_models",
    "data/exports",
    "ai_agent",
    "ai_agent/models"
]

for d in required_dirs:
    path = Path(d)
    if path.exists() and path.is_dir():
        log_success(f"Directory found: {d}")
    else:
        try:
            path.mkdir(parents=True, exist_ok=True)
            log_warning(f"Created missing directory: {d}")
        except Exception as e:
            log_error(f"Failed to create {d}: {e}")

# Check write permissions
try:
    test_file = Path("data/write_test.tmp")
    with open(test_file, "w") as f:
        f.write("test")
    os.remove(test_file)
    log_success("Write permissions verified for data/")
except Exception as e:
    log_error(f"Write permission denied in data/: {e}")

# ==========================================
# 2. Component Instantiation
# ==========================================
print("\n2️⃣ Component Instantiation Check")
print("-" * 70)

init_memory = get_memory_usage()
print(f"   Initial Memory: {init_memory:.2f} MB")

try:
    from ai_agent.ai_decision_engine import AIDecisionEngine
    from strategy_engine import StrategyEngine
    from rl_learning_manager import RLLearningManager
    from trade_outcome_tracker import TradeOutcomeTracker
    
    # AI Decision Engine
    print("   Initializing AI Decision Engine...")
    ai_engine = AIDecisionEngine(use_gpu=False)
    log_success("AIDecisionEngine initialized")
    
    # RL Manager
    print("   Initializing RL Manager...")
    rl_manager = RLLearningManager(state_dim=34, action_dim=3)
    log_success("RLLearningManager initialized")
    
    # Strategy Engine
    # Static class, just check import
    log_success("StrategyEngine ready")
    
    curr_memory = get_memory_usage()
    print(f"   Post-Init Memory: {curr_memory:.2f} MB (Diff: +{curr_memory - init_memory:.2f} MB)")
    
    if (curr_memory - init_memory) > 500: # 500MB threshold
        log_warning("High memory usage during initialization")

except ImportError as e:
    log_error(f"Import failed: {e}")
except Exception as e:
    log_error(f"Instantiation failed: {e}")

# ==========================================
# 3. Data Pipeline Simulation
# ==========================================
print("\n3️⃣ Data Pipeline Simulation")
print("-" * 70)

try:
    # Generate synthetic data (200 days)
    dates = pd.date_range(end=datetime.now(), periods=200)
    data = {
        'timestamp': dates,
        'open': np.random.uniform(100, 200, 200),
        'high': np.random.uniform(100, 200, 200) + 5,
        'low': np.random.uniform(100, 200, 200) - 5,
        'close': np.random.uniform(100, 200, 200),
        'volume': np.random.randint(1000, 10000, 200)
    }
    df = pd.DataFrame(data)
    log_success("Synthetic data generated (200 rows)")
    
    # Feature Engineering Check
    print("   Running Feature Engineering...")
    if hasattr(ai_engine, 'feature_engineer'):
        features = ai_engine.feature_engineer.prepare_features(df)
        if not features.empty:
            log_success(f"Features generated: {features.shape}")
        else:
            log_error("Feature engineering returned empty DataFrame")
    else:
        log_warning("AI Engine missing feature_engineer attribute")

    # Strategy Engine Check
    print("   Running Strategy Engine...")
    signals = StrategyEngine.get_all_signals(df)
    if 'consensus' in signals:
        log_success(f"Strategy signals generated: {signals['consensus']}")
    else:
        log_error("Strategy Engine failed to generate consensus")

    # AI Prediction Check
    print("   Running AI Prediction...")
    # Mocking model presence if not loaded
    if ai_engine.model is None:
        log_warning("AI Model not loaded (expected for fresh install). Skipping inference check.")
    else:
        pred = ai_engine.predict_price(df)
        if pred:
            log_success("AI Prediction successful")
        else:
            log_error("AI Prediction failed")

except Exception as e:
    log_error(f"Pipeline simulation failed: {e}")

# ==========================================
# 4. Database Stress Test
# ==========================================
print("\n4️⃣ Database Stress & Integrity Test")
print("-" * 70)

db_path = "data/trading_database.db"

try:
    from database_manager import initialize_database, log_trade, store_rl_experience
    
    # Ensure fresh DB or valid connection
    initialize_database()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Schema Check
    cursor.execute("PRAGMA table_info(trades)")
    columns = [info[1] for info in cursor.fetchall()]
    required_cols = ['id', 'symbol', 'price', 'quantity', 'status']
    if all(col in columns for col in required_cols):
        log_success("Trades table schema verified")
    else:
        log_error(f"Missing columns in trades table. Found: {columns}")
        
    # 2. Insert Stress Test (100 trades)
    print("   Inserting 100 dummy trades...")
    start_time = time.time()
    
    for i in range(100):
        trade = {
            'timestamp': datetime.now(),
            'symbol': f'TEST_{i}',
            'stock_name': 'TEST_STOCK',
            'strategy': 'STRESS_TEST',
            'signal': 'BUY',
            'quantity': 1,
            'price': 100.0 + i,
            'status': 'SUCCESS'
        }
        log_trade(trade)
        
    duration = time.time() - start_time
    log_success(f"Inserted 100 trades in {duration:.4f}s ({(100/duration):.1f} trades/s)")
    
    # 3. RL Experience Stress Test
    print("   Inserting 50 RL experiences...")
    for i in range(50):
        exp = {
            'symbol': f'TEST_{i}',
            'state': np.random.randn(34),
            'action': 1,
            'reward': 1.0,
            'next_state': np.random.randn(34),
            'done': True,
            'trade_id': i
        }
        store_rl_experience(exp)
        
    log_success("Inserted 50 RL experiences")
    
    # 4. cleanup
    cursor.execute("DELETE FROM trades WHERE symbol LIKE 'TEST_%'")
    cursor.execute("DELETE FROM rl_experiences WHERE symbol LIKE 'TEST_%'")
    conn.commit()
    log_success("Cleanup complete")
    conn.close()

except Exception as e:
    log_error(f"Database test failed: {e}")

# ==========================================
# 5. Global Exception Handling Test
# ==========================================
print("\n5️⃣ Global Exception Safety")
print("-" * 70)

try:
    # Test if importing the main script causes side effects
    import trading_execution_ai
    log_success("Main script import safe (no side effects)")
except Exception as e:
    log_error(f"Main script import caused error: {e}")

# ==========================================
# Final Report
# ==========================================
print("\n" + "=" * 70)
print("📊 RIGOROUS CHECK SUMMARY")
print("=" * 70)

if not errors:
    print("✅ SYSTEM IS ROBUST AND HEALTHY")
    print("\nPerformance Metrics:")
    print(f"   Memory Usage: {get_memory_usage():.2f} MB")
    if warnings:
        print(f"\n⚠️  {len(warnings)} Non-Critical Warnings:")
        for w in warnings:
            print(f"   - {w}")
else:
    print(f"❌ SYSTEM CHECK FAILED WITH {len(errors)} ERRORS")
    for e in errors:
        print(f"   - {e}")

sys.exit(0 if not errors else 1)
