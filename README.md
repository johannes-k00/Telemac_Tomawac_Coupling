### Wave Spectra and Windforcing Pipeline for TELEMAC-2D and TOMAWAC Coupling
Wave Spectra & Wind Forcing Pipeline for TELEMAC-2D / TOMAWAC Coupling
This automates the data preparation workflow for coupled TELEMAC-2D (hydrodynamics) and TOMAWAC (spectral wave model) simulations. It extracts spatial boundary nodes, queries global/regional wave hindcast datasets (NetCDF), generates 2D spectral boundary forcing files (.spe), and constructs spatially uniform binary SERAFIN wind fields (.slf).


### Overview of Pipeline Steps
[Mesh & Boundary Files (.ngh, .cli)]
              │
              ▼
   Step 1: Extract Open Boundary Nodes
              │
              ▼
   Step 2: Apply Coordinate Shift (Shift Boundary into Hindcast Coverage)
              │
              ▼
   Step 3: Extract NetCDF Hindcast, Interpolate & Window Time Series
              │
              ▼
   Step 4: Generate 2D JONSWAP Boundary Spectrum (.spe) for TOMAWAC
              │
              ▼
   Step 5: Convert Wind Data (.lqd) into SERAFIN Wind Field (.slf)

---

## Detailed Workflow

### Step 1: Extract Open Boundary Nodes
* **Input:** Blue Kenue Mesh file (`.ngh`) and Boundary Condition file (`.cli`).
* **Processing:** Scans the mesh for boundary type `5444` (boundary marker = 1) and matches node IDs with coordinates $(X, Y)$.
* **Output:** `randknoten.csv`, `merged.csv`, `coordinates_spectra.dat`

### Step 2: Apply Coordinate Shift
* **Input:** `coordinates_spectra.dat`
* **Processing:** Shifts boundary coordinates by defined offsets (`shift_x`, `shift_y`) to ensure all nodes fall well inside the wet grid cells of the NetCDF hindcast.
* **Output:** `coordinates_spectra_moved.dat`

### Step 3: Extract NetCDF Hindcast, Interpolate & Window Time Series
* **Input:** `coordinates_spectra_moved.dat` and CMEMS Wave Hindcast NetCDF (`.nc`).
* **Processing:**
  * Transforms NetCDF coordinates (WGS84) to UTM Zone 32N and matches nodes using k-d trees (`cKDTree`).
  * Extracts $H_s$, $T_p$, and Mean Wave Direction ($\theta$).
  * Interpolates temporal data (e.g., to `15min` steps) using vector-based directional interpolation to prevent $0^\circ \leftrightarrow 360^\circ$ wrap-around errors.
  * Filters a specific storm window (`center_time ± hours`) and normalizes time into relative seconds (`time_seconds`).
  * Handles edge NaNs physically ($H_s = 0.02\text{ m}$).
* **Output:** `extracted_timeseries_points_interpolatet_window.csv`

### Step 4: Generate 2D JONSWAP Boundary Spectrum (`.spe`)
* **Input:** Interpolated time series CSV and a dummy TOMAWAC spectrum file (`dummy.spe`).
* **Processing:** Computes 1D JONSWAP spectra ($\gamma = 3.3$) via `mhkit`, applies a $\cos^2$ directional spreading function, formats variable naming (`F...PT2D...`), and writes the binary SELAFIN boundary file.
* **Output:** `boundary_jonswap.spe`

### Step 5: Convert Wind Data to SERAFIN Wind Field (`.slf`)
* **Input:** Time series wind file (`.lqd`) and TELEMAC mesh file (`.slf`).
* **Processing:** Converts polar wind inputs ($S, \theta$) into Cartesian components ($U, V$), maps them onto the full computational mesh, and writes a Big-Endian SERAFIN binary file.
* **Output:** `wind_sturm_final.slf`

---





### Note / Disclaimer

> **Full disclosure:** I'm actually a total Python noob and don't really have a deep clue about Python coding... 
> But somehow, through trial, error, sheer willpower (and a lot of magic), this pipeline actually works flawlessly (hopefully)! 
