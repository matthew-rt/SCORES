# Getting the data

SCORES compares historic weather against historic demand, so it needs
several input datasets. Some ship with the repository; the large weather
datasets must be downloaded separately.

## What ships with the repository

| File | Contents |
| --- | --- |
| `data/demand.csv` | Hourly GB electricity demand, **2013–2019**, columns `Day, HR, Demand (MW)` (dates formatted `01-JAN-2013`). Used by `fns.get_GB_demand()` and hence `ElectricitySystemGB`. |
| `data/ev_demand.csv` | Normalised daily EV charging profiles (weekday / Saturday / Sunday columns), used by `get_GB_demand()` when an `ev_demand` total is specified. |
| `data/daily_gas.csv` | Daily GB gas consumption (from 2016), used by heat-demand scaling. |
| `data/wind/site_locs.csv`, `data/solar/site_locs.csv`, `data/tidal/site_locs.csv` | Site index → latitude/longitude lookup tables for each weather dataset. |
| `data/wind/site_locs_incl_offshore.csv`, `data/solar/site_locs_incl_offshore.csv` | As above but including offshore points. |
| `data/wind/example.csv`, `data/solar/example.csv` | Small examples of the per-site weather file format. |

## Weather data (must be downloaded)

The generation models read **one CSV file per site**, named
`<site index>.csv` (e.g. `data/wind/364.csv`), from the folder you pass as
`data_path`. Each folder must also contain a `site_locs.csv` listing every
site with its latitude and longitude:

```text
Site,Latitude,Longitude
16,50.0,1.875
21,50.5,-5.0
...
```

!!! note "Onshore vs offshore site lists"
    The shipped `data/wind/site_locs.csv` lists **onshore** sites (indexes
    16–279); `site_locs_incl_offshore.csv` also covers offshore points
    (indexes 1–320). The models read whichever file is named
    `site_locs.csv` in your data folder, so for offshore wind studies make
    sure the offshore-inclusive list (and matching per-site data files)
    is in place — historical studies kept separate folders per dataset.

The per-site files are hourly time series. Whatever the weather source,
the parser expects:

- a header row, then one row per hour;
- **column 1**: a timestamp in `dd/mm/yyyy HH:MM` format (used only on the
  first row, to anchor the series in time);
- **column 3** (index 2): the value — wind speed in m/s (at 100 m for the
  default `data_height=100`) or solar irradiance in kJ/m².

(The code comments call this the "MERRA 2 format" — a historical label
from when SCORES used NASA's MERRA-2 reanalysis. The format applies to
ERA5-derived files too.)

!!! warning "The bundled example.csv files do not exactly match this format"
    `data/wind/example.csv` uses ISO timestamps (`2011-01-01 00:00:00`)
    rather than the `dd/mm/yyyy HH:MM` format the code parses, and
    `data/README.md` describes a two-column format while the code reads
    column index 2. Treat the code (`generation.py`, `run_model` methods)
    as the source of truth.

### Downloading ERA5 data from Copernicus

SCORES now uses **ERA5**, ECMWF's global reanalysis, available hourly
from 1940 to the present on a 0.25° grid, downloaded from the Copernicus
Climate Data Store (CDS). In outline:

1. Register for a (free) CDS account at
   [https://cds.climate.copernicus.eu](https://cds.climate.copernicus.eu),
   then install the API client (`pip install cdsapi`) and put your API key
   in `~/.cdsapirc` as described on the CDS site.
2. Request **"ERA5 hourly data on single levels"** for your years and a
   bounding box covering your study area, with the variables:
     - *wind*: `100m_u_component_of_wind` and `100m_v_component_of_wind`
       — combine as `speed = sqrt(u² + v²)` to get wind speed at 100 m,
       which matches the models' default `data_height=100`;
     - *solar*: `surface_solar_radiation_downwards` (`ssrd`) — hourly
       accumulations in J/m²; divide by 1000 for the kJ/m² the solar
       model expects.
3. Convert the downloaded netCDF into **one CSV per grid point** in the
   format above, plus a `site_locs.csv` mapping your chosen site indexes
   to the grid-point latitudes/longitudes.
4. Place the results in per-technology folders (e.g. `data/wind/`,
   `data/solar/`) together with the matching `site_locs.csv`.

There is currently no tracked ERA5 conversion script in the repository —
the legacy MERRA-2 scripts in `data/getting data/` (see below) show the
target CSV format and are easily adapted (`netCDF4` in, per-site CSV out).

!!! tip "Global Wind Atlas bias correction"
    ERA5 wind speeds can be biased at individual sites. The wind models
    accept `era_mean_wind_speed` and `gwa_mean_wind_speed` arrays
    (per site) to rescale each site's ERA5 speeds so their mean matches
    the [Global Wind Atlas](https://globalwindatlas.info/); see
    [Generation models](../user-guide/generation.md).

### Legacy: MERRA-2

Earlier versions of SCORES used NASA's MERRA-2 reanalysis, and two shipped
resources document that workflow: the PDF
**`Getting the Data Required to Run SCORES.pdf`** (step-by-step download
guide via a NASA EarthData account) and the scripts in
`data/getting data/`:

- `getNASA.py` — downloads `.nc4` files from an EarthData URL list;
- `NASA_wind.py` — converts netCDF wind components into per-site CSVs;
- `NASA_solar.py` — converts netCDF radiation files into per-site
  irradiance CSVs.

MERRA-2-derived CSVs remain fully usable — the model only cares about the
file format.

### Tidal data

`data/tidal/` contains a `site_locs.csv` for tidal sites, an example
current-speed file (`1.csv`), and two helper scripts
(`read_netCDF.py`, `find_largest_tidal.py`) for extracting tidal current
data from netCDF sources.

## Demand data

`ElectricitySystemGB` calls `fns.get_GB_demand(year_min, year_max, months,
elec_scaler, heat_demand, ev_demand)`, which reads `data/demand.csv`. The
shipped file covers **2013–2019**; simulations outside this range need
either your own demand file (pass a `demand=` list directly to the system
classes) or an extended `demand.csv` in the same format.

Optional extras in `get_GB_demand`:

- `heat_demand` (TWh/yr) — adds an electrified-heating profile scaled from
  the daily gas data.
- `ev_demand` (TWh/yr) — adds an unmanaged EV-charging profile from
  `data/ev_demand.csv`.
- `elec_scaler` — multiplies the underlying electricity demand (e.g. `1.1`
  for 10% demand growth).

## Cached model runs

The first time a generation model runs for a given combination of sites,
years and months, the resulting normalised power time series is written to
`stored_model_runs/` (the `save_path` argument). Later constructions of the
same model load the cached file instead of re-processing the weather data,
which is much faster. Pass `force_run=True` to ignore the cache, or
`save=False` to skip writing it.

!!! tip
    If you change the underlying weather data, or a run was interrupted,
    delete the matching file in `stored_model_runs/` — otherwise stale
    results will be silently loaded.
