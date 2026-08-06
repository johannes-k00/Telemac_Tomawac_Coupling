# Wave Spectra & Wind Forcing Pipeline for TELEMAC-2D / TOMAWAC Coupling

This pipeline automates the data preparation workflow for coupled **TELEMAC-2D** (hydrodynamics) and **TOMAWAC** (spectral wave model) modelling. It extracts spatial boundary nodes, queries global/regional wave hindcast datasets (NetCDF), generates 2D spectral boundary forcing files (`.spe`), and constructs spatially uniform binary SERAFIN wind fields (`.slf`).
The generated files can be used to impose a wave spectrum on the boundary in **TOMAWAC**.

---

## Overview of Pipeline Steps

```text
[Mesh & Boundary Files (.ngh, .cli)]
              │
              ▼
   Step 1: Extract Open Boundary Coordinates
              │
              ▼
   Step 2: Apply Coordinate Shift (Shift Boundary into Hindcast Coverage)
              │
              ▼
   Step 3: Extract and Process Wave Hindcast Time Series
              │
              ▼
   Step 4: Generate 2D JONSWAP Boundary Spectrum (.spe) for TOMAWAC
              │
              ▼
   Step 5: Convert Wind Data (.lqd) into SERAFIN Wind Field (.slf)
```
---

## Detailed Workflow

### Step 1: Extract Open Boundary Coordinates
* **Input:** Blue Kenue Mesh file (`.ngh`) and Boundary Condition file (`.cli`).
* **Processing:**
  * Extracts all mesh nodes marked as boundary nodes from the .ngh mesh file.
  * Reads the TELEMAC boundary condition file (.cli) and identifies the nodes belonging to the open boundary (boundary type beginning with 5, e.g. 5444).
  * Matches boundary node IDs with their mesh coordinates.
  * Writes the coordinates into a point file formatted for the subsequent spectral extraction workflow.
* **Output:** `boundary_knots.csv`, `merged.csv`, `coordinates_spectra_to_impose.dat`

### Step 2: Apply Coordinate Shift
* **Input:** `coordinates_spectra_to_impose.dat`
* **Processing:**
  * Applies a user-defined coordinate offset (Δx, Δy) to all boundary points.
  * This optional shift can be used to move the spectral extraction points slightly inside the available hindcast grid or away from coastline/grid-edge cells, ensuring that valid wave data are extracted for every boundary node.
  * The required offset depends on the study area and the underlying wave hindcast dataset.
* **Output:** `coordinates_spectra_to_impose_moved.dat`

### Step 3: Extract and Process Wave Hindcast Time Series
* **Input:** `coordinates_spectra_to_impose_moved.dat` and CMEMS Wave Hindcast NetCDF (`.nc`).
* **Processing:**
  * Transforms the hindcast grid from WGS84 (EPSG:4326) to UTM Zone 32N (EPSG:25832).
  * Locates the nearest hindcast grid cell for each boundary point using a cKDTree nearest-neighbour search.
  * Extracts significant wave height (Hs), peak wave period (Tp), and mean wave direction (θ) for every boundary point and timestep.
  * Interpolates the extracted time series to a user-defined temporal resolution (e.g. 15 min). Wave directions are interpolated using vector components to avoid 0°/360° discontinuities.
  * Selects a user-defined simulation time window (center_time ± hours).
  * Converts timestamps into relative simulation time (time_seconds).
  * Fills missing values (NaN) by assigning a small minimum wave height (Hs = 0.02 m) and copying Tp and wave direction from a user-defined reference boundary point.
* **Output:** `extracted_timeseries_points_interpolatet_window.csv`

### Step 4: Generate 2D JONSWAP Boundary Spectrum (`.spe`)
* **Prerequisite:** A dummy TOMAWAC spectrum file (dummy.spe) must be generated beforehand. It is used as a template for the SELAFIN mesh and header information.
* **Input:** Interpolated time series CSV and a dummy TOMAWAC spectrum file (`dummy.spe`).
* **Processing:**
  * Reads the processed wave time series for all boundary points.
  * Uses the dummy TOMAWAC spectrum file to obtain the required mesh and SELAFIN header information.
  * Computes a 1D JONSWAP spectrum (γ = 3.3) for each boundary point and timestep using MHKiT.
  * Applies a cos² directional spreading function to construct a two-dimensional directional wave spectrum.
  * Formats the spectrum variable names according to the TOMAWAC convention (FxxxxxPT2Dxxxxxx).
  * Writes the resulting spectra as a binary SELAFIN (.spe) file that can be used as a TOMAWAC spectral boundary condition.
* **Output:** `boundary_jonswap.spe`

### Step 5: Convert Wind Data to SERAFIN Wind Field (`.slf`)
* **Input:** Time series wind file (`.lqd`) and TELEMAC mesh file (`.slf`).
* **Processing:**
  * Reads the wind time series containing wind speed and direction.
  * Converts the polar wind data (speed, direction) into Cartesian wind components (U, V).
  * Reads the TELEMAC mesh and its topology.
  * Assigns the wind components uniformly to every mesh node for each timestep, creating a spatially uniform wind field.
  * Writes the resulting wind field as a binary SERAFIN (.slf) file compatible with TELEMAC-2D and TOMAWAC.
* **Output:** `wind_export.slf`

---

## Requirements
* numpy
* pandas
* scipy
* xarray
* pyproj
* mhkit
* ppSELAFIN (pputils)

---

## Note / Disclaimer

> **Full disclosure:** I'm actually a total Python noob and don't really have a clue about coding... 
> But somehow, through trial, error, willpower, the loss of my sanity (and a lot of magic), this pipeline actually works for me (hopefully)!

## Acknowledgements
> Special thanks to Taoan from the OpenTelemac Forum, whose shared code and explanations on spectral boundary conditions were extremely helpful during the development of this workflow.
>
> https://www.opentelemac.org/index.php/assistance/forum5/19-tomawac/7657-wave-series-as-boundary-condition?start=50


