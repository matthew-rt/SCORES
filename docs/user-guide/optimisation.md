# Linear-programme optimisation

`opt_con_class.py` formulates system sizing and operation as a linear
programme (LP) in [Pyomo](https://www.pyomo.org/) and solves it with an
external solver (GLPK by default, HiGHS via `highspy`). The mathematical
formulation is documented in `LinearProgramFormulation.pdf` at the
repository root.

The LP co-optimises, with perfect foresight over the weather years:

- installed capacity of each candidate renewable generator (within its
  `limits`);
- energy capacity of each store, plus independent charge and discharge
  power capacities (within `storagelimits` / `chargelimits` /
  `dischargelimits`);
- the charger mix (V2G vs unidirectional) of each EV fleet;
- capacity and dispatch of dispatchable generators (optionally
  energy-limited);
- hourly operation of everything, subject to a limit on fossil-fuel energy.

## Building the model

```python
from opt_con_class import System_LinProg_Model
from storage import MultipleStorageAssets
import aggregatedEVs as aggEV
import numpy as np

model = System_LinProg_Model(
    surplus=-demand,             # np.array, MW; demand alone = negative surplus
    fossilLimit=0.05,            # fraction of demand that may come from fossil
    Mult_Stor=MultipleStorageAssets([...]),   # required, even if empty
    Mult_aggEV=aggEV.MultipleAggregatedEVs([]),  # required, even if empty
    gen_list=[...],              # candidate GenerationModels
    YearRange=[2013, 2019],
    dispatchable_list=[],        # optional DispatchableGenerators
    dispatchable_energy_limits=False,  # or per-generator fractions of demand
)
```

`surplus` can be *demand only* (as a negative array) — in which case the LP
decides how much of each candidate generator to build — or *pre-committed
generation minus demand*, with `gen_list` supplying additional candidates.

## Form, then solve

```python
model.Form_Model(
    SizingThenOperation=False,   # True for the size-then-operate workflow
    includeleapdays=True,
    fossilfuelpenalty=1.0,       # £/MWh on fossil generation (0 gives odd results)
    StartSOCEqualsEndSOC=True,
    InitialSOC=[-1],             # or per-store values in 0-1
    timeresolution=1,            # hours per timestep
    start_EV=-1, end_EV=-1,      # datetimes; required only when EVs present
)
model.Run_Sizing(solver="glpk")  # or "highs"
```

Forming the model is slow (it builds every constraint); solving is
comparatively fast. The point of the split is that a formed model can be
**re-solved repeatedly with changed parameters** — see
[Sensitivity analysis](#sensitivity-analysis-without-reforming).

### Results

After `Run_Sizing()`:

| Attribute | Contents |
| --- | --- |
| `model.df_capacity` | DataFrame of optimal built capacities: MW per generator, MWh + charge/discharge MW per store, chargers per EV fleet, fossil-fuel energy used. |
| `model.df_costs` | DataFrame of capital and operational costs per asset. |
| `model.PlotSurplus(start, end)` | Plots the surplus before/after storage and EV actions. |
| Each store's `charge`, `discharge`, `SOC` arrays and each generator's optimised capacity | Written back onto the input objects (via `store_optimisation_results`), so `B.plot_timeseries(...)` works after a solve. |

### Run_Sizing_Then_Op

`Run_Sizing_Then_Op(...)` sizes the system on all-but-one weather year and
then simulates operation on the held-out year, testing how a design sized
with foresight performs on unseen weather.

!!! danger "Currently broken"
    In the current version `Run_Sizing_Then_Op` raises exceptions with the
    pinned package versions. The equivalent workflow can be scripted
    manually: `Run_Sizing()` on the sizing years, then
    `MultipleStorageAssets.causal_system_operation` /
    `non_causal_system_operation` on the test year with capacities fixed.

## Sensitivity analysis without reforming

Selected inputs are Pyomo `Param`s (declared mutable), so they can be
changed on the formed model and re-solved in a loop, avoiding the expensive
`Form_Model` step:

```python
for lim in [0.04, 0.02, 0.0]:
    model.model.foss_lim_param = lim * sum(demand)
    model.Run_Sizing()
    print(lim, model.df_capacity)

# Upper bound on generator 0's capacity:
model.model.Gen_Limit_Param_Upper[0] = 25_000   # MW
model.Run_Sizing()
```

`Userguide_Examples/Variable_Parameters.py` demonstrates timing the
difference.

## Practical notes

- **Memory/time scale with `timehorizon × assets`.** Seven weather years at
  hourly resolution is a large LP; start with one year while developing.
  `timeresolution` can coarsen timesteps.
- The fossil limit is expressed in *energy*: `fossilLimit * total demand`.
- `fossilfuelpenalty` defaults to £1/MWh, not zero — a zero cost lets the
  solver use fossil energy in arbitrary hours within the cap, producing
  unnatural-looking dispatch.
- Storage / generator `limits` come from the objects passed in, so set
  `limits=[min, max]` (MW) on generators and `storagelimits` etc. (MWh/MW)
  on stores to constrain the build.
