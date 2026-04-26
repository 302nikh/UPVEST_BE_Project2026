"""
Optimized Model Trainer - Maximum Accuracy
-------------------------------------------
Enhanced training configuration for minimal prediction error.
"""

import pandas as pd
import numpy as np
import torch
from torch.utils.data import TensorDataset, DataLoader
from sklearn.model_selection import train_test_split
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_agent.feature_engineering import FeatureEngineer
from ai_agent.models.lstm_predictor import LSTMPredictor, LSTMTrainer
from trading_execution import fetch_historical_data
from standalone_login_auth import load_token_from_file


def prepare_training_data(symbols, interval='day', days=1000):
    """
    Fetch maximum historical data for training.
    
    Args:
        symbols: List of stock symbols
        interval: Data interval
        days: Number of days (increased to 1000 for more data)
        
    Returns:
        Combined DataFrame
    """
    print(f"📊 Fetching maximum historical data for {len(symbols)} symbols...")
    print(f"   Target: {days} days per symbol")
    all_data = []
    
    for symbol in symbols:
        print(f"  📈 Fetching {symbol}...")
        df = fetch_historical_data(symbol, interval=interval, days=days)
        if not df.empty:
            df['symbol'] = symbol
            all_data.append(df)
            print(f"     ✅ Got {len(df)} data points")
    
    if not all_data:
        raise ValueError("❌ No data fetched!")
    
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"\n✅ Total data points: {len(combined_df):,}")
    
    return combined_df


def train_lstm_model_optimized(df, epochs=100, batch_size=64, test_size=0.15, 
                               learning_rate=0.0005, save_path='data/trained_models/lstm_best.pth'):
    """
    Train LSTM with optimized hyperparameters for maximum accuracy.
    
    Optimizations:
    - More epochs (100 vs 50)
    - Larger batch size (64 vs 32) for stable gradients
    - Smaller test split (15% vs 20%) for more training data
    - Lower learning rate (0.0005 vs 0.001) for better convergence
    - Larger hidden size (256 vs 128)
    - More LSTM layers (3 vs 2)
    """
    print("\n" + "="*70)
    print("🚀 OPTIMIZED LSTM TRAINING - MAXIMUM ACCURACY MODE")
    print("="*70)
    
    # Feature engineering with longer lookback
    print("\n1️⃣ Feature Engineering (Enhanced)...")
    fe = FeatureEngineer(lookback_period=90)  # Increased from 60
    df_features = fe.prepare_features(df)
    
    print(f"   📊 Features shape: {df_features.shape}")
    print(f"   📈 Number of features: {len(df_features.columns)}")
    
    # Create sequences
    print("\n2️⃣ Creating training sequences...")
    X, y, scaler, feature_cols = fe.create_sequences(df_features, target_col='close')
    
    print(f"   📦 Sequences: X={X.shape}, y={y.shape}")
    print(f"   🎯 Feature columns: {len(feature_cols)}")
    
    # Train-test split
    print("\n3️⃣ Splitting data (85% train, 15% validation)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, shuffle=False
    )
    
    print(f"   🏋️ Train: {X_train.shape[0]:,} samples")
    print(f"   ✅ Validation: {X_test.shape[0]:,} samples")
    
    # Convert to PyTorch tensors
    X_train_tensor = torch.FloatTensor(X_train)
    y_train_tensor = torch.FloatTensor(y_train)
    X_test_tensor = torch.FloatTensor(X_test)
    y_test_tensor = torch.FloatTensor(y_test)
    
    # Create data loaders
    train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
    test_dataset = TensorDataset(X_test_tensor, y_test_tensor)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    # Create enhanced model
    print("\n4️⃣ Creating Enhanced LSTM model...")
    input_size = X.shape[2]
    model = LSTMPredictor(
        input_size=input_size, 
        hidden_size=256,  # Increased from 128
        num_layers=3,     # Increased from 2
        dropout=0.3       # Increased from 0.2
    )
    
    print(f"   🧠 Input features: {input_size}")
    print(f"   🔢 Hidden units: 256 (enhanced)")
    print(f"   📚 LSTM layers: 3 (enhanced)")
    print(f"   💧 Dropout: 0.3")
    print(f"   ⚙️ Total parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Train with optimized settings
    print("\n5️⃣ Training (Optimized for Accuracy)...")
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"   🖥️ Device: {device.upper()}")
    
    trainer = LSTMTrainer(model, learning_rate=learning_rate, device=device)
    
    print(f"\n   📋 Training Configuration:")
    print(f"      • Epochs: {epochs}")
    print(f"      • Batch size: {batch_size}")
    print(f"      • Learning rate: {learning_rate}")
    print(f"      • Early stopping patience: 15")
    print(f"\n   🏃 Starting training...\n")
    
    try:
        history = trainer.train(train_loader, test_loader, epochs=epochs, patience=15)
    except KeyboardInterrupt:
        print("\n⚠️ Training interrupted by user. Saving current progress...")
        history = trainer.history # Use whatever history we have
    except Exception as e:
        print(f"\n❌ Training error: {e}")
        raise e
    finally:
        # Save final model (or best validation model if early stopping/interrupt)
        print(f"\n6️⃣ Saving model to {save_path}...")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        trainer.save_model(save_path)
        
        # Save scaler and feature columns
        import pickle
        scaler_path = save_path.replace('.pth', '_scaler.pkl')
        config_path = save_path.replace('.pth', '_config.pkl')
        
        with open(scaler_path, 'wb') as f:
            pickle.dump({'scaler': scaler, 'feature_cols': feature_cols}, f)
        
        with open(config_path, 'wb') as f:
            pickle.dump({
                'input_size': input_size,
                'hidden_size': 256,
                'num_layers': 3,
                'lookback_period': 90
            }, f)
        
        print(f"   ✅ Model saved: {save_path}")
        print(f"   ✅ Scaler saved: {scaler_path}")
        print(f"   ✅ Config saved: {config_path}")
        
        # Calculate final metrics if history exists
        if 'train_losses' in history and history['train_losses']:
            print("\n7️⃣ Final Model Performance:")
            final_train_loss = history['train_losses'][-1]
            final_val_loss = history['val_losses'][-1]
            best_val_loss = min(history['val_losses'])
            
            print(f"   📉 Final Train Loss: {final_train_loss:.6f}")
            print(f"   📉 Final Val Loss: {final_val_loss:.6f}")
            print(f"   🏆 Best Val Loss: {best_val_loss:.6f}")
            print(f"   📊 Improvement: {((history['val_losses'][0] - best_val_loss) / history['val_losses'][0] * 100):.2f}%")
        
    print("\n" + "="*70)
    print("✅ TRAINING COMPLETE - MODEL READY FOR PRODUCTION!")
    print("="*70)
    
    return trainer, history


if __name__ == "__main__":
    print("\n🚀 OPTIMIZED LSTM MODEL TRAINING")
    print("="*70)
    print("Target: Maximum Accuracy with Minimal Error")
    print("="*70)
    
    # Check if token exists
    token_info = load_token_from_file()
    if not token_info:
        print("\n❌ No access token found. Please run authentication first.")
        sys.exit(1)
    
    # Define training symbols - NIFTY 50 Constituents (Top 50 Indian Stocks)
    training_symbols = [
        # Banking & Financial
        "NSE_EQ|INE040A01034",  # HDFCBANK
        "NSE_EQ|INE090A01021",  # ICICIBANK
        "NSE_EQ|INE062A01020",  # SBIN
        "NSE_EQ|INE238A01034",  # AXISBANK
        "NSE_EQ|INE176A01028",  # KOTAKBANK
        "NSE_EQ|INE774A01016",  # BAJFINANCE
        "NSE_EQ|INE296A01024",  # BAJAJFINSV
        "NSE_EQ|INE018A01030",  # HDFCLIFE
        "NSE_EQ|INE795G01014",  # SBILIFE
        "NSE_EQ|INE726G01019",  # ICICIPRULI
        
        # IT & Technology
        "NSE_EQ|INE467B01029",  # TCS
        "NSE_EQ|INE009A01021",  # INFY
        "NSE_EQ|INE860A01027",  # HCL TECH
        "NSE_EQ|INE158A01026",  # WIPRO
        "NSE_EQ|INE277A01024",  # TECHM
        
        # Oil & Gas
        "NSE_EQ|INE002A01018",  # RELIANCE
        "NSE_EQ|INE213A01029",  # ONGC
        "NSE_EQ|INE029A01011",  # BPCL
        "NSE_EQ|INE095A01012",  # IOC
        
        # Consumer & FMCG
        "NSE_EQ|INE030A01027",  # HINDUNILVR
        "NSE_EQ|INE154A01025",  # ITC
        "NSE_EQ|INE047A01021",  # NESTLEIND
        "NSE_EQ|INE259A01022",  # BRITANNIA
        "NSE_EQ|INE192A01025",  # TITAN
        
        # Automobile
        "NSE_EQ|INE101A01026",  # MARUTI
        "NSE_EQ|INE169A01031",  # M&M
        "NSE_EQ|INE917I01010",  # TATAMOTORS
        "NSE_EQ|INE758T01015",  # BAJAJ-AUTO
        "NSE_EQ|INE066A01013",  # EICHERMOT
        "NSE_EQ|INE752E01010",  # HEROMOTOCO
        
        # Pharma & Healthcare
        "NSE_EQ|INE089A01023",  # SUNPHARMA
        "NSE_EQ|INE176A01022",  # DRREDDY
        "NSE_EQ|INE528G01035",  # DIVISLAB
        "NSE_EQ|INE019A01038",  # CIPLA
        "NSE_EQ|INE326A01037",  # APOLLOHOSP
        
        # Infrastructure & Metals
        "NSE_EQ|INE018A01030",  # L&T
        "NSE_EQ|INE081A01012",  # TATASTEEL
        "NSE_EQ|INE114A01011",  # JSWSTEEL
        "NSE_EQ|INE038A01020",  # HINDALCO
        "NSE_EQ|INE245A01021",  # ULTRACEMCO
        "NSE_EQ|INE176A01016",  # GRASIM
        
        # Power & Utilities
        "NSE_EQ|INE733E01010",  # POWERGRID
        "NSE_EQ|INE152A01029",  # NTPC
        "NSE_EQ|INE848E01016",  # ADANIGREEN
        "NSE_EQ|INE075A01022",  # TATAPOWER
        
        # Telecom & Others
        "NSE_EQ|INE397D01024",  # BHARTIARTL
        "NSE_EQ|INE155A01022",  # ASIANPAINT
        "NSE_EQ|INE585B01010",  # ADANIENT
        "NSE_EQ|INE121A01016",  # INDUSINDBK
        "NSE_EQ|INE111A01025",  # COALINDIA
    ]
    

# ============================================================
# INTRADAY LSTM TRAINER
# ============================================================

def train_lstm_intraday(
    df,
    epochs=20,
    batch_size=64,
    test_size=0.15,
    learning_rate=0.0005,
    save_path='data/trained_models/lstm_intraday.pth'
):
    """
    Train LSTM specifically for intraday (30-minute) data.

    Key differences vs daily model:
      - lookback_period = 78  (approx. 2 full trading days of 30-min candles)
      - is_intraday = True    (adds VWAP, session_hour, intraday_return etc.)
      - Save path: lstm_intraday.pth  (separate from daily lstm_best.pth)
    """
    print("\n" + "="*70)
    print("  INTRADAY LSTM TRAINING - 30-MINUTE CANDLES")
    print("="*70)

    LOOKBACK = 78    # ~2 full NSE trading days (13 candles/day x 6 days)

    print("\n1 Feature Engineering (Intraday + Standard)...")
    fe = FeatureEngineer(lookback_period=LOOKBACK)
    df_features = fe.prepare_features(df, is_intraday=True)   # <-- intraday features ON

    print(f"   Features shape : {df_features.shape}")
    print(f"   Feature count  : {len(df_features.columns)}")

    print("\n2 Creating sequences...")
    X, y, scaler, feature_cols = fe.create_sequences(df_features, target_col='close')
    print(f"   Sequences: X={X.shape}, y={y.shape}")

    print("\n3 Splitting (85% train / 15% val)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, shuffle=False
    )
    print(f"   Train : {X_train.shape[0]:,} samples")
    print(f"   Val   : {X_test.shape[0]:,} samples")

    X_train_t = torch.FloatTensor(X_train)
    y_train_t = torch.FloatTensor(y_train)
    X_test_t  = torch.FloatTensor(X_test)
    y_test_t  = torch.FloatTensor(y_test)

    train_ds = TensorDataset(X_train_t, y_train_t)
    test_ds  = TensorDataset(X_test_t,  y_test_t)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    test_loader  = DataLoader(test_ds,  batch_size=batch_size, shuffle=False)

    print("\n4 Building LSTM model...")
    input_size = X.shape[2]
    model = LSTMPredictor(
        input_size=input_size,
        hidden_size=256,
        num_layers=3,
        dropout=0.3
    )
    print(f"   Input features : {input_size}  (includes VWAP, session_hour, etc.)")
    print(f"   Parameters     : {sum(p.numel() for p in model.parameters()):,}")

    print("\n5 Training...")
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    trainer = LSTMTrainer(model, learning_rate=learning_rate, device=device)

    try:
        history = trainer.train(train_loader, test_loader, epochs=epochs, patience=12)
    except KeyboardInterrupt:
        print("\n Training interrupted — saving progress...")
        history = getattr(trainer, 'history',
                          {'train_losses': trainer.train_losses,
                           'val_losses':   trainer.val_losses})
    finally:
        print(f"\n6 Saving model to {save_path}...")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        trainer.save_model(save_path)

        import pickle
        scaler_path = save_path.replace('.pth', '_scaler.pkl')
        config_path = save_path.replace('.pth', '_config.pkl')

        with open(scaler_path, 'wb') as f:
            pickle.dump({'scaler': scaler, 'feature_cols': feature_cols}, f)
        with open(config_path, 'wb') as f:
            pickle.dump({
                'input_size':    input_size,
                'hidden_size':   256,
                'num_layers':    3,
                'lookback_period': LOOKBACK,
                'is_intraday':   True
            }, f)

        print(f"   Model  saved : {save_path}")
        print(f"   Scaler saved : {scaler_path}")
        print(f"   Config saved : {config_path}")

        if trainer.val_losses:
            best_val = min(trainer.val_losses)
            print(f"\n   Best Val Loss: {best_val:.6f}")

    print("\n" + "="*70)
    print("  INTRADAY TRAINING COMPLETE!")
    print("="*70)
    return trainer, history


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    import sys

    # Usage:
    #   python model_trainer_optimized.py           -> trains DAILY model
    #   python model_trainer_optimized.py intraday  -> trains INTRADAY model

    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "daily"

    print("\n" + "="*70)
    if mode == "intraday":
        print("  MODE: INTRADAY LSTM TRAINING (30-minute candles)")
    else:
        print("  MODE: DAILY LSTM TRAINING")
    print("="*70)

    token_info = load_token_from_file()
    if not token_info:
        print("\n No access token found. Please run authentication first.")
        sys.exit(1)

    # ---- Nifty 50 symbols ----
    training_symbols = [
        # Banking & Financial
        "NSE_EQ|INE040A01034",  # HDFCBANK
        "NSE_EQ|INE090A01021",  # ICICIBANK
        "NSE_EQ|INE062A01020",  # SBIN
        "NSE_EQ|INE238A01034",  # AXISBANK
        "NSE_EQ|INE176A01028",  # KOTAKBANK
        "NSE_EQ|INE774A01016",  # BAJFINANCE
        # IT
        "NSE_EQ|INE467B01029",  # TCS
        "NSE_EQ|INE009A01021",  # INFY
        "NSE_EQ|INE860A01027",  # HCLTECH
        "NSE_EQ|INE158A01026",  # WIPRO
        "NSE_EQ|INE277A01024",  # TECHM
        # Oil & Gas
        "NSE_EQ|INE002A01018",  # RELIANCE
        "NSE_EQ|INE213A01029",  # ONGC
        # Consumer
        "NSE_EQ|INE030A01027",  # HINDUNILVR
        "NSE_EQ|INE154A01025",  # ITC
        "NSE_EQ|INE192A01025",  # TITAN
        # Auto
        "NSE_EQ|INE101A01026",  # MARUTI
        "NSE_EQ|INE917I01010",  # TATAMOTORS
        "NSE_EQ|INE758T01015",  # BAJAJ-AUTO
        # Pharma
        "NSE_EQ|INE089A01023",  # SUNPHARMA
        "NSE_EQ|INE019A01038",  # CIPLA
        # Infra
        "NSE_EQ|INE081A01012",  # TATASTEEL
        "NSE_EQ|INE114A01011",  # JSWSTEEL
        "NSE_EQ|INE245A01021",  # ULTRACEMCO
        # Telecom
        "NSE_EQ|INE397D01024",  # BHARTIARTL
        "NSE_EQ|INE155A01022",  # ASIANPAINT
    ]

    try:
        if mode == "intraday":
            # ---- INTRADAY: 30-min candles, last 60 calendar days ----
            print(f"\n Fetching 30-min data for {len(training_symbols)} stocks...")
            df = prepare_training_data(training_symbols, interval='30minute', days=60)

            trainer, history = train_lstm_intraday(
                df,
                epochs=20,
                batch_size=64,
                test_size=0.15,
                learning_rate=0.0005,
                save_path='data/trained_models/lstm_intraday.pth'
            )
            print("\n Intraday model saved to: data/trained_models/lstm_intraday.pth")
            print("   The AI engine will now load this model for intraday mode.")

        else:
            # ---- DAILY: original behaviour ----
            print(f"\n Fetching daily data for {len(training_symbols)} stocks...")
            df = prepare_training_data(training_symbols, interval='day', days=1000)

            trainer, history = train_lstm_model_optimized(
                df,
                epochs=100,
                batch_size=64,
                test_size=0.15,
                learning_rate=0.0005,
                save_path='data/trained_models/lstm_best.pth'
            )
            print("\n Daily model saved to: data/trained_models/lstm_best.pth")

        print("\n Training complete!")

    except Exception as e:
        print(f"\n Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

