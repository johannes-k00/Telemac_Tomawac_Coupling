"""
Step 5 – Generate SERAFIN Wind Field

Prerequisites:
- A TELEMAC mesh (.slf)
- A wind time series (.lqd)
- ppSELAFIN

This script converts wind speed and direction into Cartesian wind
components (U, V), maps them uniformly onto the computational mesh
and exports a TELEMAC/TOMAWAC-compatible SERAFIN wind field.
"""
# ----------------------------------------------------
# === 0) Input/Output ===
# ----------------------------------------------------

import sys
import numpy as np
import struct

pputils_path = "pputils"
if pputils_path not in sys.path:
    sys.path.append(pputils_path)

from ppmodules.selafin_io_pp import ppSELAFIN

# --- DATEINAMEN ---
input_txt = "wind.lqd"
mesh_file = "mesh.slf"
output_slf = "Wind_export.slf"


def pol_to_cart(speed, direction_deg):
    rad = np.radians(direction_deg)
    u = speed * np.sin(rad)
    v = speed * np.cos(rad)
    return u, v

# ----------------------------------------------------
# === 1) Load Mesh ===
# ----------------------------------------------------
slf_mesh = ppSELAFIN(mesh_file)
if hasattr(slf_mesh, 'readHeader'): slf_mesh.readHeader()
elif hasattr(slf_mesh, 'read_header'): slf_mesh.read_header()

try:
    npoin, nelem = slf_mesh.npoin, slf_mesh.nelem
    x_coords, y_coords = slf_mesh.x, slf_mesh.y
    ikle, ipobo = slf_mesh.ikle, slf_mesh.ipobo
except AttributeError:
    npoin, nelem = slf_mesh.getNPOIN(), slf_mesh.getNELEM()
    x_coords, y_coords = slf_mesh.getMeshX(), slf_mesh.getMeshY()
    ikle, ipobo = slf_mesh.getIKLE(), slf_mesh.getIPOBO()

print(f"Mesh extracted ({npoin} knots).")

# ----------------------------------------------------
# === 2) Load Wind ===
# ----------------------------------------------------
wind_data = None
try:
    with open(input_txt, 'r') as f:
        lines = f.readlines()

    data_lines = lines[4:]
    raw_data = []
    for line in data_lines:
        if line.strip():
            raw_data.append([float(x) for x in line.split()])

    wind_data = np.array(raw_data)
    print(f"Loaded {len(wind_data)} timesteps.")

except Exception as e:
    print(f":Error while loading wind data {e}")

# ----------------------------------------------------
# === 3) Write ===
# ----------------------------------------------------

if wind_data is not None:
    with open(output_slf, 'wb') as f:
        # 1. Header (Big-Endian)
        # Titel (80) + Record Delimiter
        title = "WIND FIELD FOR TELEMAC".ljust(72) + "SERAFIN "
        f.write(struct.pack('>i80si', 80, title.encode('ascii'), 80))

        # Number of variables (2: Wind X, Wind Y)
        f.write(struct.pack('>i2ii', 8, 2, 0, 8))

        # 2. Variablenames & Units
        # every variable has 32 Byte (16 Name + 16 Unit)
        vnames = [
            'WIND ALONG X    '.encode('ascii'),
            'WIND ALONG Y    '.encode('ascii')
        ]
        vunit = 'M/S             '.encode('ascii')

        for name in vnames:
            f.write(struct.pack('>i32si', 32, name + vunit, 32))

        # 3. Netz-Parameter (IPARAM)
        # 10 Integer-Werte
        ipar = [int(nelem), int(npoin), 3, 1, 0, 0, 0, 0, 0, 0]
        f.write(struct.pack('>i10ii', 40, *ipar, 40))

        # IKLE & IPOBO Header
        f.write(struct.pack('>i4ii', 16, int(nelem), int(npoin), 3, 1, 16))

        # 4. IKLE (connectivity)
        if ikle.ndim == 1:
            ikle_matrix = ikle.reshape((int(nelem), 3))
        else:
            ikle_matrix = ikle

        ikle_safe = np.clip(ikle_matrix, 0, npoin - 1)
        ikle_to_write = (ikle_safe + 1).T.flatten().astype('>i4')

        size_ikle = len(ikle_to_write) * 4
        f.write(struct.pack('>i', size_ikle) + ikle_to_write.tobytes() + struct.pack('>i', size_ikle))

        # 5. IPOBO (boundaryknots-vactor)
        size_ipobo = len(ipobo) * 4
        f.write(struct.pack('>i', size_ipobo) + ipobo.astype('>i4').tobytes() + struct.pack('>i', size_ipobo))

        # 6. Coodinates (X and Y seperated)
        size_coords = int(npoin) * 4
        f.write(struct.pack('>i', size_coords) + x_coords.astype('>f4').tobytes() + struct.pack('>i', size_coords))
        f.write(struct.pack('>i', size_coords) + y_coords.astype('>f4').tobytes() + struct.pack('>i', size_coords))

        # 7. timeframe
        for row in wind_data:
            t = float(row[0])
            u_val, v_val = pol_to_cart(row[1], row[2])

            # timestep (4 Byte Float)
            f.write(struct.pack('>ifi', 4, t, 4))

            # Windfileds (U und V) for all knots (NPOIN)
            u_f = np.full(int(npoin), u_val, dtype='>f4')
            v_f = np.full(int(npoin), v_val, dtype='>f4')

            for field in [u_f, v_f]:
                f.write(struct.pack('>i', size_coords) + field.tobytes() + struct.pack('>i', size_coords))
    print(f"Wind field successfully written to: {output_slf}")
else:
    print("No wind data available. Output file was not created.")
     
