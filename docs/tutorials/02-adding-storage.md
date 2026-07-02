# Tutorial 2 — Adding storage

**Goal:** turn generation and demand into a *surplus*, simulate a battery
against it, and size storage to hit a reliability target.

**You need:** tutorial 1 completed (wind data in place).

## 2.1 The surplus

Storage in SCORES is always simulated against a **surplus** series:
generation minus demand, in MW, hourly. Positive surplus can charge
storage; negative surplus (a deficit) is met by discharging.

```python
import numpy as np
from generation import OffshoreWindModel
from fns import get_GB_demand

ymin, ymax = 2015, 2016

wind = OffshoreWindModel(year_min=ymin, year_max=ymax,
                         sites="all", data_path="data/wind/")
demand = np.array(get_GB_demand(ymin, ymax, list(range(1, 13))))

power = wind.scale_output(100_000)      # a 100 GW fleet
surplus = power - demand

print(f"Hours in deficit: {(surplus < 0).mean()*100:.0f}%")
```

`get_GB_demand` reads `data/demand.csv` (2013–2019). Note the argument
order if you go beyond the basics: `(year_min, year_max, months,
elec_scaler, heat_demand, ev_demand)` — `elec_scaler` comes **before** the
heat and EV totals.

## 2.2 Simulate a battery

```python
from storage import BatteryStorageModel

battery = BatteryStorageModel(capacity=50_000)    # 50 GWh
reliability = battery.charge_sim(surplus)
print(f"Reliability: {reliability:.2f}% of demand met")
print(battery.analyse_usage())
battery.plot_timeseries(0, 24*28)                 # first four weeks of SOC
```

`charge_sim` walks through the hours: charging when surplus is positive
(limited by `max_c_rate` and remaining headroom, losing `eff_in`),
discharging when negative (limited by `max_d_rate` and stored energy,
losing `eff_out`), and applying self-discharge. The return value is the
percentage of demand energy met over the period.

## 2.3 Size storage for a target

Rather than guessing capacities, ask for the capacity that achieves a
reliability:

```python
battery = BatteryStorageModel()
needed = battery.size_storage(surplus, reliability=99, req_res=1e3)
print(f"99% reliability needs {needed/1e3:,.0f} GWh of battery")
```

`size_storage` bisects on capacity until the achieved reliability matches
the target to within `req_res` MWh, returning `np.inf` if even
`max_capacity` (default 100 TWh) is not enough. Try a few reliability
targets — the capacity explodes as you approach 100%, which is the core
finding SCORES exists to quantify.

!!! tip "start_up_time"
    Reliability counting can exclude the first `start_up_time` hours so the
    arbitrary initial state of charge doesn't distort results. The GB
    system class uses 90 days.

## 2.4 Combine technologies

Batteries are efficient but expensive per MWh; hydrogen is cheap per MWh
but lossy. A portfolio uses each where it is strongest:

```python
from storage import (BatteryStorageModel, HydrogenStorageModel,
                     MultipleStorageAssets)

stores = MultipleStorageAssets(
    [BatteryStorageModel(capacity=30_000),       # 30 GWh
     HydrogenStorageModel(capacity=10_000_000)], # 10 TWh
    c_order=[0, 1],    # battery charges first...
    d_order=[0, 1],    # ...and discharges first
)
print(f"Combined reliability: {stores.charge_sim(surplus):.2f}%")
print(stores.analyse_usage())
```

With this ordering the battery handles the daily churn (many shallow
cycles) while hydrogen absorbs the seasonal imbalance (few deep cycles).
Swap the orders and compare `analyse_usage()` to see why ordering matters.

!!! warning
    `ThermalStorageModel` is currently broken (constructor mismatch);
    stick to battery and hydrogen, or build a plain `StorageModel` with
    thermal parameters.

## 2.5 Things to try

- Sweep wind capacity from 60 to 140 GW and plot required storage vs
  installed wind — the generation/storage trade-off curve.
- Compare `HydrogenStorageModel(cost_sensitivity="Low")` vs `"High"` costs
  with `get_cost()`.

**Next:** [Tutorial 3 — A whole-system study](03-whole-system.md), which
automates this loop and adds costs.
