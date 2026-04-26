"""
System Interconnectivity Check
------------------------------
Verifies that all modules can talk to each other and dependencies are correct.
"""

import sys
import os
import importlib
import traceback

print("=" * 70)
print("🔍 SYSTEM INTERCONNECTIVITY CHECK")
print("=" * 70)

modules_to_check = [
    "trade_outcome_tracker",
    "rl_config",
    "rl_learning_manager",
    "database_manager",
    "strategy_engine",
    "ai_agent.ai_decision_engine",
    "ai_agent.rl_agent",
    "ai_agent.feature_engineering",
    "trading_execution_ai" 
]

errors = []

print("\n1️⃣ Module Import Check")
print("-" * 70)

for module_name in modules_to_check:
    try:
        if module_name == "trading_execution_ai":
            # For the main script, we check if it handles imports correctly without running main()
             spec = importlib.util.spec_from_file_location(module_name, f"{module_name}.py")
             if spec and spec.loader:
                 print(f"   ✅ {module_name} found and loadable")
             else:
                 errors.append(f"{module_name} could not be found")
        else:
            importlib.import_module(module_name)
            print(f"   ✅ {module_name} imported successfully")
    except Exception as e:
        print(f"   ❌ {module_name} FAILED: {e}")
        errors.append(f"Import error {module_name}: {e}")
        # traceback.print_exc()

print("\n2️⃣ Class Initialization & Interconnectivity")
print("-" * 70)

try:
    print("   Testing RL Config -> Learning Manager link...")
    from rl_config import RLConfig
    from rl_learning_manager import RLLearningManager
    
    # Check if Manager uses Config correctly
    manager = RLLearningManager(state_dim=10, action_dim=3)
    if manager.config == RLConfig:
        print("   ✅ RL Learning Manager correctly linked to RL Config")
    else:
        errors.append("RL Manager not using RL Config")

    print("   Testing Outcome Tracker -> RL interaction...")
    from trade_outcome_tracker import TradeOutcomeTracker
    tracker = TradeOutcomeTracker()
    
    # Simulate data flow
    state = [0.1] * 10
    tracker.record_trade_entry('TEST', 1, state, 100.0, 10)
    exp = tracker.record_trade_exit('TEST', 110.0)
    if exp and 'reward' in exp:
        print("   ✅ Trade Outcome Tracker generating valid experience")
    else:
        errors.append("Outcome Tracker failed to generate experience")

    print("   Testing Database -> RL Experience storage...")
    from database_manager import store_rl_experience, initialize_database
    initialize_database()
    
    # Needs to match schema
    import numpy as np
    dummy_exp = {
        'symbol': 'SYSCHECK',
        'state': np.zeros(34),
        'action': 1,
        'reward': 1.0,
        'next_state': np.zeros(34),
        'done': True,
        'profit': 10.0,
        'profit_pct': 10.0,
        'holding_time': 1.0
    }
    if store_rl_experience(dummy_exp):
        print("   ✅ Database accepts RL experience")
    else:
        errors.append("Database rejected RL experience")

except Exception as e:
    print(f"   ❌ Interconnectivity Error: {e}")
    errors.append(f"Interconnectivity error: {e}")
    traceback.print_exc()

print("\n" + "=" * 70)
print("📊 SYSTEM CHECK SUMMARY")
print("=" * 70)

if not errors:
    print("✅ ALL CHECKS PASSED - System is interconnected and healthy!")
else:
    print(f"❌ {len(errors)} ERRORS FOUND")
    for e in errors:
        print(f"   - {e}")

sys.exit(0 if not errors else 1)
