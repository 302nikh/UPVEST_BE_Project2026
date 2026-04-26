import os
import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = "data/trading_database.db"
EXPORT_DIR = "data/exports"

def export_all_data():
    """
    Export all trades and daily summaries to an Excel file.
    Returns the absolute path to the generated file, or None if failed.
    """
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return None
        
    os.makedirs(EXPORT_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"upvest_export_{timestamp}.xlsx"
    export_path = os.path.abspath(os.path.join(EXPORT_DIR, filename))
    
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Check if tables exist before exporting
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]

        if not tables:
            print("No data tables found in database.")
            conn.close()
            return None

        # Write to Excel
        with pd.ExcelWriter(export_path, engine='xlsxwriter') as writer:
            if "trades" in tables:
                df_trades = pd.read_sql_query("SELECT * FROM trades", conn)
                if not df_trades.empty:
                    # Clean up dates for better excel formatting
                    if 'timestamp' in df_trades.columns:
                        df_trades['timestamp'] = pd.to_datetime(df_trades['timestamp'], errors='coerce').dt.tz_localize(None)
                    df_trades.to_excel(writer, sheet_name="Transactions", index=False)
                    
                    # Formatting workbook
                    worksheet = writer.sheets["Transactions"]
                    for i, col in enumerate(df_trades.columns):
                        max_len = max(df_trades[col].map(lambda x: len(str(x))).max(), len(col)) + 2
                        worksheet.set_column(i, i, min(max_len, 30))

            if "daily_summary" in tables:
                df_summary = pd.read_sql_query("SELECT * FROM daily_summary", conn)
                if not df_summary.empty:
                    if 'date' in df_summary.columns:
                        df_summary['date'] = pd.to_datetime(df_summary['date'], errors='coerce').dt.tz_localize(None)
                    df_summary.to_excel(writer, sheet_name="Daily Summaries", index=False)
                    
                    worksheet = writer.sheets["Daily Summaries"]
                    for i, col in enumerate(df_summary.columns):
                        max_len = max(df_summary[col].map(lambda x: len(str(x))).max(), len(col)) + 2
                        worksheet.set_column(i, i, min(max_len, 30))

        conn.close()
        
        # Verify file was created and isn't empty 
        # (pandas will create an empty byte file if no sheets were written)
        if os.path.exists(export_path) and os.path.getsize(export_path) > 0:
            return export_path
        else:
            if os.path.exists(export_path):
                os.remove(export_path)
            return None
            
    except Exception as e:
        print(f"Export Error: {e}")
        return None

if __name__ == "__main__":
    path = export_all_data()
    print(f"Exported to: {path}")
