"""
LSTM Price Predictor
--------------------
Neural network model for predicting stock prices using LSTM.
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Tuple
import os


class LSTMPredictor(nn.Module):
    """
    LSTM-based price prediction model.
    """
    
    def __init__(self, input_size, hidden_size=128, num_layers=2, dropout=0.2):
        """
        Args:
            input_size: Number of input features
            hidden_size: Number of LSTM hidden units
            num_layers: Number of LSTM layers
            dropout: Dropout rate
        """
        super(LSTMPredictor, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True
        )
        
        # Fully connected layers
        self.fc1 = nn.Linear(hidden_size, 64)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(64, 1)
        
    def forward(self, x):
        """
        Forward pass.
        
        Args:
            x: Input tensor of shape (batch_size, sequence_length, input_size)
            
        Returns:
            Predicted price
        """
        # LSTM forward
        lstm_out, _ = self.lstm(x)
        
        # Take the last time step
        last_output = lstm_out[:, -1, :]
        
        # Fully connected layers
        out = self.fc1(last_output)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.fc2(out)
        
        return out


class LSTMTrainer:
    """
    Trainer class for LSTM model.
    """
    
    def __init__(self, model, learning_rate=0.001, device='cpu'):
        """
        Args:
            model: LSTM model instance
            learning_rate: Learning rate for optimizer
            device: 'cpu' or 'cuda'
        """
        self.model = model.to(device)
        self.device = device
        self.criterion = nn.MSELoss()
        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        self.train_losses = []
        self.val_losses = []
        
    def train_epoch(self, train_loader):
        """Train for one epoch."""
        self.model.train()
        epoch_loss = 0
        
        for batch_X, batch_y in train_loader:
            batch_X = batch_X.to(self.device)
            batch_y = batch_y.to(self.device)
            
            # Forward pass
            predictions = self.model(batch_X)
            loss = self.criterion(predictions.squeeze(), batch_y)
            
            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            
            epoch_loss += loss.item()
        
        return epoch_loss / len(train_loader)
    
    def validate(self, val_loader):
        """Validate the model."""
        self.model.eval()
        val_loss = 0
        
        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                batch_X = batch_X.to(self.device)
                batch_y = batch_y.to(self.device)
                
                predictions = self.model(batch_X)
                loss = self.criterion(predictions.squeeze(), batch_y)
                val_loss += loss.item()
        
        return val_loss / len(val_loader)
    
    def train(self, train_loader, val_loader, epochs=50, patience=10):
        """
        Train the model with early stopping.
        
        Args:
            train_loader: Training data loader
            val_loader: Validation data loader
            epochs: Maximum number of epochs
            patience: Early stopping patience
            
        Returns:
            Training history
        """
        best_val_loss = float('inf')
        patience_counter = 0
        
        print(f"Training LSTM on {self.device}...")
        
        for epoch in range(epochs):
            train_loss = self.train_epoch(train_loader)
            val_loss = self.validate(val_loader)
            
            self.train_losses.append(train_loss)
            self.val_losses.append(val_loss)
            
            print(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}")
            
            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                # Save best model
                self.save_model('data/trained_models/lstm_best.pth')
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    print(f"Early stopping at epoch {epoch+1}")
                    break
        
        print(f"✅ Training complete! Best val loss: {best_val_loss:.6f}")
        return {'train_losses': self.train_losses, 'val_losses': self.val_losses}
    
    def predict(self, X):
        """
        Make predictions.
        
        Args:
            X: Input tensor or numpy array
            
        Returns:
            Predictions as numpy array
        """
        self.model.eval()
        
        if isinstance(X, np.ndarray):
            X = torch.FloatTensor(X)
        
        X = X.to(self.device)
        
        with torch.no_grad():
            predictions = self.model(X)
        
        return predictions.cpu().numpy()
    
    def save_model(self, path):
        """Save model to disk."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'train_losses': self.train_losses,
            'val_losses': self.val_losses
        }, path)
    
    def load_model(self, path):
        """Load model from disk."""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.train_losses = checkpoint.get('train_losses', [])
        self.val_losses = checkpoint.get('val_losses', [])


if __name__ == "__main__":
    print("Testing LSTM Predictor...")
    
    # Create dummy data
    batch_size = 32
    sequence_length = 60
    input_size = 20
    
    X_dummy = torch.randn(batch_size, sequence_length, input_size)
    
    # Create model
    model = LSTMPredictor(input_size=input_size, hidden_size=128, num_layers=2)
    
    # Forward pass
    output = model(X_dummy)
    
    print(f"Input shape: {X_dummy.shape}")
    print(f"Output shape: {output.shape}")
    print(f"Model parameters: {sum(p.numel() for p in model.parameters())}")
    print("✅ LSTM model test passed!")
