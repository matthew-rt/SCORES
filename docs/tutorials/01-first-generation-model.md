# Tutorial 1 — Your first generation model

**Goal:** simulate an offshore wind farm from historic weather data and
understand what SCORES gives you back.

**You need:** the wind weather dataset in `data/wind/`
(see [Getting the data](../getting-started/data.md)).

## 1.1 Pick your sites

Weather data is organised by *site* — a grid point of the weather dataset
(ERA5) with an index, listed in `data/wind/site_locs.csv`:

```text
Site,Latitude,Longitude
16,50.0,1.875
21,50.5,-5.0
22,50.5,-4.375
...
```

Each site has a matching hourly data file, e.g. `data/wind/364.csv`. Pick a
few site indexes near where your hypothetical wind farm lives (you can plot
`site_locs.csv` with pandas/matplotlib to see the grid). To use every
available site, pass `sites="all"`.

## 1.2 Build the model

```python
from generation import OffshoreWindModel

osw = OffshoreWindModel(
    year_min=2015,
    year_max=2016,
    sites=[119, 174, 178],
    data_path="data/wind/",
    turbine_size=10,          # MW; must exist in the technical params file
)
```

Watch what happens on the first run: the model reads each site's CSV,
builds a power curve for a 10 MW turbine (cut-in/cut-out speeds, rotor
diameter and hub height from `params/Offshore_wind_params.xlsx`), adjusts
wind speeds to hub height, and converts speed to power for every hour of
2015–2016. It then saves the normalised result to `stored_model_runs/`.

Construct the same model again — it returns almost instantly, loading the
cache instead. Pass `force_run=True` to recompute.

!!! note
    By default one turbine is placed at each site (`n_turbine=None`), so
    this model is a 30 MW fleet. Pass e.g. `n_turbine=[20, 30, 10]` for a
    600 MW fleet spread over the three sites.

## 1.3 Look at the output

```python
import matplotlib.pyplot as plt

p = osw.power_out            # list of hourly MW values, len = hours in 2015-16
plt.plot(p[:24*14])          # first fortnight
plt.ylabel("Output (MW)"); plt.xlabel("Hour")
plt.show()

print(f"Load factor : {osw.get_load_factor():.1f} %")
print(f"Annual cost : £{osw.get_cost():,.0f}/yr")
print(f"LCOE        : £{osw.calculate_LCOE():.2f}/MWh")
```

Typical GB offshore sites give load factors in the 40–55% range; if you see
something wildly different, check your data files and site indexes.

`get_diurnal_profile()` returns the average output for each hour of the
day — flat-ish for wind, strongly peaked for solar.

## 1.4 Rescale without re-running

The hourly *shape* is fixed by the weather; capacity is a linear scaling:

```python
p_20gw = osw.scale_output(20_000)   # rescale the fleet to 20 GW
```

`scale_output` sets `power_out_scaled` (and returns it as an array). All
cost methods use the scaled capacity, so `osw.get_cost()` now prices a
20 GW fleet. This is exactly what the system-level optimisers do while
searching over capacities — the expensive weather processing happens once.

## 1.5 Things to try

- **Commissioning dates:** rebuild with
  `year_online=[2015, 2015, 2016], month_online=[1, 7, 1]` and watch the
  load factor account for sites that were not yet operational.
- **Turbine size:** compare `turbine_size=10` with `turbine_size=15` at the
  same sites (each size caches separately).
- **Onshore and solar:** `OnshoreWindModel(..., data_path="data/wind/",
  turbine_size=3.5)` and `SolarModel(..., data_path="data/solar/")` follow
  the same pattern (solar's first run is noticeably slower).

## Complete listing

```python
from generation import OffshoreWindModel
import matplotlib.pyplot as plt

osw = OffshoreWindModel(year_min=2015, year_max=2016,
                        sites=[119, 174, 178],
                        data_path="data/wind/", turbine_size=10)

print(f"Load factor : {osw.get_load_factor():.1f} %")
print(f"LCOE        : £{osw.calculate_LCOE():.2f}/MWh")

plt.plot(osw.power_out[:24*14])
plt.ylabel("Output (MW)"); plt.xlabel("Hour of 2015")
plt.title("Offshore wind, first fortnight of 2015")
plt.show()
```

**Next:** [Tutorial 2 — Adding storage](02-adding-storage.md), where this
wind fleet meets GB demand.
