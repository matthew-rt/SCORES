# Cost parameters

Generation and storage models read their default cost and technical
assumptions from Excel spreadsheets in `params/`. Any value can be
overridden with constructor keyword arguments, and the files can be
bypassed entirely (`cost_params_file=None`) by supplying everything
explicitly.

!!! warning "params/ is not in git"
    The `params/` folder is not tracked by the repository, so a fresh clone
    will not contain these files even though most constructors default to
    them. The formats below let you recreate them.

## SCORES Cost assumptions.xlsx

The main cost workbook. Three sheets — **Low**, **Medium**, **High** —
selected by the `cost_sensitivity` argument. Each sheet is a table indexed
by `Technology` and `Year` (selected by `cost_param_entry` and
`cost_year`), with columns:

| Column | Used for |
| --- | --- |
| `Technology` | Row key, e.g. `Offshore Wind`, `Onshore Wind`, `Large-scale Solar`, `CCGT H Class`, `Hydrogen CCGT`, `PEM`, `Alkaline`, `Salt Cavern`, `CCS Gas`, `Dedicated Biomass`, `Wave`, `Tidal Stream Energy`, `Floating Offshore Wind` |
| `Year` | Cost year, e.g. 2025, 2030, ... (selected by `cost_year`) |
| `Capex-£/kW` | Capital cost of power equipment (generators; storage charge/discharge equipment) |
| `Capex-£/MWh` | Capital cost of storage media |
| `Fixed Opex-£/MW/year`, `Fixed Opex-£/MWh/year` | Fixed operating costs |
| `Variable O&M-£/MWh` | Variable operating cost per unit of output/throughput |
| `Operating lifetime-years` | Asset lifetime used for annuitisation |
| `Hurdle Rate-%` | Discount rate used for annuitisation |
| `Efficiency-%` | Conversion efficiency (used for storage chains) |

### How costs are used

Capex is converted to an equivalent annual cost with the hurdle rate `r`
over the lifetime `n`:

```text
annual capex charge = capex × r / (1 − (1 + r)^−n)
fixed_cost (£/MW/yr or £/MWh/yr) = annual capex charge + fixed opex
```

A model's `get_cost()` is then
`fixed_cost × installed capacity + variable cost × annual output`, and
`ElectricitySystem.cost(x)` divides total annual cost by annual demand to
report **£/MWh of demand served**.

Generators also take `additional_variable_cost` (£/MWh) for fuel or carbon
costs on top of the spreadsheet value.

## Technical parameter files

### Offshore_wind_params.xlsx / Onshore_wind_params.xlsx

Turbine technical data indexed by `Turbine Size (MW)` (rows at 0.5 MW steps
from 2.0 MW), with columns:

`Cut in speed`, `Cut out speed`, `Rated wind speed`, `Rotor Diameter (m)`,
`Hub height (m)`

The wind models look up the row matching their `turbine_size` argument; a
missing size raises an exception telling you to add the row or pass the
parameters manually with `technical_params_file=None`.

### Storage_technical_assumptions.xlsx

Indexed by `Technology` with a `Technology type` column distinguishing
`Storage` / `Charge` / `Discharge` rows. Provides efficiencies,
self-discharge and max charge/discharge rates (e.g. `Li-Ion`,
`Salt Cavern`, `PEM`, `Hydrogen CCGT`).

## Overriding by keyword

```python
from generation import OffshoreWindModel

# Ignore the spreadsheets completely:
osw = OffshoreWindModel(
    sites=[119], year_min=2015, year_max=2015, data_path="data/wind/",
    cost_params_file=None,
    capex=1_500_000,      # £/MW
    opex=40_000,          # £/MW/yr
    variable_cost=3,      # £/MWh
    lifetime=25,
    hurdlerate=0.07,
    technical_params_file=None,
    rotor_diameter=190, rated_wind_speed=11,
    v_cut_in=3, v_cut_out=25, hub_height=110,
)
```

!!! note
    When `cost_params_file=None`, *all* of `capex`, `opex`,
    `variable_cost`, `lifetime` and `hurdlerate` must be given — missing
    ones currently produce a `NameError` rather than a helpful message.

## Sensitivity studies

Because `cost_sensitivity` ("Low"/"Medium"/"High") and `cost_year` are
plain constructor arguments, cost sensitivity runs are usually just a loop:

```python
for sens in ["Low", "Medium", "High"]:
    gen = OffshoreWindModel(..., cost_sensitivity=sens)
    ...
```

The cached weather run is reused, so only the cost arithmetic changes.
