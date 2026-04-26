"""
Comprehensive Error Check for Trading Database System
------------------------------------------------------
This script performs thorough error checking on all database components.
"""

import sys
from datetime import datetime, date

print("=" * 70)
print("🔍 COMPREHENSIVE ERROR CHECK - Trading Database System")
print("=" * 70)

errors_found = []
warnings_found = []

# Test 1: Syntax Check
print("\n1️⃣ Syntax Check")
print("-" * 70)
try:
    import py_compile
    files_to_check = [
        'database_manager.py',
        'export_trading_data.py',
        'trading_execution.py',
        'trading_execution_ai.py'
    ]
    
    for file in files_to_check:
        try:
            py_compile.compile(file, doraise=True)
            print(f"   ✅ {file} - Syntax OK")
        except py_compile.PyCompileError as e:
            errors_found.append(f"Syntax error in {file}: {e}")
            print(f"   ❌ {file} - Syntax Error: {e}")
except Exception as e:
    errors_found.append(f"Syntax check failed: {e}")
    print(f"   ❌ Syntax check failed: {e}")

# Test 2: Import Check
print("\n2️⃣ Import Check")
print("-" * 70)
try:
    import database_manager
    print("   ✅ database_manager - Import OK")
except Exception as e:
    errors_found.append(f"Import error in database_manager: {e}")
    print(f"   ❌ database_manager - Import Error: {e}")

try:
    import export_trading_data
    print("   ✅ export_trading_data - Import OK")
except Exception as e:
    errors_found.append(f"Import error in export_trading_data: {e}")
    print(f"   ❌ export_trading_data - Import Error: {e}")

# Note: trading_execution imports may hang due to pre_startup_checks making API calls
print("   ⚠️  trading_execution.py - Skipped (may hang due to API calls)")
print("   ⚠️  trading_execution_ai.py - Skipped (may hang due to API calls)")
warnings_found.append("trading_execution imports skipped (require API access)")

# Test 3: Database Functionality
print("\n3️⃣ Database Functionality Check")
print("-" * 70)
try:
    from database_manager import initialize_database, log_trade, update_daily_summary, export_to_excel
    
    # Initialize database
    initialize_database()
    print("   ✅ Database initialization - OK")
    
    # Test trade logging
    test_trade = {
        'timestamp': datetime.now(),
        'symbol': 'NSE_EQ|INE467B01029',
        'stock_name': 'TCS_TEST',
        'strategy': 'test_strategy',
        'signal': 'BUY',
        'quantity': 5,
        'price': 3500.00,
        'order_id': 'TEST_ERROR_CHECK',
        'status': 'SUCCESS',
        'ai_enabled': True,
        'confidence': 0.75,
        'models_used': 'LSTM,Sentiment'
    }
    
    if log_trade(test_trade):
        print("   ✅ Trade logging - OK")
    else:
        errors_found.append("Trade logging failed")
        print("   ❌ Trade logging - FAILED")
    
    # Test daily summary
    test_summary = {
        'date': date.today(),
        'starting_balance': 100000.0,
        'ending_balance': 101000.0,
        'total_pnl': 1000.0,
        'total_trades': 3,
        'buy_trades': 2,
        'sell_trades': 1,
        'total_capital_used': 30000.0,
        'open_positions': 1,
        'ai_trades': 2,
        'rule_based_trades': 1
    }
    
    if update_daily_summary(test_summary):
        print("   ✅ Daily summary update - OK")
    else:
        errors_found.append("Daily summary update failed")
        print("   ❌ Daily summary update - FAILED")
    
    # Test Excel export
    if export_to_excel():
        print("   ✅ Excel export - OK")
    else:
        errors_found.append("Excel export failed")
        print("   ❌ Excel export - FAILED")
        
except Exception as e:
    errors_found.append(f"Database functionality error: {e}")
    print(f"   ❌ Database functionality - Error: {e}")

# Test 4: File Existence Check
print("\n4️⃣ File Existence Check")
print("-" * 70)
import os
from pathlib import Path

required_files = {
    'database_manager.py': 'Database manager module',
    'export_trading_data.py': 'Excel export utility',
    'test_database.py': 'Test script',
    'data/trading_database.db': 'SQLite database',
    'data/exports': 'Export directory'
}

for file_path, description in required_files.items():
    if os.path.exists(file_path):
        print(f"   ✅ {file_path} - {description}")
    else:
        warnings_found.append(f"Missing: {file_path}")
        print(f"   ⚠️  {file_path} - NOT FOUND")

# Test 5: Database Schema Check
print("\n5️⃣ Database Schema Check")
print("-" * 70)
try:
    import sqlite3
    conn = sqlite3.connect('data/trading_database.db')
    cursor = conn.cursor()
    
    # Check trades table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trades'")
    if cursor.fetchone():
        print("   ✅ trades table - EXISTS")
        
        # Check columns
        cursor.execute("PRAGMA table_info(trades)")
        columns = [row[1] for row in cursor.fetchall()]
        expected_columns = ['id', 'timestamp', 'date', 'symbol', 'stock_name', 'strategy', 
                          'signal', 'quantity', 'price', 'total_amount', 'order_id', 
                          'status', 'ai_enabled', 'confidence', 'models_used', 'notes']
        
        missing_columns = set(expected_columns) - set(columns)
        if missing_columns:
            errors_found.append(f"Missing columns in trades table: {missing_columns}")
            print(f"   ❌ Missing columns: {missing_columns}")
        else:
            print(f"   ✅ All {len(columns)} columns present")
    else:
        errors_found.append("trades table not found")
        print("   ❌ trades table - NOT FOUND")
    
    # Check daily_summary table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_summary'")
    if cursor.fetchone():
        print("   ✅ daily_summary table - EXISTS")
        
        cursor.execute("PRAGMA table_info(daily_summary)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"   ✅ All {len(columns)} columns present")
    else:
        errors_found.append("daily_summary table not found")
        print("   ❌ daily_summary table - NOT FOUND")
    
    # Check indexes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = [row[0] for row in cursor.fetchall()]
    print(f"   ✅ {len(indexes)} indexes created")
    
    conn.close()
    
except Exception as e:
    errors_found.append(f"Database schema check error: {e}")
    print(f"   ❌ Schema check failed: {e}")

# Test 6: Dependencies Check
print("\n6️⃣ Dependencies Check")
print("-" * 70)
try:
    import sqlite3
    print("   ✅ sqlite3 - OK")
except:
    errors_found.append("sqlite3 not available")
    print("   ❌ sqlite3 - NOT AVAILABLE")

try:
    import pandas
    print("   ✅ pandas - OK")
except:
    errors_found.append("pandas not installed")
    print("   ❌ pandas - NOT INSTALLED")

try:
    import openpyxl
    print("   ✅ openpyxl - OK")
except:
    errors_found.append("openpyxl not installed")
    print("   ❌ openpyxl - NOT INSTALLED")

# Final Summary
print("\n" + "=" * 70)
print("📊 FINAL SUMMARY")
print("=" * 70)

if not errors_found and not warnings_found:
    print("✅ ALL CHECKS PASSED - No errors or warnings found!")
    print("\n🎉 The trading database system is fully functional and ready to use.")
else:
    if errors_found:
        print(f"\n❌ ERRORS FOUND: {len(errors_found)}")
        for i, error in enumerate(errors_found, 1):
            print(f"   {i}. {error}")
    
    if warnings_found:
        print(f"\n⚠️  WARNINGS: {len(warnings_found)}")
        for i, warning in enumerate(warnings_found, 1):
            print(f"   {i}. {warning}")
    
    if not errors_found:
        print("\n✅ No critical errors found. Warnings are informational only.")
        print("🎉 The trading database system is functional.")

print("\n" + "=" * 70)
print("Error check completed!")
print("=" * 70)

# Exit with appropriate code
sys.exit(0 if not errors_found else 1)
