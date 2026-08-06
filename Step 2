"""
Step 2 – Apply Coordinate Shift

Applies a user-defined coordinate offset to the boundary points.
This optional shift can be used to move the spectral extraction
points into valid wet cells of the hindcast grid. The required
offset depends on the study area and hindcast dataset.
"""
# ----------------------------------------------------
# === 0) Input/Output ===
# ----------------------------------------------------
coordinates_spectra_to_impose = "coordinates_spectra_to_impose.dat"
coordinates_spectra_to_impose_moved = "coordinates_spectra_to_impose_moved.dat"

# User-defined coordinate offset (m)
shift_x = -2.0
shift_y = 0.0


# ----------------------------------------------------
# === 1) read data ===
# ----------------------------------------------------
with open(coordinates_spectra_to_impose, 'r') as f:
    lines = f.readlines()

header = lines[0] # make sure header is correct e.g. 133 0
data = lines[1:]

new_lines = [header]

for line in data:
    parts = line.split()
    if len(parts) < 3: continue

    id_pt = parts[0]
    x = float(parts[1])
    y = float(parts[2])
    z = parts[3]

    # --- Adjust position of the points ---
    # if E/W has to be moved, this is where you do it
    
    new_x = x + shift_x
    # if N/S has to be moved, this is where you do it
    new_y = y + shift_y

    new_lines.append(f"{id_pt} {new_x:.6f} {new_y:.6f} {z}\n")

# ----------------------------------------------------
# === 2) write data ===
# ----------------------------------------------------
with open(coordinates_spectra_to_impose_moved, 'w') as f:
    f.writelines(new_lines)

print("dataset coordinates_spectra_to_impose_moved.dat was created!")
     
