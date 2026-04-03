
import pandas as pd
import numpy as np
import os
import time
import pickle
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error
import torch
import torch.nn as nn

DATA_DIR   = "data"
MODELS_DIR = "models"
VENTANA    = 20   # cuántas velas mira para predecir
EPOCHS     = 50
INTERVALO  = 300  # reentrenar cada 5 minutos

os.makedirs(MODELS_DIR, exist_ok=True)

# =========================
# MODELO LSTM
# =========================
class ModeloLSTM(nn.Module):
    def __init__(self, entrada=4, ocultas=64, capas=2):
        super().__init__()
        self.lstm = nn.LSTM(entrada, ocultas, capas, batch_first=True)
        self.fc   = nn.Linear(ocultas, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])

# =========================
# PREPARAR DATOS
# =========================
def preparar_datos(df):
    cols  = ["open", "high", "low", "close"]
    data  = df[cols].values.astype(float)

    scaler = MinMaxScaler()
    data   = scaler.fit_transform(data)

    X, y = [], []
    for i in range(VENTANA, len(data)):
        X.append(data[i - VENTANA:i])
        y.append(data[i, 3])  # predice el close

    X = torch.tensor(np.array(X), dtype=torch.float32)
    y = torch.tensor(np.array(y), dtype=torch.float32).unsqueeze(1)
    return X, y, scaler

# =========================
