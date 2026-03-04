import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import DataLoader, TensorDataset
import joblib

df = pd.read_csv("clean_ibtracs.csv")

features = [
    "USA_PRES",
    "USA_WIND",
    "pressure_trend",
    "wind_trend",
    "LAT",
    "LON"
]

targets = [
    "future_pressure_6h",
    "future_wind_6h",
    "future_lat_6h",
    "future_lon_6h"
]

scaler_X = MinMaxScaler()
scaler_y = MinMaxScaler()

X_scaled = scaler_X.fit_transform(df[features])
y_scaled = scaler_y.fit_transform(df[targets])

joblib.dump(scaler_X, "scaler_X.pkl")
joblib.dump(scaler_y, "scaler_y.pkl")

SEQ_LEN = 5
X_seq = []
y_seq = []

for i in range(len(X_scaled) - SEQ_LEN):
    X_seq.append(X_scaled[i:i+SEQ_LEN])
    y_seq.append(y_scaled[i+SEQ_LEN])

X_seq = np.array(X_seq)
y_seq = np.array(y_seq)

X_tensor = torch.tensor(X_seq, dtype=torch.float32)
y_tensor = torch.tensor(y_seq, dtype=torch.float32)

dataset = TensorDataset(X_tensor, y_tensor)
loader = DataLoader(dataset, batch_size=64, shuffle=True)

class CycloneLSTM(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(6, 64, 2, batch_first=True)
        self.fc = nn.Linear(64, 4)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])

model = CycloneLSTM()
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

for epoch in range(10):
    for xb, yb in loader:
        preds = model(xb)
        loss = criterion(preds, yb)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    print(f"Epoch {epoch+1}, Loss: {loss.item():.5f}")

torch.save(model.state_dict(), "cyclone_lstm_multioutput.pth")

print("Model trained and saved.")
