import pandas as pd

print("Loading IBTrACS dataset...")

df = pd.read_csv("ibtracs.NI.list.v04r01.csv", low_memory=False)

# Select required columns
df = df[[
    "SID",
    "ISO_TIME",
    "LAT",
    "LON",
    "USA_WIND",
    "USA_PRES"
]]

# Strip spaces
df["ISO_TIME"] = df["ISO_TIME"].astype(str).str.strip()

# Convert datetime safely
df["ISO_TIME"] = pd.to_datetime(df["ISO_TIME"], errors="coerce")

# Convert numeric columns safely
df["LAT"] = pd.to_numeric(df["LAT"], errors="coerce")
df["LON"] = pd.to_numeric(df["LON"], errors="coerce")
df["USA_WIND"] = pd.to_numeric(df["USA_WIND"], errors="coerce")
df["USA_PRES"] = pd.to_numeric(df["USA_PRES"], errors="coerce")

# Drop rows with missing important values
df = df.dropna(subset=["ISO_TIME", "LAT", "LON", "USA_WIND", "USA_PRES"])

# Sort properly
df = df.sort_values(["SID", "ISO_TIME"])

print("Creating 6-hour future targets...")

# 6 hours ahead (IBTrACS is 3-hour interval)
df["future_pressure_6h"] = df.groupby("SID")["USA_PRES"].shift(-2)
df["future_wind_6h"] = df.groupby("SID")["USA_WIND"].shift(-2)
df["future_lat_6h"] = df.groupby("SID")["LAT"].shift(-2)
df["future_lon_6h"] = df.groupby("SID")["LON"].shift(-2)

# Drop rows without future values
df = df.dropna()

# Now trends (will work because numeric)
df["pressure_trend"] = df.groupby("SID")["USA_PRES"].diff().fillna(0)
df["wind_trend"] = df.groupby("SID")["USA_WIND"].diff().fillna(0)

# Save cleaned dataset
df.to_csv("clean_ibtracs.csv", index=False)

print("✅ Dataset cleaned successfully.")
print("Final shape:", df.shape)
