"""
Model Trainer
-------------
Script to train LSTM model on historical data.
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


def prepare_training_data(symbols, interval='day', days=500):
    """
    Fetch and prepare training data from multiple symbols.
    
    Args:
        symbols: List of stock symbols
        interval: Data interval
        days: Number of days of historical data
        
    Returns:
        Combined DataFrame
    """
    print(f"Fetching data for {len(symbols)} symbols...")
    all_data = []
    
    for symbol in symbols:
        print(f"  Fetching {symbol}...")
        df = fetch_historical_data(symbol, interval=interval, days=days)
        if not df.empty:
            df['symbol'] = symbol
            all_data.append(df)
    
    if not all_data:
        raise ValueError("No data fetched!")
    
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"✅ Fetched {len(combined_df)} data points")
    
    return combined_df


def train_lstm_model(df, epochs=50, batch_size=32, test_size=0.2, 
                     learning_rate=0.001, save_path='data/trained_models/lstm_best.pth'):
    """
    Train LSTM model on historical data.
    
    Args:
        df: Historical OHLCV data
        epochs: Number of training epochs
        batch_size: Batch size
        test_size: Validation split ratio
        learning_rate: Learning rate
        save_path: Path to save trained model
        
    Returns:
        Trained model and training history
    """
    print("\n" + "="*60)
    print("LSTM MODEL TRAINING")
    print("="*60)
    
    # Feature engineering
    print("\n1. Feature Engineering...")
    fe = FeatureEngineer(lookback_period=60)
    df_features = fe.prepare_features(df)
    
    print(f"   Features shape: {df_features.shape}")
    print(f"   Number of features: {len(df_features.columns)}")
    
    # Create sequences
    print("\n2. Creating sequences...")
    X, y, scaler, feature_cols = fe.create_sequences(df_features, target_col='close')
    
    print(f"   Sequences: X={X.shape}, y={y.shape}")
    print(f"   Feature columns: {len(feature_cols)}")
    
    # Train-test split
    print("\n3. Splitting data...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, shuffle=False  # Don't shuffle time series
    )
    
    print(f"   Train: {X_train.shape}, Test: {X_test.shape}")
    
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
    
    # Create model
    print("\n4. Creating LSTM model...")
    input_size = X.shape[2]  # Number of features
    model = LSTMPredictor(input_size=input_size, hidden_size=128, num_layers=2, dropout=0.2)
    
    print(f"   Input size: {input_size}")
    print(f"   Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Train
    print("\n5. Training...")
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    trainer = LSTMTrainer(model, learning_rate=learning_rate, device=device)
    
    history = trainer.train(train_loader, test_loader, epochs=epochs, patience=10)
    
    # Save final model
    print(f"\n6. Saving model to {save_path}...")
    trainer.save_model(save_path)
    
    # Save scaler and feature columns
    import pickle
    scaler_path = save_path.replace('.pth', '_scaler.pkl')
    with open(scaler_path, 'wb') as f:
        pickle.dump({'scaler': scaler, 'feature_cols': feature_cols}, f)
    
    print(f"✅ Scaler saved to {scaler_path}")
    
    print("\n" + "="*60)
    print("TRAINING COMPLETE!")
    print("="*60)
    
    return trainer, history


if __name__ == "__main__":
    print("LSTM Model Training Script")
    print("="*60)
    
    # Check if token exists
    token_info = load_token_from_file()
    if not token_info:
        print("❌ No access token found. Please run authentication first.")
        sys.exit(1)
    
    # Define training symbols
    training_symbols = [
        "NSE_EQ|INE467B01029",  # TCS
        "NSE_EQ|INE002A01018",  # RELIANCE
        "NSE_EQ|INE009A01021",  # INFY
        "NSE_EQ|INE238A01034",  # AXISBANK
    ]
    
    try:
        # Fetch data
        df = prepare_training_data(training_symbols, interval='day', days=500)
        
        # Train model
        trainer, history = train_lstm_model(
            df,
            epochs=50,
            batch_size=32,
            test_size=0.2,
            learning_rate=0.001
        )
        
        print("\n✅ Model training successful!")
        print("   Model saved to: data/trained_models/lstm_best.pth")
        print("   You can now use this model in the AI decision engine.")
        
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
