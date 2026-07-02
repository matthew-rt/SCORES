# Troubleshooting

Common errors and their causes.

## Import and setup errors

**`ImportError: cannot import name 'OnshoreWindModel3600' from 'generation'`**
(also `OffshoreWindModel10000`, etc., including via `import maps`)
: The fixed-turbine-size classes were removed; turbine size is now the
  `turbine_size` argument of `OnshoreWindModel` / `OffshoreWindModel`.
  Older scripts (`example_scripts.py`, `LinProgOptExample.py`,
  `maps.py`) still import them. Replace
  `OnshoreWindModel3600(...)` with `OnshoreWindModel(turbine_size=3.6, ...)`.

**`ModuleNotFoundError: No module named 'loaderfunctions'`**
: The module file is `Loaderfunctions.py` (capital L). Case-insensitive
  filesystems (macOS, Windows) tolerate `import loaderfunctions`; Linux
  does not. Use `import Loaderfunctions`.

**`AttributeError: module 'generation' has no attribute 'generatordictionaries'`**
: Removed API, still called by `GUIrun.py` and `excelloaderexample.py`.
  Build models directly with `turbine_size=` instead.

**`FileNotFoundError: params/SCORES Cost assumptions.xlsx`**
: The `params/` folder is not in git. Obtain it separately or pass
  `cost_params_file=None` with explicit cost keyword arguments
  ([details](../user-guide/costs.md)).

**`ImportError: ... openpyxl ...` when models load cost files**
: `pip install openpyxl` (pandas needs it for `.xlsx`).

## Data errors

**`Exception: model can not be run without a data path`**
: No cached run exists for this exact model configuration, so the weather
  data is needed: pass `data_path="data/wind/"` (or wherever your data is).

**`FileNotFoundError: data/wind/364.csv`**
: The sites list references a site index with no data file. Check the
  files in your data folder against `site_locs.csv`, and remember each
  site needs its own `<index>.csv`.

**`ValueError: time data ... does not match format '%d/%m/%Y %H:%M'`**
: Your weather CSV's first data row has a different timestamp format from
  the layout the parser expects (labelled "MERRA 2 format" in the code,
  but required for ERA5-derived files too — see
  [Getting the data](../getting-started/data.md)). Note the bundled
  `example.csv` files themselves have a different format — they show the
  column layout, not the exact timestamp format.

**`Exception: supply and demand have different lengths`**
: Generators and the system were built with different year ranges (or one
  used a cached run made with different years/months). All generators and
  the demand series must cover identical hours.

**`KeyError` on demand years / empty demand**
: `data/demand.csv` covers 2013–2019 only. Supply your own `demand=` array
  for other years.

## Solver errors

**`ApplicationError: No executable found for solver 'glpk'`**
: GLPK is not installed or not on `PATH`. Install it, or use
  `Run_Sizing(solver="highs")` which uses the pip-installed `highspy`.

**LP takes forever / runs out of memory**
: Start with one weather year; use `Form_Model(timeresolution=24)` for
  scans; remember `Form_Model` is the slow step and parameter mutation
  avoids repeating it ([tutorial 4](../tutorials/04-linear-programming.md)).

## Suspicious results

**Load factors look wrong / division by zero in `get_load_factor()`**
: When a model is loaded from cache, `max_possible_output` is not
  reconstructed, so `get_load_factor()` divides by zero. Rebuild with
  `force_run=True` if you need load factors.

**Zero demand from `get_GB_demand`**
: The fourth positional argument is `elec_scaler`. Older examples pass
  `False` there (a leftover from an old signature), which multiplies
  demand by zero. Pass keyword arguments:
  `get_GB_demand(2015, 2015, list(range(1,13)), heat_demand=0, ev_demand=0)`.

**Stale results after changing weather data**
: Delete the matching cache files in `stored_model_runs/` — cached runs
  are keyed by sites/years/months, not by data contents.

**Optimiser returns a corner of the bounds**
: For the heuristic optimiser, widen `min_gen_cap`/`max_gen_cap`; for the
  LP, check the `limits` on each generator and storage object — an active
  bound usually means the model wanted more than you allowed.
