import torch
from pathlib import Path
path = Path('data/trained_models/lstm_best.pth')
if not path.exists():
    raise FileNotFoundError(path)
chk = torch.load(path, map_location='cpu')
print('keys:', list(chk.keys()))
print('train_losses len', len(chk.get('train_losses', [])))
print('val_losses len', len(chk.get('val_losses', [])))
print('first_val_loss', chk.get('val_losses', [None])[0])
print('final_val_loss', chk.get('val_losses', [None])[-1])
print('best_val_loss', min(chk.get('val_losses', [float(1e9)])))
print('final_train_loss', chk.get('train_losses', [None])[-1])
print('model_state_dict_params', sum(p.numel() for p in chk['model_state_dict'].values()))
