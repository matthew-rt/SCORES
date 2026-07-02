# Tutorials

These tutorials build up from a single wind farm to a co-optimised system
with electric-vehicle fleets. They are designed to be followed in order —
each one assumes the concepts (and sometimes the cached model runs) of the
previous.

| Tutorial | You will learn | Needs |
| --- | --- | --- |
| [1. Your first generation model](01-first-generation-model.md) | Build a wind model, understand sites/years/caching, read load factors and LCOE. | Wind weather data |
| [2. Adding storage](02-adding-storage.md) | Simulate a battery against a surplus, size storage for a reliability target, combine stores. | Tutorial 1 |
| [3. A whole-system study](03-whole-system.md) | Combine generators, storage and GB demand; cost and analyse a design; run the heuristic optimiser. | Tutorials 1–2, solar data |
| [4. Sizing with the linear programme](04-linear-programming.md) | Formulate and solve the Pyomo LP; read the results; run fast sensitivity sweeps. | GLPK or HiGHS solver |
| [5. Electric vehicle fleets](05-electric-vehicles.md) | Define an EV fleet, include it in the LP, compare causal vs non-causal operation. | Tutorial 4 |

## Before you start

1. Work through [Installation](../getting-started/installation.md) and
   [Getting the data](../getting-started/data.md). You need at least the
   wind dataset (`data/wind/` with per-site CSVs) for tutorial 1, and solar
   for tutorial 3 onwards.
2. Run everything from the **repository root** — the code uses relative
   paths (`data/`, `params/`, `log/`, `stored_model_runs/`).
3. Expect the *first* run of any model to take a while (it is crunching
   seven years of hourly weather data); repeats are fast thanks to the
   cache in `stored_model_runs/`.

!!! tip "Interactive use"
    The tutorials work well typed into an IPython session or a Jupyter
    notebook, so you can inspect intermediate objects. Plain scripts are
    fine too — each tutorial's final listing is a complete runnable script.

## Further worked examples

The `Userguide_Examples/` folder contains the original worked examples
that accompany `SCORES_User_Guide.pdf`, covering variations of these
workflows (multiple locations, variable parameters, hydrogen-vs-gas
studies, charger-type optimisation). The
[repository file guide](../reference/file-guide.md) describes each one.
Note that some predate recent API changes — the
[troubleshooting page](../reference/troubleshooting.md) lists known
mismatches.
