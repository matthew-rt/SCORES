# Electricity systems

`system.py` combines generators, storage and demand into a whole
electricity system that can be simulated and optimised heuristically.

## ElectricitySystem

```python
ElectricitySystem(gen_list, stor_list, demand,
                  t_res=1, reliability=99, start_up_time=0,
                  strategy="ordered",
                  aggEV_list=aggEV.MultipleAggregatedEVs([]),
                  DispatchableAssetList=None, Interconnector=None)
```

- `gen_list` — list of `GenerationModel`s. Every generator's `power_out`
  must be the same length as `demand`.
- `stor_list` — list of `StorageModel`s (wrapped internally in a
  `MultipleStorageAssets`).
- `demand` — hourly demand in MW (positive).
- `reliability` — target % of demand energy to be met when sizing storage.
- `start_up_time` — number of initial hours excluded from reliability
  accounting, so results are not distorted by the initial state of charge
  (GB default: 90 days).
- `strategy` — `"ordered"` charges/discharges stores in priority order.

### The decision vector `x`

Most methods take a vector `x` describing the system:

```text
x = [gen_1 ... gen_n,  frac_1 ... frac_(m-1)]
     capacities in GW   storage-share fractions (0-1)
```

The first `n` entries are the installed capacities of each generator **in
GW**. The remaining `m-1` entries give the fraction of total storage
capacity held by each store except the last (which takes the remainder).
Total storage capacity itself is *sized* to hit the reliability target.

### Key methods

| Method | What it does |
| --- | --- |
| `cost(x)` | Scales generation to `x`, sizes storage for the reliability target, and returns total system cost in **£/MWh of demand**. |
| `analyse(x, filename="log/system_analysis.txt")` | Full simulation at `x`; writes capacities, costs, curtailment and storage usage to file. |
| `get_reliability(...)` | Reliability of the current configuration. |
| `optimise(...)` | Full heuristic optimisation: Latin-hypercube search over generation ratios (`lhs_generation`) then refinement (`optimise_fixed_gen_ratio`, storage-ratio search). Accepts bounds like `min_gen_cap`, `max_gen_cap`, `tic0` (initial total installed capacity), `stor_cap` (initial storage split). |
| `sensitivity_analysis(var, values, ...)` | Re-optimises while sweeping a parameter; results plotted with `plot_sensitivity_results`. |
| `get_diurnal_profile(gen_cap, stor_cap)` | Average daily generation/storage behaviour at a given design. |
| `plot_timeseries(start, end)` | Time-series plot of the last simulation. |

## ElectricitySystemGB

Convenience subclass for Great Britain: loads hourly GB demand from
`data/demand.csv` via `fns.get_GB_demand` (shipped data covers
**2013–2019**), and sets `start_up_time` to 90 days.

```python
es = ElectricitySystemGB(generators, storage,
                         year_min=2013, year_max=2019,
                         reliability=99,
                         scaler=1)     # optional demand multiplier
```

!!! warning
    `ElectricitySystemGB` accepts `heat_demand=` and `ev_demand=` arguments
    but currently ignores them (hard-coded zeros are passed through to
    `get_GB_demand`). To include electrified heat or EV demand, call
    `fns.get_GB_demand(...)` yourself with the values you want and pass
    the result via `demand=`.

## Other subclasses

- **`DispatchableOutput`** — one generator plus storage operated to deliver
  a flat, dispatchable output. Provides reliability-vs-capacity and
  reliability-vs-cost curves for a target load factor.
- **`CostOptimisation`** — variant of `ElectricitySystem` with additional
  optimisation strategies over generation and storage ratios (used by some
  historical studies; the linear programme in
  [`opt_con_class.py`](optimisation.md) is generally the better tool now).

## Heuristic vs linear-programme optimisation

`ElectricitySystem.optimise` treats the simulator as a black box: it
samples candidate designs, sizes storage by bisection for each, and
polishes with scipy. It handles non-linear operational rules (ordered
dispatch, causal operation) but is slow and only locally optimal.

`System_LinProg_Model` solves sizing and operation *jointly and exactly*,
but requires the (linear) perfect-foresight formulation. Common practice in
this repository's studies: use the LP for sizing, then check the design
under causal operation with `MultipleStorageAssets.causal_system_operation`.

## Example

```python
from generation import OffshoreWindModel, SolarModel
from storage import BatteryStorageModel, HydrogenStorageModel
from system import ElectricitySystemGB

gens = [OffshoreWindModel(year_min=2013, year_max=2019, sites="all",
                          data_path="data/wind/"),
        SolarModel(year_min=2013, year_max=2019, sites="all",
                   data_path="data/solar/")]
stor = [BatteryStorageModel(), HydrogenStorageModel()]

es = ElectricitySystemGB(gens, stor, year_min=2013, year_max=2019,
                         reliability=99)

x = [80, 60, 0.1]           # 80 GW wind, 60 GW solar, 10% battery share
print(es.cost(x))           # £/MWh
es.analyse(x)               # -> log/system_analysis.txt

es.optimise(min_gen_cap=[20, 0], max_gen_cap=[120, 90],
            tic0=140, stor_cap=[0.1])
```
