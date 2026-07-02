# Tutorial 4 — Sizing with the linear programme

**Goal:** formulate system sizing as a Pyomo linear programme, solve it
exactly, and run fast sensitivity sweeps by mutating parameters instead of
rebuilding the model.

**You need:** a solver — GLPK (`brew install glpk` / `apt install
glpk-utils`) or HiGHS (already installed via `highspy`). Verify with
`Userguide_Examples/Pyomo_Example.py`.

## 4.1 Why an LP?

Tutorial 3's optimiser samples and polishes — it is flexible but slow and
approximate. The LP in `opt_con_class.py` optimises *all* capacities and
*every hour's operation* simultaneously, to provable optimality, under a
perfect-foresight assumption. For linear cost structures it is the
reference answer. (`LinearProgramFormulation.pdf` gives the mathematics.)

## 4.2 Set up

Keep the first LP small: one weather year, two generators, two stores.

```python
import numpy as np
import aggregatedEVs as aggEV
from generation import OffshoreWindModel, SolarModel
from storage import (BatteryStorageModel, HydrogenStorageModel,
                     MultipleStorageAssets)
from opt_con_class import System_LinProg_Model
from fns import get_GB_demand

ymin = ymax = 2015

gens = [
    OffshoreWindModel(year_min=ymin, year_max=ymax, sites="all",
                      data_path="data/wind/", limits=[0, 150_000]),
    SolarModel(year_min=ymin, year_max=ymax, sites="all",
               data_path="data/solar/", limits=[0, 100_000]),
]
stores = MultipleStorageAssets([BatteryStorageModel(),
                                HydrogenStorageModel()])
demand = np.asarray(get_GB_demand(ymin, ymax, list(range(1, 13))))
```

Note `limits=[min, max]` (MW) on each generator — these become the LP's
build bounds. Storage bounds come from `storagelimits` /
`chargelimits` / `dischargelimits` on the storage objects.

## 4.3 Formulate and solve

```python
lp = System_LinProg_Model(
    surplus=-demand,          # demand as negative surplus
    fossilLimit=0.05,         # ≤5% of energy from fossil fuel
    Mult_Stor=stores,
    Mult_aggEV=aggEV.MultipleAggregatedEVs([]),   # required, even empty
    gen_list=gens,
    YearRange=[ymin, ymax],
)
lp.Form_Model()               # slow: builds every hourly constraint
lp.Run_Sizing(solver="glpk")  # or solver="highs"
```

Two-phase on purpose: `Form_Model` is the expensive step,
`Run_Sizing` is comparatively quick and can be repeated.

## 4.4 Read the results

```python
print(lp.df_capacity)     # built MW per generator; MWh + charge/discharge MW per store
print(lp.df_costs)        # capital + operational cost breakdown

lp.PlotSurplus(4000, 4500)             # surplus before/after storage action
stores.assets[0].plot_timeseries(4000, 4500)   # battery SOC
stores.assets[1].plot_timeseries(0, -1)        # hydrogen SOC, full year
```

The solve writes the optimised charge/discharge/SOC series back onto the
storage objects and the built capacity back onto each generator, so all
the usual plotting works. Persist what you need, e.g.
`lp.df_capacity.to_csv("log/capacities.csv", index=False)`.

Look at the hydrogen SOC over the full year: the LP, knowing the weather
in advance, fills the cavern ahead of the winter deficit — that is the
perfect-foresight assumption made visible.

## 4.5 Fast sensitivity sweeps

Key inputs are mutable Pyomo `Param`s on the formed model, so sweeps skip
`Form_Model`:

```python
results = {}
for lim in [0.05, 0.02, 0.0]:
    lp.model.foss_lim_param = lim * sum(demand)
    lp.Run_Sizing(solver="glpk")
    results[lim] = lp.df_capacity

# Cap solar (generator index 1) at 25 GW and re-solve:
lp.model.Gen_Limit_Param_Upper[1] = 25_000
lp.Run_Sizing(solver="glpk")
```

`Userguide_Examples/Variable_Parameters.py` times the difference — for a
multi-year model, reforming can take longer than every re-solve combined.

## 4.6 Scaling up

- Add years (`year_min=2013, year_max=2019` and `YearRange=[2013, 2019]`)
  once the one-year model behaves; solve time and memory grow roughly
  linearly with hours.
- `Form_Model(timeresolution=24)` coarsens to daily steps for quick scans.
- Add a `DispatchableGenerator` list (with `dispatchable_energy_limits`)
  to study low-carbon firm power instead of a bare fossil allowance.

!!! warning
    The built-in size-then-operate workflow (`Run_Sizing_Then_Op`) is
    currently broken; to test a sized design on
    unseen weather, fix the capacities and use
    `MultipleStorageAssets.causal_system_operation` — demonstrated next.

**Next:** [Tutorial 5 — Electric vehicle fleets](05-electric-vehicles.md).
