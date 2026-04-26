"""
Trading Database Manager
-------------------------
Manages SQLite database for storing trade-wise and day-wise trading data.
Provides Excel export functionality for reporting and analysis.
"""

import sqlite3
import pandas as pd
from datetime import datetime, date
from pathlib import Path
import os
from typing import Dict, List, Optional, Tuple


# Database path
DB_DIR = Path(__file__).parent / "data"
DB_PATH = DB_DIR / "trading_database.db"
EXPORT_DIR = DB_DIR / "exports"


def initialize_database():
    """
    Initialize the SQLite database with required tables.
    Creates database file and tables if they don't exist.
    """
    # Ensure data directory exists
    DB_DIR.mkdir(exist_ok=True)
    EXPORT_DIR.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create trades table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            date DATE NOT NULL,
            symbol TEXT NOT NULL,
            stock_name TEXT NOT NULL,
            strategy TEXT NOT NULL,
            signal TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            total_amount REAL NOT NULL,
            order_id TEXT,
            status TEXT NOT NULL,
            ai_enabled BOOLEAN DEFAULT 0,
            confidence REAL,
            models_used TEXT,
            notes TEXT
        )
    """)
    
    # Create daily_summary table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE UNIQUE NOT NULL,
            starting_balance REAL NOT NULL,
            ending_balance REAL NOT NULL,
            total_pnl REAL DEFAULT 0,
            realized_pnl REAL DEFAULT 0,
            unrealized_pnl REAL DEFAULT 0,
            total_trades INTEGER DEFAULT 0,
            buy_trades INTEGER DEFAULT 0,
            sell_trades INTEGER DEFAULT 0,
            total_capital_used REAL DEFAULT 0,
            open_positions INTEGER DEFAULT 0,
            ai_trades INTEGER DEFAULT 0,
            rule_based_trades INTEGER DEFAULT 0,
            notes TEXT
        )
    """)
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            upstox_email TEXT,
            upstox_linked BOOLEAN DEFAULT 0,
            upstox_linked_at TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    """)
    
    # Create RL experiences table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rl_experiences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            symbol TEXT NOT NULL,
            state BLOB NOT NULL,
            action INTEGER NOT NULL,
            reward REAL NOT NULL,
            next_state BLOB,
            done BOOLEAN NOT NULL,
            trade_id INTEGER,
            profit REAL,
            profit_pct REAL,
            holding_time REAL,
            FOREIGN KEY (trade_id) REFERENCES trades(id)
        )
    """)
    
    # Create indexes for faster queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_date ON trades(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_summary_date ON daily_summary(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rl_experiences_symbol ON rl_experiences(symbol)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rl_experiences_timestamp ON rl_experiences(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    
    conn.commit()
    conn.close()
    
    print(f"[OK] Database initialized at: {DB_PATH}")


def log_trade(trade_data: Dict) -> bool:
    """
    Log a trade to the database.
    
    Args:
        trade_data: Dictionary containing trade information
            Required keys: timestamp, symbol, stock_name, strategy, signal, 
                          quantity, price, status
            Optional keys: order_id, ai_enabled, confidence, models_used, notes
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Extract data with defaults
        timestamp = trade_data.get('timestamp', datetime.now())
        trade_date = timestamp.date() if isinstance(timestamp, datetime) else date.today()
        
        symbol = trade_data['symbol']
        stock_name = trade_data['stock_name']
        strategy = trade_data['strategy']
        signal = trade_data['signal']
        quantity = trade_data['quantity']
        price = trade_data['price']
        total_amount = quantity * price
        order_id = trade_data.get('order_id', '')
        status = trade_data['status']
        ai_enabled = trade_data.get('ai_enabled', False)
        confidence = trade_data.get('confidence', None)
        models_used = trade_data.get('models_used', '')
        notes = trade_data.get('notes', '')
        
        cursor.execute("""
            INSERT INTO trades (
                timestamp, date, symbol, stock_name, strategy, signal,
                quantity, price, total_amount, order_id, status,
                ai_enabled, confidence, models_used, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, trade_date, symbol, stock_name, strategy, signal,
            quantity, price, total_amount, order_id, status,
            ai_enabled, confidence, models_used, notes
        ))
        
        conn.commit()
        conn.close()
        
        print(f"[LOG] Trade logged: {signal} {quantity} {stock_name} @ Rs.{price:.2f}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error logging trade: {e}")
        return False


def update_daily_summary(summary_data: Dict) -> bool:
    """
    Update or insert daily summary data.
    
    Args:
        summary_data: Dictionary containing daily summary information
            Required keys: date, starting_balance, ending_balance
            Optional keys: total_pnl, realized_pnl, unrealized_pnl, total_trades,
                          buy_trades, sell_trades, total_capital_used, 
                          open_positions, ai_trades, rule_based_trades, notes
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Extract data with defaults
        summary_date = summary_data.get('date', date.today())
        starting_balance = summary_data['starting_balance']
        ending_balance = summary_data['ending_balance']
        total_pnl = summary_data.get('total_pnl', 0)
        realized_pnl = summary_data.get('realized_pnl', 0)
        unrealized_pnl = summary_data.get('unrealized_pnl', 0)
        total_trades = summary_data.get('total_trades', 0)
        buy_trades = summary_data.get('buy_trades', 0)
        sell_trades = summary_data.get('sell_trades', 0)
        total_capital_used = summary_data.get('total_capital_used', 0)
        open_positions = summary_data.get('open_positions', 0)
        ai_trades = summary_data.get('ai_trades', 0)
        rule_based_trades = summary_data.get('rule_based_trades', 0)
        notes = summary_data.get('notes', '')
        
        # Use INSERT OR REPLACE to handle updates
        cursor.execute("""
            INSERT OR REPLACE INTO daily_summary (
                date, starting_balance, ending_balance, total_pnl,
                realized_pnl, unrealized_pnl, total_trades, buy_trades,
                sell_trades, total_capital_used, open_positions,
                ai_trades, rule_based_trades, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            summary_date, starting_balance, ending_balance, total_pnl,
            realized_pnl, unrealized_pnl, total_trades, buy_trades,
            sell_trades, total_capital_used, open_positions,
            ai_trades, rule_based_trades, notes
        ))
        
        conn.commit()
        conn.close()
        
        print(f"[INFO] Daily summary updated for {summary_date}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error updating daily summary: {e}")
        return False


def get_trades_by_date(query_date: date) -> pd.DataFrame:
    """
    Retrieve all trades for a specific date.
    
    Args:
        query_date: Date to query
    
    Returns:
        DataFrame containing trades for the specified date
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        query = "SELECT * FROM trades WHERE date = ? ORDER BY timestamp"
        df = pd.read_sql_query(query, conn, params=(query_date,))
        conn.close()
        return df
    except Exception as e:
        print(f"[ERROR] Error retrieving trades: {e}")
        return pd.DataFrame()


def get_trades_by_date_range(start_date: date, end_date: date) -> pd.DataFrame:
    """
    Retrieve all trades within a date range.
    
    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
    
    Returns:
        DataFrame containing trades within the date range
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        query = "SELECT * FROM trades WHERE date BETWEEN ? AND ? ORDER BY timestamp"
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()
        return df
    except Exception as e:
        print(f"[ERROR] Error retrieving trades: {e}")
        return pd.DataFrame()


def get_daily_summary(query_date: date) -> Optional[Dict]:
    """
    Get daily summary for a specific date.
    
    Args:
        query_date: Date to query
    
    Returns:
        Dictionary containing daily summary or None if not found
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM daily_summary WHERE date = ?", (query_date,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            columns = [
                'id', 'date', 'starting_balance', 'ending_balance', 'total_pnl',
                'realized_pnl', 'unrealized_pnl', 'total_trades', 'buy_trades',
                'sell_trades', 'total_capital_used', 'open_positions',
                'ai_trades', 'rule_based_trades', 'notes'
            ]
            return dict(zip(columns, row))
        return None
        
    except Exception as e:
        print(f"[ERROR] Error retrieving daily summary: {e}")
        return None


def get_daily_summaries_by_range(start_date: date, end_date: date) -> pd.DataFrame:
    """
    Retrieve daily summaries within a date range.
    
    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
    
    Returns:
        DataFrame containing daily summaries within the date range
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        query = "SELECT * FROM daily_summary WHERE date BETWEEN ? AND ? ORDER BY date"
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()
        return df
    except Exception as e:
        print(f"[ERROR] Error retrieving daily summaries: {e}")
        return pd.DataFrame()


def export_to_excel(start_date: Optional[date] = None, 
                   end_date: Optional[date] = None,
                   output_path: Optional[str] = None) -> bool:
    """
    Export trading data to Excel format.
    
    Args:
        start_date: Start date for export (default: 30 days ago)
        end_date: End date for export (default: today)
        output_path: Custom output path (default: data/exports/trading_data_YYYY-MM-DD.xlsx)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Set default dates
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = date.today().replace(day=1)  # First day of current month
        
        # Set default output path
        if output_path is None:
            filename = f"trading_data_{end_date.strftime('%Y-%m-%d')}.xlsx"
            output_path = EXPORT_DIR / filename
        
        # Retrieve data
        trades_df = get_trades_by_date_range(start_date, end_date)
        summaries_df = get_daily_summaries_by_range(start_date, end_date)
        
        # Create Excel writer
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Write trades sheet
            if not trades_df.empty:
                trades_df.to_excel(writer, sheet_name='Trades', index=False)
            else:
                pd.DataFrame({'Message': ['No trades found for this period']}).to_excel(
                    writer, sheet_name='Trades', index=False
                )
            
            # Write daily summaries sheet
            if not summaries_df.empty:
                summaries_df.to_excel(writer, sheet_name='Daily Summary', index=False)
            else:
                pd.DataFrame({'Message': ['No daily summaries found for this period']}).to_excel(
                    writer, sheet_name='Daily Summary', index=False
                )
            
            # Create overview sheet with statistics
            overview_data = {
                'Metric': [
                    'Export Date Range',
                    'Total Trades',
                    'Total Buy Trades',
                    'Total Sell Trades',
                    'Total P&L',
                    'AI-Enabled Trades',
                    'Rule-Based Trades',
                    'Total Capital Used',
                    'Average Daily P&L'
                ],
                'Value': [
                    f"{start_date} to {end_date}",
                    len(trades_df) if not trades_df.empty else 0,
                    len(trades_df[trades_df['signal'] == 'BUY']) if not trades_df.empty else 0,
                    len(trades_df[trades_df['signal'] == 'SELL']) if not trades_df.empty else 0,
                    summaries_df['total_pnl'].sum() if not summaries_df.empty else 0,
                    len(trades_df[trades_df['ai_enabled'] == 1]) if not trades_df.empty else 0,
                    len(trades_df[trades_df['ai_enabled'] == 0]) if not trades_df.empty else 0,
                    summaries_df['total_capital_used'].sum() if not summaries_df.empty else 0,
                    summaries_df['total_pnl'].mean() if not summaries_df.empty else 0
                ]
            }
            overview_df = pd.DataFrame(overview_data)
            overview_df.to_excel(writer, sheet_name='Overview', index=False)
        
        print(f"[OK] Data exported to: {output_path}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error exporting to Excel: {e}")
        return False


def get_trade_statistics(days: int = 30) -> Dict:
    """
    Get trading statistics for the last N days.
    
    Args:
        days: Number of days to look back
    
    Returns:
        Dictionary containing trade statistics
    """
    try:
        end_date = date.today()
        from datetime import timedelta
        start_date = date.today() - timedelta(days=days)
        
        trades_df = get_trades_by_date_range(start_date, end_date)
        summaries_df = get_daily_summaries_by_range(start_date, end_date)
        
        stats = {
            'period': f"{start_date} to {end_date}",
            'total_trades': len(trades_df),
            'buy_trades': len(trades_df[trades_df['signal'] == 'BUY']) if not trades_df.empty else 0,
            'sell_trades': len(trades_df[trades_df['signal'] == 'SELL']) if not trades_df.empty else 0,
            'ai_trades': len(trades_df[trades_df['ai_enabled'] == 1]) if not trades_df.empty else 0,
            'rule_based_trades': len(trades_df[trades_df['ai_enabled'] == 0]) if not trades_df.empty else 0,
            'total_pnl': summaries_df['total_pnl'].sum() if not summaries_df.empty else 0,
            'avg_daily_pnl': summaries_df['total_pnl'].mean() if not summaries_df.empty else 0,
            'total_capital_used': summaries_df['total_capital_used'].sum() if not summaries_df.empty else 0,
            'trading_days': len(summaries_df)
        }
        
        return stats
        
    except Exception as e:
        print(f"[ERROR] Error calculating statistics: {e}")
        return {}


def store_rl_experience(experience_data: Dict) -> bool:
    """
    Store an RL experience to the database.
    
    Args:
        experience_data: Dictionary containing:
            - symbol: Stock symbol
            - state: State vector (numpy array or list)
            - action: Action taken (0=HOLD, 1=BUY, 2=SELL)
            - reward: Reward received
            - next_state: Next state vector (optional)
            - done: Whether episode is done
            - trade_id: Associated trade ID (optional)
            - profit: Profit amount (optional)
            - profit_pct: Profit percentage (optional)
            - holding_time: Holding time in days (optional)
    
    Returns:
        bool: True if successful
    """
    try:
        import pickle
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Serialize state and next_state
        state_blob = pickle.dumps(experience_data['state'])
        next_state_blob = pickle.dumps(experience_data.get('next_state')) if experience_data.get('next_state') is not None else None
        
        cursor.execute("""
            INSERT INTO rl_experiences (
                timestamp, symbol, state, action, reward, next_state, done,
                trade_id, profit, profit_pct, holding_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(),
            experience_data['symbol'],
            state_blob,
            experience_data['action'],
            experience_data['reward'],
            next_state_blob,
            experience_data['done'],
            experience_data.get('trade_id'),
            experience_data.get('profit'),
            experience_data.get('profit_pct'),
            experience_data.get('holding_time')
        ))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Error storing RL experience: {e}")
        return False


def get_recent_experiences(limit: int = 1000) -> List[Dict]:
    """
    Get recent RL experiences from database.
    
    Args:
        limit: Maximum number of experiences to retrieve
    
    Returns:
        List of experience dictionaries
    """
    try:
        import pickle
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, symbol, state, action, reward, next_state, done,
                   trade_id, profit, profit_pct, holding_time
            FROM rl_experiences
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        experiences = []
        for row in cursor.fetchall():
            exp = {
                'id': row[0],
                'timestamp': row[1],
                'symbol': row[2],
                'state': pickle.loads(row[3]),
                'action': row[4],
                'reward': row[5],
                'next_state': pickle.loads(row[6]) if row[6] else None,
                'done': bool(row[7]),
                'trade_id': row[8],
                'profit': row[9],
                'profit_pct': row[10],
                'holding_time': row[11]
            }
            experiences.append(exp)
        
        conn.close()
        return experiences
        
    except Exception as e:
        print(f"[ERROR] Error retrieving experiences: {e}")
        return []


def get_experiences_by_symbol(symbol: str, limit: int = 500) -> List[Dict]:
    """
    Get RL experiences for a specific symbol.
    
    Args:
        symbol: Stock symbol
        limit: Maximum number of experiences
    
    Returns:
        List of experience dictionaries
    """
    try:
        import pickle
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, symbol, state, action, reward, next_state, done,
                   trade_id, profit, profit_pct, holding_time
            FROM rl_experiences
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (symbol, limit))
        
        experiences = []
        for row in cursor.fetchall():
            exp = {
                'id': row[0],
                'timestamp': row[1],
                'symbol': row[2],
                'state': pickle.loads(row[3]),
                'action': row[4],
                'reward': row[5],
                'next_state': pickle.loads(row[6]) if row[6] else None,
                'done': bool(row[7]),
                'trade_id': row[8],
                'profit': row[9],
                'profit_pct': row[10],
                'holding_time': row[11]
            }
            experiences.append(exp)
        
        conn.close()
        return experiences
        
    except Exception as e:
        print(f"[ERROR] Error retrieving experiences for {symbol}: {e}")
        return []


# ========================================
# User Management Functions
# ========================================

def create_user(email: str, full_name: str, password_hash: str) -> Optional[int]:
    """
    Create a new user account.
    
    Args:
        email: User's email address (unique)
        full_name: User's full name
        password_hash: Hashed password from AuthManager
        
    Returns:
        User ID if successful, None otherwise
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO users (email, full_name, password_hash)
            VALUES (?, ?, ?)
        """, (email, full_name, password_hash))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"[OK] User created: {email} (ID: {user_id})")
        return user_id
        
    except sqlite3.IntegrityError:
        print(f"[ERROR] User with email {email} already exists")
        return None
    except Exception as e:
        print(f"[ERROR] Error creating user: {e}")
        return None


def get_user_by_email(email: str) -> Optional[Dict]:
    """
    Retrieve user by email address.
    
    Args:
        email: User's email address
        
    Returns:
        User dictionary if found, None otherwise
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, email, full_name, password_hash, created_at,
                   upstox_email, upstox_linked, upstox_linked_at, is_active
            FROM users
            WHERE email = ?
        """, (email,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'email': row[1],
                'full_name': row[2],
                'password_hash': row[3],
                'created_at': row[4],
                'upstox_email': row[5],
                'upstox_linked': bool(row[6]),
                'upstox_linked_at': row[7],
                'is_active': bool(row[8])
            }
        return None
        
    except Exception as e:
        print(f"[ERROR] Error retrieving user: {e}")
        return None


def verify_user_credentials(email: str, password_hash: str) -> Optional[Dict]:
    """
    Verify user credentials for login.
    
    Args:
        email: User's email
        password_hash: Hashed password to verify
        
    Returns:
        User dictionary if credentials valid, None otherwise
    """
    user = get_user_by_email(email)
    if user and user['password_hash'] == password_hash and user['is_active']:
        return user
    return None


def update_upstox_link(user_id: int, upstox_email: str) -> bool:
    """
    Link Upstox account to user.
    
    Args:
        user_id: User's database ID
        upstox_email: Email from Upstox account
        
    Returns:
        True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users
            SET upstox_email = ?,
                upstox_linked = 1,
                upstox_linked_at = ?
            WHERE id = ?
        """, (upstox_email, datetime.now(), user_id))
        
        conn.commit()
        conn.close()
        
        print(f"[OK] Upstox account linked for user ID {user_id}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error linking Upstox account: {e}")
        return False


# Note: Database initialization is handled explicitly in trading execution files
# via initialize_database() call at startup
