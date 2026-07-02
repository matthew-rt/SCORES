# Tutorial 3 — A whole-system study

**Goal:** combine several generators, several stores and GB demand into an
`ElectricitySystem`; cost a design; and let the heuristic optimiser search
for a cheaper one.

**You need:** tutorials 1–2, plus solar data in `data/solar/`.

## 3.1 Build the system

```python
from generation import OffshoreWindModel, OnshoreWindModel, SolarModel
from storage import BatteryStorageModel, HydrogenStorageModel
from system import ElectricitySystemGB

ymin, ymax = 2013, 2019

generators = [
    OffshoreWindModel(year_min=ymin, year_max=ymax, sites="all",
                      data_path="data/wind/"),
    OnshoreWindModel(year_min=ymin, year_max=ymax, sites="all",
                     data_path="data/wind/"),
    SolarModel(year_min=ymin, year_max=ymax, sites="all",
               data_path="data/solar/"),
]
storage = [BatteryStorageModel(), HydrogenStorageModel()]

es = ElectricitySystemGB(generators, storage,
                         year_min=ymin, year_max=ymax,
                         reliability=99)
```

`ElectricitySystemGB` loads GB demand for the same years and checks every
generator's time series is the same length as demand — if you see
`supply and demand have different lengths`, your year ranges disagree.

## 3.2 Cost a design

Designs are described by a vector `x`:

```python
#    [offshore GW, onshore GW, solar GW, battery share]
x = [70, 30, 60, 0.05]
cost = es.cost(x)
print(f"System cost: £{cost:.2f}/MWh")
```

Reading `x`: the first three entries are generator capacities **in GW**
(same order as `generators`); the remaining entries are the fraction of
total storage capacity in each store *except the last* — here 5% battery,
95% hydrogen. Given those shares, `cost()` sizes the total storage
capacity by bisection until the system hits the 99% reliability target,
then returns total annualised cost per MWh of demand.

## 3.3 Analyse it

```python
es.analyse(x)     # writes log/system_analysis.txt
```

The analysis file records the sized capacities, cost breakdown per
technology, curtailed energy, and storage utilisation — worth reading
before trusting any optimisation result. `es.get_diurnal_profile(...)` and
`es.plot_timeseries(...)` visualise how the design operates.

## 3.4 Optimise

```python
es.optimise(
    min_gen_cap=[20, 0, 0],       # GW lower bounds per generator
    max_gen_cap=[120, 40, 90],    # GW upper bounds
    tic0=150,                     # initial guess at total installed GW
    stor_cap=[0.05],              # initial storage-share guess
)
```

Under the hood: Latin-hypercube sampling over generation mixes
(`lhs_generation`), storage sized for each sample, then
`scipy.optimize.minimize` refinement of the best candidates. Expect this
to take a while — every cost evaluation is a multi-year hourly simulation
plus a bisection sizing. Results land in `log/`.

!!! tip
    The heuristic optimiser is a local search around sampled points: run
    it more than once (or tighten bounds around a region of interest) to
    gain confidence, and cross-check promising designs with the
    [linear programme](04-linear-programming.md).

## 3.5 Things to try

- Fix the generation mix and sweep only the battery share from 0 to 0.3 —
  batteries reduce cycling losses but hydrogen keeps capex down; where is
  the minimum?
- Add `reliability=99.9` and watch the cost climb.
- Use `es.sensitivity_analysis(...)` to sweep a cost assumption.

**Next:** [Tutorial 4 — Sizing with the linear
programme](04-linear-programming.md), the exact-optimisation alternative.
