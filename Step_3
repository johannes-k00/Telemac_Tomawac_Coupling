"""
Step 3 – Extract and Process Wave Hindcast Time Series

Prerequisites:
- Run Step 1 and Step 2 first.
- A wave hindcast NetCDF dataset is required.
- Coordinate transformation is configured for UTM Zone 32N (EPSG:25832)
  and may need to be adapted for other study areas.

This script extracts wave parameters from the hindcast, interpolates the
time series, selects a user-defined simulation window and exports the
processed data for spectral boundary generation.
"""


# ----------------------------------------------------
# === 0) Input/Output ===
# ----------------------------------------------------


# --- INPUT FILES ---
coord_file = "coordinates_spectra_to_impose_moved.dat"
nc_file = ".nc"


# --- OUTPUT FILES (1. Extraction, 2. Interpolation, 3. Zeitfenster) ---
out_file_raw = "extracted_timeseries_points.csv"                            #
out_file_interp = "extracted_timeseries_points_interpolatet.csv"            #
out_file_window = "extracted_timeseries_points_interpolatet_window.csv"     # dataset with points and interpolated values for higher temporal resolution an

# --- TIMEFRAME ---
center_time = "2023-10-20 21:45:00"
hours_before = 48
hours_after = 16

# --- INTERPOLATIONS-SETTINGS ---
interp_interval = "15min"   # z.B. "10min", "30min", "5min"


# --- REPLACING NANs ---
reference_id = 88971 # User-defined reference point used to fill missing Tp and direction values


# ----------------------------------------------------
# === 1) Extract Hindcast ===
# ----------------------------------------------------
import pandas as pd
import xarray as xr
import numpy as np
from pyproj import Transformer
from scipy.spatial import cKDTree

pts = pd.read_csv(
    coord_file,
    sep=r"\s+",
    skiprows=1,
    header=None,
    names=["id", "x", "y", "z"]
)
print(">>> points loaded:", pts.shape)

# ----------------------------------------------------
# === 3) Create spec_id ===
# ----------------------------------------------------
pts = pts.sort_values("id").reset_index(drop=True)
pts["spec_id"] = np.arange(1, len(pts) + 1)

print(">>> spec_id added.")
print(pts.head())

ds = xr.open_dataset(nc_file)
print(">>> Hindcast loaded")
print("Variablen:", list(ds.data_vars))

hs_var = "VHM0"
tp_var = "VTPK"
dir_var = "VPED"

transformer = Transformer.from_crs("EPSG:4326", "EPSG:25832", always_xy=True)   #CRS

lon = ds["longitude"].values
lat = ds["latitude"].values

lon2d, lat2d = np.meshgrid(lon, lat)
xg, yg = transformer.transform(lon2d, lat2d)

print(">>> Hindcast-Raster sucessfully transformed!")

grid_points = np.column_stack((xg.ravel(), yg.ravel()))
tree = cKDTree(grid_points)

pts_xy = pts[["x", "y"]].values
dist, idx = tree.query(pts_xy)

lat_idx = idx // xg.shape[1]
lon_idx = idx % xg.shape[1]

pts["lat_idx"] = lat_idx
pts["lon_idx"] = lon_idx

print(">>> Gridpoints assigned!")

records = []
for _, p in pts.iterrows():
    i = int(p.lat_idx)
    j = int(p.lon_idx)

    rec = pd.DataFrame({
        "id": p.id,
        "spec_id": p.spec_id,
        "x": p.x,
        "y": p.y,
        "time": ds.time.values,
        "hs": ds[hs_var][:, i, j].values,
        "tp": ds[tp_var][:, i, j].values,
        "dir": ds[dir_var][:, i, j].values,
    })
    records.append(rec)

df = pd.concat(records, ignore_index=True)
print(">>> Extraction finished!")
print(df.head())

df.to_csv(out_file_raw, index=False)
print(">>> Data saved to:", out_file_raw)


# ----------------------------------------------------
# === 4) Interpolate ===
# ----------------------------------------------------
import pandas as pd
import numpy as np

df = pd.read_csv(out_file_raw)
df["time"] = pd.to_datetime(df["time"])
df = df.sort_values(["id", "time"])
print(">>> Original data loaded:", df.shape)

def interpolate_direction(series):
    u = np.cos(np.deg2rad(series))
    v = np.sin(np.deg2rad(series))

    idx = series.index

    u2 = pd.Series(u, index=idx).interpolate("linear")
    v2 = pd.Series(v, index=idx).interpolate("linear")

    dir_rad = np.arctan2(v2, u2)
    dir_deg = np.rad2deg(dir_rad)

    dir_deg = (dir_deg + 360) % 360
    return dir_deg

df_interpolated_list = []

for pid, group in df.groupby("id"):

    g = group.set_index("time")

    new_index = pd.date_range(
        start=g.index.min(),
        end=g.index.max(),
        freq=interp_interval
    )

    g2 = g.reindex(new_index)

    g2["hs"] = g2["hs"].interpolate("linear")
    g2["tp"] = g2["tp"].interpolate("linear")

    g2["dir"] = interpolate_direction(g2["dir"])

    g2["id"] = pid

    g2 = g2.reset_index().rename(columns={"index": "time"})

    df_interpolated_list.append(g2)

df_interpolated = pd.concat(df_interpolated_list, ignore_index=True)

df_interpolated["x"] = df_interpolated.groupby("id")["x"].ffill().bfill()
df_interpolated["y"] = df_interpolated.groupby("id")["y"].ffill().bfill()
df_interpolated["spec_id"] = df_interpolated.groupby("id")["spec_id"].ffill().bfill()


print(">>> Interpolation done:", df_interpolated.shape)
print(df_interpolated.head())

df_interpolated.to_csv(out_file_interp, index=False)
print(">>> Datsved under:", out_file_interp)


# ----------------------------------------------------
# === 5) Cut to Timeframe ===
# ----------------------------------------------------
df = pd.read_csv(out_file_interp)
df["time"] = pd.to_datetime(df["time"])

print(">>> Interpolated data loaded:", df.shape)

center_time = pd.to_datetime(center_time)
t_start = center_time - pd.Timedelta(hours=hours_before)
t_end   = center_time + pd.Timedelta(hours=hours_after)

print("\n>>> timeframe:")
print("Start:", t_start)
print("End :", t_end)

df_window = df[
    (df["time"] >= t_start) &
    (df["time"] <= t_end)
].copy()

print("\n>>> Filtered data:", df_window.shape)
print(df_window.head())

# ----------------------------------------------------
# === 6) Create Timesteps ===
# ----------------------------------------------------

unique_times = (
    df_window["time"]
    .drop_duplicates()
    .sort_values()
)
t0 = unique_times.min()

time_seconds = (unique_times - t0).dt.total_seconds()

time_to_sec = dict(zip(unique_times, time_seconds))

df_window["time_seconds"] = df_window["time"].map(time_to_sec)

# Adjust direction
df_window["dir_towards"] = (df_window["dir"] + 180) % 360  # necesarry??


# Adjust tp
# Peak frequency from peak period
#df_window["fp"] = 1.0 / df_window["tp"]

# Remove unused colums
df_window = df_window.drop(columns=["time", "dir"])



print("\n>>> Sekundenzeitachse ergänzt (pro Zeitschritt):")
print(df_window[["id", "time_seconds"]].head(10))

#fake data for nans
#ref_spec = (
#    df_window[df_window["id"] == 50234]
#    .set_index("time_seconds")[["hs", "tp", "dir_towards"]]
#)

#for col in ["hs", "tp", "dir_towards"]:
#    df_window[col] = df_window[col].fillna(
#        df_window["time_seconds"].map(ref_spec[col])
#    )

#print("NaNs after faking:")
#print(df_window[["hs", "tp", "dir_towards"]].isna().sum())

# ----------------------------------------------------
# === 7) Fill NAN ===
# ----------------------------------------------------

# 1. define the reference points for Tp and Dir
ref_spec = (
    df_window[df_window["id"] == reference_id]
    .set_index("time_seconds")[["hs", "tp", "dir_towards"]]
)

# set miniml value for hs
df_window["hs"] = df_window["hs"].fillna(0.02)

# tp and dir from reference point
for col in ["tp", "dir_towards"]:
    df_window[col] = df_window[col].fillna(
        df_window["time_seconds"].map(ref_spec[col])
    )

print("✅ NaNs corrected.")
print("   wind will push waves greatly now.")
# ----------------------------------------------------
# === 8) Export ===
# ----------------------------------------------------
df_window.to_csv(out_file_window, index=False)
print(">>> Data saved to:", out_file_window)


     
