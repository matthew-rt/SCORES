# Electric vehicle fleets

`aggregatedEVs.py` models fleets of electric vehicles as aggregated,
partially-available storage. All vehicles and chargers within one fleet are
homogeneous; heterogeneity is represented by defining several fleets (e.g.
"Domestic", "Work", "Commercial") with different plug-in patterns.

## AggregatedEVModel

```python
import numpy as np
import aggregatedEVs as aggEV

fleet = aggEV.AggregatedEVModel(
    eff_in=95, eff_out=95,
    chargertype=[0.5, 0.5],          # fractions: [V2G, smart unidirectional]
    chargercost=np.array([2000/20, 800/20, 50/20]),  # £/charger/yr [V2G, smart, dumb]
    max_c_rate=10, max_d_rate=10,    # kW per charger, grid-side
    min_SOC=0, max_SOC=36,           # kWh per vehicle
    number=1_000_000,                # number of chargers in the fleet
    initial_number=0.9,              # fraction plugged in at t=0
    Ein=20,                          # kWh in battery when a car plugs in
    Eout=36,                         # kWh required when it unplugs
    Nin=np.array([...]),             # 24 values: plug-in rate per hour (weekday)
    Nout=np.array([...]),            # 24 values: unplug rate per hour (weekday)
    Nin_weekend=np.array([...]),
    Nout_weekend=np.array([...]),
    name="Domestic1",
)
```

Behavioural inputs:

- `Nin` / `Nout` are normalised hourly connection/disconnection profiles
  (e.g. `Nout[7] = 0.2` means 20% of the fleet's chargers see a vehicle
  unplug at 7am on weekdays). The sums of `Nin` and `Nout` must match,
  otherwise the connected population drifts and the constructor raises.
- Vehicles arrive with `Ein` kWh and must leave with `Eout` kWh — the model
  must charge each vehicle by `Eout - Ein` while it is plugged in.
  (`Eout` must equal `max_SOC` for the causal simulation and optimiser.)
- `chargertype` splits the fleet between charger classes:
  index 0 = **V2G** (can discharge to the grid), 1 = **smart
  unidirectional** (timing optimised, no export), 2 = **unmanaged** (the
  remainder; charges immediately on arrival).
- `limits=[minV2G, maxV2G, minUni, maxUni]` bounds the charger numbers when
  the linear programme optimises the mix.

## MultipleAggregatedEVs

Wraps a list of fleets, mirroring `MultipleStorageAssets`:

```python
fleets = aggEV.MultipleAggregatedEVs([dom_fleet, work_fleet])
```

`construct_connectivity_timeseries(start, end)` expands the 24-hour
weekday/weekend profiles into a full simulation-length series with correct
weekday/weekend alignment — this is why methods involving EVs require
`start`/`end` datetimes (usually midnight on 1 January of the first year,
and midnight on 1 January after the last year).

## Where EV fleets plug in

- **Linear programme** — pass as `Mult_aggEV` to `System_LinProg_Model`;
  set `start_EV` and `end_EV` in `Form_Model`. The LP optimises charger
  mix (within `limits`) and all charging/discharging schedules.
- **Causal / non-causal simulation** — pass to
  `MultipleStorageAssets.causal_system_operation` /
  `non_causal_system_operation` to simulate fleets alongside conventional
  storage.
- **ElectricitySystem** — an `aggEV_list` argument exists on the system
  classes; an empty `MultipleAggregatedEVs([])` is the default.

Even when a workflow requires the object, a zero-fleet
`MultipleAggregatedEVs([])` is always acceptable.

## Worked examples in the repository

- `Userguide_Examples/agg_EV_example.py` — sizing with a domestic fleet.
- `Userguide_Examples/simulation_ex.py` — causal vs non-causal operation
  with EVs (see the [tutorial](../tutorials/05-electric-vehicles.md)).
- `Userguide_Examples/charger_type.py` — optimising the V2G/unidirectional
  charger split.
- `Userguide_Examples/fleetcorrelation.py`, `DDManalysis.py` — further
  fleet studies.
