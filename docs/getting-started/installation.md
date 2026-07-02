# Installation

## Requirements

- **Python 3.10+** (the pinned package versions in `requirements.txt`
  require a reasonably recent Python; 3.11 or 3.12 are known-good choices).
- A linear-programming solver if you want to use the Pyomo optimisation in
  `opt_con_class.py` (see [Solvers](#solvers) below).

## Set up a virtual environment

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

`requirements.txt` pins the following packages:

| Package | Used for |
| --- | --- |
| `numpy`, `pandas`, `scipy` | Core numerics throughout. |
| `matplotlib` | All plotting. |
| `Pyomo` | The linear programme in `opt_con_class.py`. |
| `highspy` | The HiGHS solver, usable by Pyomo (`solver="highs"`). |
| `pyDOE` | Latin hypercube sampling in `system.py` optimisation routines. |
| `Cartopy`, `geopandas`, `pyproj` | Map drawing in `maps.py`. |
| `scikit_learn` | Regression utilities used by some analysis scripts. |
| `tqdm` | Progress bars. |

!!! note "Packages used but not listed in requirements.txt"
    A few tracked scripts need packages that are *not* in
    `requirements.txt`: `openpyxl` (needed by `pandas.read_excel` to read
    the `params/*.xlsx` cost files), `seaborn` (`loadfactorplotter.py`,
    `excelloaderexample.py`), `cdsapi` and `netCDF4` (downloading and
    converting ERA5 weather data — see
    [Getting the data](data.md)), `requests` (the legacy MERRA-2 download
    scripts in `data/getting data/`), and `tkinter`
    (`GUIrun.py`; ships with most Python installs). Install them as needed:

    ```bash
    pip install openpyxl seaborn cdsapi netCDF4 requests
    ```

## Solvers

The simulation-only parts of SCORES (generation models, storage
`charge_sim`, `ElectricitySystem`) need **no solver**. The linear programme
(`System_LinProg_Model`) needs one of:

- **GLPK** — the default (`Run_Sizing(solver="glpk")`).
  Install with `brew install glpk` (macOS), `apt install glpk-utils`
  (Debian/Ubuntu), or `conda install -c conda-forge glpk`.
- **HiGHS** — already available via the `highspy` pip package; pass
  `solver="highs"`.
- Any other solver Pyomo supports (CBC, Gurobi, CPLEX, ...) if you have it
  installed; pass its Pyomo name as the `solver` argument.

You can verify your solver installation with
`Userguide_Examples/Pyomo_Example.py`, which builds and solves a tiny
standalone Pyomo problem.

## Files you need that are not in the repository

Two kinds of input are required at runtime but are **not** committed:

1. **Weather data** — hourly wind speed / irradiance CSVs per site. See
   [Getting the data](data.md).
2. **Parameter spreadsheets** — the default constructor arguments of most
   models point at `params/SCORES Cost assumptions.xlsx`,
   `params/Offshore_wind_params.xlsx`, `params/Onshore_wind_params.xlsx`
   and `params/Storage_technical_assumptions.xlsx`. The `params/` folder is
   not tracked by git, so a fresh clone will not have it — obtain it from a
   colleague or recreate it (the expected format is described in
   [Cost parameters](../user-guide/costs.md)). Alternatively, pass explicit
   `capex=`, `opex=`, `lifetime=`, `hurdlerate=` etc. keyword arguments and
   set `cost_params_file=None` / `technical_params_file=None`.

## Checking the installation

With weather data in place (see the next page), this should run without
error:

```python
from generation import OffshoreWindModel

osw = OffshoreWindModel(
    year_min=2015, year_max=2015,
    sites=[178], data_path="data/wind/",
)
print(f"Load factor: {osw.get_load_factor():.1f}%")
```
