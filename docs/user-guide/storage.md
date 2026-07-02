# Storage models

Storage lives in `storage.py`. A `StorageModel` describes one storage
technology; `MultipleStorageAssets` wraps a portfolio of them and simulates
their combined operation against a surplus time series.

## StorageModel (base class)

Key constructor arguments (all costs can come from the
[cost spreadsheets](costs.md) or be given explicitly):

| Argument | Meaning |
| --- | --- |
| `capacity` | Installed energy capacity (MWh). Default 1 (i.e. "per-MWh" until `set_capacity` is called). |
| `eff_in`, `eff_out` | Charge / discharge efficiency, % (0–100). |
| `self_dis` | Self-discharge, % per month. |
| `max_c_rate`, `max_d_rate` | Max charge/discharge rate as % of capacity per hour, defined **grid-side**. |
| `storage_param_entry`, `charge_param_entry`, `discharge_param_entry` | Rows of the cost spreadsheet for the storage medium, charging equipment and discharging equipment (e.g. `"Salt Cavern"`, `"PEM"`, `"Hydrogen CCGT"`). |
| `storageCapex/FixedOpex/VarOpex/lifetime`, `chargeCapex/...`, `dischargeCapex/...` | Explicit cost overrides (storage per MWh; charge/discharge equipment per MW). |
| `hurdleRate` | Discount rate used to annuitise capex. |
| `initial_charge` | Starting state of charge, 0–1. |
| `storagelimits`, `chargelimits`, `dischargelimits` | `[min, max]` bounds used by the linear-programme optimiser. |

Separating the *storage medium* (£/MWh) from the *charge* and *discharge
equipment* (£/MW) lets technologies like hydrogen — cheap cavern storage,
expensive electrolysers and turbines — be represented properly. The linear
programme sizes all three independently.

### Simulation methods

| Method | What it does |
| --- | --- |
| `charge_sim(surplus, t_res=1, start_up_time=0, ...)` | Simulates the store hour by hour against a surplus (MW) series: charges when surplus is positive, discharges when negative. Returns the reliability achieved (% of demand energy met). |
| `size_storage(surplus, reliability, ...)` | Bisection search for the capacity (MWh) that achieves a target reliability. Returns `np.inf` if `max_capacity` is insufficient. |
| `analyse_usage()` | Returns energy in, energy out and cycle counts from the last simulation. |
| `get_cost()` | Annualised cost (£/yr) at current capacity, including throughput-based variable costs. |
| `plot_timeseries(start, end)` | Plots state of charge (and charging behaviour) from the last simulation or optimisation. |
| `reset()` / `set_capacity(mwh)` | Clear usage counters / change capacity. |

## Provided technologies

### BatteryStorageModel

Li-ion battery with hard-coded 2020-era defaults: 95%/95% efficiencies, 2%
per month self-discharge, £391/kWh storage capex, 15-year life, max
charge/discharge 25% of capacity per hour, 8% hurdle rate. Pass arguments
to override.

### HydrogenStorageModel

Hydrogen chain read from the cost spreadsheets by default: salt-cavern
storage (`"Salt Cavern"`), PEM electrolysis charging (`"PEM"`), hydrogen
CCGT discharge (`"Hydrogen CCGT"`), with technical parameters (efficiencies
and rates) from `params/Storage_technical_assumptions.xlsx`.

### ThermalStorageModel

!!! danger "Currently broken"
    In the current version, `ThermalStorageModel` passes positional
    arguments matching an old version of the `StorageModel` constructor,
    so building one crashes. Until fixed, construct a plain `StorageModel`
    with thermal parameters instead.

## MultipleStorageAssets

Wraps a list of `StorageModel`s into one dispatchable portfolio:

```python
from storage import (BatteryStorageModel, HydrogenStorageModel,
                     MultipleStorageAssets)

stores = MultipleStorageAssets(
    [BatteryStorageModel(capacity=100_000),      # 100 GWh
     HydrogenStorageModel(capacity=1_000_000)],  # 1 TWh
    c_order=[0, 1],   # charge the battery first
    d_order=[0, 1],   # discharge the battery first
)
```

- `c_order` / `d_order` set the priority order for charging and
  discharging under "ordered" operation (defaults: list order).
- `DispatchableAssetList` optionally supplies `DispatchableGenerator`s (in
  merit order) that cover deficits the stores cannot.
- `Interconnector` optionally allows imports/exports.

### Operating the portfolio

| Method | What it does |
| --- | --- |
| `charge_sim(surplus, ...)` | Ordered-priority hourly simulation of the whole portfolio; returns reliability. |
| `causal_system_operation(demand, power, c_order, d_order, Mult_aggEV, start, end, ...)` | Hour-by-hour operation **without foresight**, including EV fleets and optional dispatchable assets. Returns a results DataFrame (reliability, energy flows). |
| `non_causal_system_operation(demand, power, Mult_aggEV, start, end, ...)` | Operation **with perfect foresight**: builds and solves a linear programme for the operational decisions (needs a solver). |
| `size_storage(surplus, reliability, ...)` | Bisection sizing of total capacity at fixed relative sizes. |
| `analyse_usage()` | Per-store energy in/out and cycles. |

The causal/non-causal pair is useful for quantifying the value of
foresight: the same assets, demand and weather, operated naively versus
optimally.

## Example: size a battery for 99% reliability

```python
import numpy as np
from generation import OffshoreWindModel
from storage import BatteryStorageModel
from fns import get_GB_demand

demand = np.array(get_GB_demand(2013, 2019, list(range(1, 13))))
wind = OffshoreWindModel(year_min=2013, year_max=2019, sites="all",
                         data_path="data/wind/")
surplus = wind.scale_output(120_000) - demand    # 120 GW of wind

b = BatteryStorageModel()
needed = b.size_storage(surplus, reliability=99, req_res=1e3)
print(f"{needed/1e3:.1f} GWh of battery storage required")
print(b.analyse_usage())
```
