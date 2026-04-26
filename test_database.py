"""
Test script for database functionality
"""
from database_manager import initialize_database, log_trade, update_daily_summary, export_to_excel
from datetime import datetime, date

print("🧪 Testing Database Functionality\n")
print("=" * 50)

# Test 1: Initialize database
print("\n1️⃣ Testing database initialization...")
try:
    initialize_database()
    print("✅ Database initialized successfully")
except Exception as e:
    print(f"❌ Database initialization failed: {e}")

# Test 2: Log a test trade
print("\n2️⃣ Testing trade logging...")
try:
    test_trade = {
        'timestamp': datetime.now(),
        'symbol': 'NSE_EQ|INE467B01029',
        'stock_name': 'TCS',
        'strategy': 'ma_crossover',
        'signal': 'BUY',
        'quantity': 10,
        'price': 3500.50,
        'order_id': 'TEST123',
        'status': 'SUCCESS',
        'ai_enabled': True,
        'confidence': 0.85,
        'models_used': 'LSTM,Sentiment'
    }
    log_trade(test_trade)
    print("✅ Trade logged successfully")
except Exception as e:
    print(f"❌ Trade logging failed: {e}")

# Test 3: Update daily summary
print("\n3️⃣ Testing daily summary update...")
try:
    test_summary = {
        'date': date.today(),
        'starting_balance': 100000.0,
        'ending_balance': 102500.0,
        'total_pnl': 2500.0,
        'total_trades': 5,
        'buy_trades': 3,
        'sell_trades': 2,
        'total_capital_used': 50000.0,
        'open_positions': 2,
        'ai_trades': 3,
        'rule_based_trades': 2
    }
    update_daily_summary(test_summary)
    print("✅ Daily summary updated successfully")
except Exception as e:
    print(f"❌ Daily summary update failed: {e}")

# Test 4: Export to Excel
print("\n4️⃣ Testing Excel export...")
try:
    export_to_excel()
    print("✅ Excel export completed successfully")
except Exception as e:
    print(f"❌ Excel export failed: {e}")

print("\n" + "=" * 50)
print("✅ All tests completed!")
print("\nCheck the following:")
print("  - Database file: data/trading_database.db")
print("  - Excel export: data/exports/")
