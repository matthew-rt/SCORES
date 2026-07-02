# Generation models

All generation technologies live in `generation.py` and inherit from
`GenerationModel`. A model instance represents a fleet of one technology at
one or more geographic sites, simulated over a range of historic weather
years at hourly resolution.

## Common constructor arguments

Every subclass accepts (a superset of) these arguments:

| Argument | Default | Meaning |
| --- | --- | --- |
| `sites` | `["all"]` | List of site indexes (integers matching `<site>.csv` files in `data_path`), or `"all"` to use every site in `site_locs.csv`. |
| `year_min`, `year_max` | 2013, 2019 | First and last weather year (inclusive). |
| `months` | 1–12 | Months to include. Sub-year runs are only allowed when `year_min == year_max`. |
| `data_path` | `""` | Folder containing the per-site weather CSVs. Required unless a cached run exists. |
| `save_path` | `"stored_model_runs/"` | Cache folder. |
| `save` / `force_run` | `True` / `False` | Whether to write the cache / ignore an existing cache. |
| `cost_params_file` | `"params/SCORES Cost assumptions.xlsx"` | Cost spreadsheet; see [Cost parameters](costs.md). Set to `None` to supply costs directly. |
| `cost_param_entry` | technology-specific | Row of the cost spreadsheet to use (e.g. `"Offshore Wind"`). |
| `cost_sensitivity` | `"Medium"` | Sheet of the cost spreadsheet (`Low`/`Medium`/`High`). |
| `cost_year` | 2025 | Year column of the cost spreadsheet. |
| `capex`, `opex`, `variable_cost`, `lifetime`, `hurdlerate` | `None` | Explicit overrides for values from the cost spreadsheet. |
| `year_online`, `month_online` | `None` | Per-site commissioning dates; output before this date is zero and excluded from load-factor calculations. |
| `limits` | `[0, 1000000]` | `[min, max]` installed MW, used as bounds by the linear-programme optimiser. |

## What a model gives you

After construction (which runs the simulation or loads a cache):

| Attribute / method | Meaning |
| --- | --- |
| `power_out` | Hourly output (MW) at the model's built capacity, over the full period. |
| `scale_output(mw)` | Linearly rescales output to `mw` installed capacity; sets and returns `power_out_scaled`. |
| `get_load_factor()` | Average load factor in % over the period. |
| `get_cost()` | Annualised cost (£/yr) at the scaled capacity: annuitised capex + fixed opex + variable costs. |
| `calculate_LCOE()` | Levelised cost of energy (£/MWh). |
| `get_diurnal_profile()` | Mean output for each hour of the day. |

Costs are annuitised with the hurdle rate:
`fixed_cost = capex * r / (1 - (1+r)^-lifetime) + opex` (per MW per year).

## Weather-driven technologies

### OffshoreWindModel / OnshoreWindModel

Simulates wind farms from hourly wind-speed data.

- `turbine_size` (MW; offshore default 10, onshore default 3.5) selects a
  row of the technical-parameters spreadsheet
  (`params/Offshore_wind_params.xlsx`), which provides rotor diameter,
  cut-in/cut-out/rated speeds and hub height. Any of these can be
  overridden by keyword.
- A power curve is generated from these parameters (fixed power
  coefficient, cubic below rated), or supply your own via `power_curve`.
- Wind speeds are shear-adjusted from `data_height` (default 100 m) to hub
  height using coefficient `alpha` (default 0.143).
- `n_turbine` sets the number of turbines per site (default: one each).
- `era_mean_wind_speed` / `gwa_mean_wind_speed` optionally rescale each
  site's speeds to Global Wind Atlas means (bias correction).

!!! warning
    `OnshoreWindModel`'s default `technical_params_file` points at
    `params/Offshore_wind_params.xlsx` (the offshore file) even though an
    `Onshore_wind_params.xlsx` exists. Pass the file explicitly if the
    distinction matters to your study.

### SolarModel

Simulates solar PV farms from hourly irradiance data (kJ/m²), computing
panel output from solar geometry (declination, hour angle, incident angle
on tilted panels) plus panel efficiency. Key arguments: `plant_capacities`
(MW per site), `tilt` (default 22°), `orient` (default 0 = south),
`efficiency` (0.17), `performance_ratio` (0.85) and `area_factor`.
Noticeably slower than the wind models on first run.

### NuclearModel / GeothermalModel

Baseload technologies producing a flat output at a fixed load factor
(`loadfactor`, default 0.77 for nuclear) rather than weather-driven
profiles. Capacity is set per site via `capacities` (MW).

### TidalStreamTurbineModel

Simulates tidal stream turbines from current-speed data (`data/tidal/`).
Convenience subclasses pin particular deployment scenarios:
`TidalStreamTurbineModel_P1/P2/P3` and `TidalStreamTurbine_VR_1_0` …
`_VR_3_5` (velocity-ratio variants).

## Profile-based and dispatchable technologies

### DispatchableGenerator

A generic dispatchable plant (e.g. gas CCGT, biomass). It has a capacity
and costs, and a `dispatch(t, demand)` method used by the storage/system
layers to fill remaining deficits in merit order. Used as
`DispatchableAssetList` entries in `MultipleStorageAssets` /
`ElectricitySystem`, and as `dispatchable_list` entries in the linear
programme (optionally with energy limits).

### Interconnector

Like a dispatchable generator but bidirectional: `dispatch(t, demand)`
imports during deficits and `export(t, surplus)` exports during surpluses.

## Caching details

The cache filename encodes technology code, turbine size, sites, years and
months (`fns.get_filename`). Two things to watch:

- Runs with `sites="all"` and runs with an explicit list of the same sites
  cache under different names.
- The cache stores output normalised to installed capacity; when a cached
  run is loaded the model's `total_installed_capacity` is set to 1, and
  `get_load_factor()` cannot be used (rebuild with `force_run=True` if you
  need load factors).

## Example

```python
from generation import OnshoreWindModel

w = OnshoreWindModel(
    year_min=2013, year_max=2019,
    sites=[23, 24, 106],
    turbine_size=5.0,
    data_path="data/wind/",
    year_online=[2013, 2015, 2017],   # staggered commissioning
    month_online=[1, 6, 1],
)
print(w)                              # summary string
print(w.get_load_factor())
profile = w.scale_output(20_000)      # rescale fleet to 20 GW
```
