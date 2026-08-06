#!/usr/bin/env python3
"""
Step 1 – Extract Open Boundary Coordinates

Extracts open boundary node coordinates from a Blue Kenue mesh (.ngh)
and a TELEMAC boundary condition file (.cli). The resulting point file
is used in the subsequent wave hindcast extraction workflow.
"""

import pandas as pd

# ----------------------------------------------------
# === 0) Input/Output ===
# ----------------------------------------------------

path_ngh   = ".ngh"
path_cli   = ".cli"

path_randknoten = "boundary_knots.csv"
path_tada       = "merged.csv"
path_final      = "coordinates_spectra_to_impose.dat"


# ----------------------------------------------------
# === 1) create boundary points ===
# ----------------------------------------------------

rows = []
with open(path_ngh, "r") as f:
    lines = f.readlines()

data_lines = lines[3:]  # jump first 3 colums

for line in data_lines:
    parts = line.strip().split()
    if len(parts) < 5:
        continue

    values = []
    for x in parts:
        try:
            v = float(x)
            if v.is_integer():
                v = int(v)
            values.append(v)
        except:
            continue

    if len(values) > 3 and values[3] == 1:
        rows.append(values)

df = pd.DataFrame(rows)
df.columns = [f"col_{i}" for i in range(len(df.columns))]

# nur erste 3 Spalten behalten
df = df[["col_0", "col_1", "col_2"]]

df.to_csv(path_randknoten, index=False)


# ----------------------------------------------------
# === 2) CLI connected to boundary points ===
# ----------------------------------------------------

rows = []
with open(path_cli, "r", errors="ignore") as f:
    for line in f:
        line = line.split("#")[0].strip()
        if not line:
            continue
        rows.append(line.split())

max_cols = max(len(r) for r in rows)
df_cli = pd.DataFrame(rows, columns=[f"cli_col_{i}" for i in range(max_cols)])

df_cli = df_cli[["cli_col_0", "cli_col_1", "cli_col_2", "cli_col_11", "cli_col_12"]]

df_cli = df_cli.rename(columns={
    "cli_col_0": "col1",
    "cli_col_1": "col2",
    "cli_col_2": "col3",
    "cli_col_11": "col12",
    "cli_col_12": "col13"
})

df_cli["id"] = pd.to_numeric(df_cli["col12"], errors="coerce")

df_csv = pd.read_csv(path_randknoten)
df_csv = df_csv.iloc[:, [0, 1, 2]]
df_csv.columns = ["id", "x", "y"]

merged = df_cli.merge(df_csv, on="id", how="left")
merged.to_csv(path_tada, index=False)


# ----------------------------------------------------
# === 3) create final points  ===
# ----------------------------------------------------

df = pd.read_csv(path_tada)

df_filtered = df[df["col1"].astype(str).str.startswith("5")].copy()

cols_to_drop = ["col1", "col2", "col3", "col13"]
df_filtered = df_filtered.drop(columns=cols_to_drop)

df_filtered["PointID"] = df_filtered["col12"]
df_filtered["Z"] = 0

df_final = df_filtered[["PointID", "x", "y", "Z"]]

num_points = len(df_final)

output_lines = [f"{num_points} 0"]
for _, row in df_final.iterrows():
    output_lines.append(f"{int(row['PointID'])} {row['x']} {row['y']} {row['Z']}")

with open(path_final, "w") as f:
    f.write("\n".join(output_lines))

print("DONE! final_points.txt was created:")
print(path_final)
