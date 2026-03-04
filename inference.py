import torch
import joblib
import numpy as np

try:
    import pandas as pd  # optional, only used if scaler has feature names
except Exception:
    pd = None


class CycloneLSTM(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = torch.nn.LSTM(input_size=6, hidden_size=64, num_layers=2, batch_first=True)
        self.fc = torch.nn.Linear(64, 4)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])


# -----------------------------
# Load model + scalers (once)
# -----------------------------
model = CycloneLSTM()
model.load_state_dict(torch.load("cyclone_lstm_multioutput.pth", map_location="cpu"))
model.eval()

scaler_X = joblib.load("scaler_X.pkl")
scaler_y = joblib.load("scaler_y.pkl")


def _build_input_for_scaler(input_data: dict):
    """Return input in the exact format the scaler expects (DataFrame if feature names exist, else ndarray)."""
    values = [
        float(input_data["LAT"]),
        float(input_data["LON"]),
        float(input_data["USA_WIND"]),
        float(input_data["USA_PRES"]),
        float(input_data["pressure_trend"]),
        float(input_data["wind_trend"]),
    ]

    # If scaler was fitted with feature names, pass a DataFrame with matching columns to avoid warnings/errors
    if hasattr(scaler_X, "feature_names_in_") and pd is not None:
        cols = list(scaler_X.feature_names_in_)
        mapping = {
            "LAT": values[0],
            "LON": values[1],
            "USA_WIND": values[2],
            "USA_PRES": values[3],
            "pressure_trend": values[4],
            "wind_trend": values[5],
        }
        row = [mapping.get(c, np.nan) for c in cols]
        return pd.DataFrame([row], columns=cols)

    # Fallback: plain ndarray
    return np.array([values], dtype=float)


def predict_6h(input_data: dict) -> dict:
    """Predict 6-hour ahead pressure, wind, and coordinates using the trained PyTorch LSTM."""
    X = _build_input_for_scaler(input_data)

    scaled_input = scaler_X.transform(X)

    # Shape for LSTM: (batch=1, seq_len=1, features=6)
    tensor_input = torch.from_numpy(scaled_input.astype(np.float32)).view(1, 1, 6)

    with torch.no_grad():
        scaled_output = model(tensor_input).numpy()

    output = scaler_y.inverse_transform(scaled_output)[0]

    return {
        "future_pressure": float(output[0]),
        "future_wind": float(output[1]),
        "future_lat": float(output[2]),
        "future_lon": float(output[3]),
    }
