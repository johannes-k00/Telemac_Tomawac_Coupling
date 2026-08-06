
"""
Step 4 – Generate TOMAWAC Boundary Spectrum

Prerequisites:
- Run Step 3 first.
- A dummy TOMAWAC spectrum file (dummy.spe) must be generated beforehand.
- MHKiT and ppSELAFIN are required.

This script generates a two-dimensional JONSWAP spectrum for each
boundary point and exports the result as a TOMAWAC-compatible
SELAFIN (.spe) boundary file.
"""

import numpy as np
import pandas as pd
import mhkit

from selafin_io_pp import ppSELAFIN

# ----------------------------------------------------
# === 0) Input/Output ===
# ----------------------------------------------------

csv_path = 'extracted_timeseries_points_interpolatet_window.csv'
dummy_path = 'dummy.spe'
output_path = 'boundary_jonswap.spe'

# ----------------------------------------------------
# === 1) Load Dummy Spectrum ===
# ----------------------------------------------------
slf = ppSELAFIN(dummy_path)
slf.readHeader()
slf.readTimes()
NELEM, NPOIN, NDP, IKLE, IPOBO, x, y = slf.getMesh()

# ----------------------------------------------------
# === 2) Load Wave Time Series ===
# ----------------------------------------------------
df = pd.read_csv(csv_path)
df.columns = [c.lower().strip() for c in df.columns]

# ----------------------------------------------------
# === 3) Create TOMAWAC Variable Names ===
# ----------------------------------------------------
first_time = df['time_seconds'].min()
unique_points = df[df['time_seconds'] == first_time].sort_values('spec_id')

new_var_names = []
for idx, row in unique_points.iterrows():
    s_id = int(row['spec_id'])
    p_id = int(row['id']) #  e.g. 50123.0
    # CREATES F + 5 ID + PT2D + 6 SPointID ( e.g 050123)
    name = f"F{s_id:05d}PT2D{p_id:06d}".ljust(16)
    new_var_names.append(name)

n_vars = len(new_var_names)

# ----------------------------------------------------
# === 4) Initialise Output SELAFIN ===
# ----------------------------------------------------
slf2 = ppSELAFIN(output_path)
slf2.setVarNames(new_var_names)
slf2.setVarUnits(slf.getVarUnits())
slf2.setIPARAM([1, 0, 0, 0, 0, 0, 0, 0, 0, 1])
slf2.setMesh(NELEM, NPOIN, NDP, IKLE, IPOBO, x, y)
slf2.writeHeader()

# ----------------------------------------------------
# === 5) Spectrum Settings ===
# ----------------------------------------------------
col_time = 'time_seconds'
col_id   = 'spec_id'
col_hs   = 'hs'
col_tp   = 'tp'
col_dir  = 'dir_towards'

# TOMAWAC frequency discretisation
f_vec = np.array([0.1 * (1.1**i) for i in range(36)]) #ADJUST(23=0.1/19=0.15)

# Direction bins (0–350° every 10°)
dirs_rad = np.radians(np.arange(0, 360, 10))
d_theta = np.radians(10)


# ----------------------------------------------------
# === 6) Generate Spectra ===
# ----------------------------------------------------
for t_val, group in df.groupby(col_time):
    data_step = np.zeros((n_vars, NPOIN), dtype=np.float32)

    for i in range(n_vars):
        s_id = i + 1
        try:
            row = group[group[col_id] == s_id].iloc[0]

            # 1. JONSWAP 1D
            spectrum = mhkit.wave.resource.jonswap_spectrum(f_vec, row[col_tp], row[col_hs], gamma=3.3)
            energy_1d = spectrum.values.flatten()

            # 2. DIRECTION (cos^2)
            ds = np.radians(row[col_dir])
            d_diff = (dirs_rad - ds + np.pi) % (2 * np.pi) - np.pi
            dt = np.where(np.abs(d_diff) <= np.pi/2, np.cos(d_diff)**2, 0)

            if np.sum(dt) > 0:
                dt = dt / (np.sum(dt) * d_theta)

            # WRITE 2D SPEKTRUM IN MATRIX
            data_step[i, :] = np.outer(energy_1d, dt).flatten()

        except (IndexError, KeyError):
            continue

    slf2.writeVariables(float(t_val), data_step)

# ----------------------------------------------------
# === 7) Finish ===
# ----------------------------------------------------

slf2.close()
print(f"\nBoundary spectrum successfully written to: {output_path}")
     
