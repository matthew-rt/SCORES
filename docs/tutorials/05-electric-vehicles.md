# Tutorial 5 — Electric vehicle fleets

**Goal:** define an aggregated EV fleet, co-optimise it with storage in
the linear programme, and compare operation with and without foresight.

**You need:** tutorial 4 (working solver).

## 5.1 Describe a fleet

An `AggregatedEVModel` describes many identical vehicles whose grid
connection follows a daily pattern. The behavioural core is four 24-value
arrays: plug-in and unplug rates for weekdays and weekends.

```python
import numpy as np
import aggregatedEVs as aggEV

# A domestic fleet: cars leave 7-9am, return 3-7pm on weekdays.
Nin  = np.zeros(24); Nout = np.zeros(24)
Nout[7:9]  = 0.2            # 40% of chargers see a car leave in the morning
Nin[[9, 15, 16, 17, 18]] = [0.1, 0.1, 0.1, 0.05, 0.05]   # returns
assert abs(Nin.sum() - Nout.sum()) < 1e-9   # must balance

dom = aggEV.AggregatedEVModel(
    eff_in=95, eff_out=95,
    chargertype=[0.5, 0.5],          # 50% V2G, 50% smart unidirectional
    chargercost=np.array([2000/20, 800/20, 50/20]),   # £/charger/yr
    max_c_rate=10, max_d_rate=10,    # kW per charger
    min_SOC=0, max_SOC=36,           # kWh per car
    number=1_000_000,
    initial_number=0.9,
    Ein=20, Eout=36,                 # arrive with 20 kWh, leave full
    Nin=Nin, Nout=Nout,
    Nin_weekend=np.zeros(24), Nout_weekend=np.zeros(24),
    name="Domestic",
)
fleets = aggEV.MultipleAggregatedEVs([dom])
```

The constructor validates the behavioural arrays (plug-in and unplug
totals must match, `Eout` must equal `max_SOC` for the optimiser).

## 5.2 Co-optimise in the LP

EVs need the simulation anchored to real dates (weekday vs weekend), so
`Form_Model` requires `start_EV`/`end_EV` datetimes:

```python
from datetime import datetime
from opt_con_class import System_LinProg_Model

lp = System_LinProg_Model(
    surplus=-demand,                 # from tutorial 4
    fossilLimit=0.05,
    Mult_Stor=stores,
    Mult_aggEV=fleets,
    gen_list=gens,
    YearRange=[2015, 2015],
)
lp.Form_Model(start_EV=datetime(2015, 1, 1, 0),
              end_EV=datetime(2016, 1, 1, 0))
lp.Run_Sizing(solver="glpk")
print(lp.df_capacity)
```

The LP schedules every hour of fleet charging (and V2G discharging) around
the vehicles' availability and energy needs, and — if you leave the
fleet's `limits` open — chooses how many V2G versus unidirectional
chargers to build. `Userguide_Examples/charger_type.py` explores that
trade-off directly.

## 5.3 Foresight versus no foresight

The LP assumes perfect foresight. `MultipleStorageAssets` offers the same
system under two operating regimes so you can measure what foresight is
worth (this is `Userguide_Examples/simulation_ex.py`):

```python
from datetime import datetime
from storage import (BatteryStorageModel, HydrogenStorageModel,
                     MultipleStorageAssets)

stores = MultipleStorageAssets([BatteryStorageModel(capacity=100_000),
                                HydrogenStorageModel(capacity=1_000_000)])
power = np.asarray(wind.power_out)
power = power / max(power) * 150_000        # 150 GW wind profile

# Causal: hour-by-hour rules, no knowledge of the future
res_causal = stores.causal_system_operation(
    demand, power, [2, 3, 0, 1], [0, 1, 3, 2], fleets,
    start=datetime(2015, 1, 1, 0), end=datetime(2016, 1, 1, 0),
    initial_SOC=[0.5, 0.75, 0.6, 1], plot_timeseries=True)

# Non-causal: perfect foresight (solves an operational LP internally)
res_perfect = stores.non_causal_system_operation(
    demand, power, fleets,
    start=datetime(2015, 1, 1, 0), end=datetime(2016, 1, 1, 0),
    InitialSOC=[0.5, 0.75, 0.6, 1], plot_timeseries=True)
```

The charge/discharge order lists (`[2, 3, 0, 1]` etc.) index the stores
*and* each fleet's V2G and unidirectional chargers; SOC lists are ordered
`[store0, store1, ..., fleet0-V2G, fleet0-uni, ...]`. Compare the
reliability and fossil-fuel use in the two result sets — the gap is the
value of foresight (or of very good forecasting).

## 5.4 Things to try

- Set `chargertype=[0.0, 1.0]` (no V2G) and re-solve: how much more
  battery does the LP build?
- Give the weekend arrays a realistic pattern instead of zeros.
- Add a second "Work" fleet with opposite connectivity and watch the LP
  exploit the complementarity.

**Done!** You have covered the full SCORES workflow. For deeper dives,
read the [user guide](../user-guide/architecture.md) and the studies in
`Userguide_Examples/` ([file guide](../reference/file-guide.md)).
