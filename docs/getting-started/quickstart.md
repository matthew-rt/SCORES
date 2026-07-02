# Quickstart

This page shows the minimum code to get results out of SCORES. Each example
assumes you have [installed SCORES](installation.md), obtained the
[weather data](data.md), and are running Python from the repository root
(the modules use relative paths like `data/` and `params/`).

## 1. Simulate a generator

```python
from generation import OffshoreWindModel

# Simulate 10 MW turbines at three weather sites for 2013-2019.
# Site indexes come from data/wind/site_locs.csv.
osw = OffshoreWindModel(
    year_min=2013,
    year_max=2019,
    sites=[119, 174, 178],
    data_path="data/wind/",
    turbine_size=10,
)

print(osw.power_out[:24])            # hourly output in MW, first day
print(f"Load factor: {osw.get_load_factor():.1f}%")
print(f"LCOE: £{osw.calculate_LCOE():.2f}/MWh")
```

The result is cached in `stored_model_runs/`, so constructing the same
model again is nearly instant.

## 2. Size storage for a reliability target

```python
import numpy as np
from storage import BatteryStorageModel
from fns import get_GB_demand

demand = np.array(get_GB_demand(2013, 2019, list(range(1, 13))))

# Scale the wind fleet to 100 GW and compute the hourly surplus
power = osw.scale_output(100_000)     # MW
surplus = power - demand

battery = BatteryStorageModel()
capacity = battery.size_storage(surplus, reliability=99)  # MWh
print(f"Storage needed: {capacity/1e3:.0f} GWh")
```

## 3. Cost a whole system

```python
from generation import OffshoreWindModel, SolarModel
from storage import BatteryStorageModel, HydrogenStorageModel
from system import ElectricitySystemGB

generators = [
    OffshoreWindModel(year_min=2013, year_max=2019, sites="all",
                      data_path="data/wind/"),
    SolarModel(year_min=2013, year_max=2019, sites="all",
               data_path="data/solar/"),
]
storage = [BatteryStorageModel(), HydrogenStorageModel()]

es = ElectricitySystemGB(generators, storage,
                         year_min=2013, year_max=2019, reliability=99)

# x = [gen capacities in GW ...] + [storage fractions for all but the last]
x = [80, 60, 0.1]   # 80 GW wind, 60 GW solar, 10% battery / 90% hydrogen
print(es.cost(x))   # £/MWh of demand served
es.analyse(x)       # writes a breakdown to log/system_analysis.txt
```

## 4. Optimise capacities with the linear programme

```python
import numpy as np
import aggregatedEVs as aggEV
from opt_con_class import System_LinProg_Model
from storage import BatteryStorageModel, HydrogenStorageModel, MultipleStorageAssets
from fns import get_GB_demand

demand = np.asarray(get_GB_demand(2015, 2015, list(range(1, 13))))

model = System_LinProg_Model(
    surplus=-demand,                 # demand enters as negative surplus
    fossilLimit=0.05,                # ≤5% of energy from fossil fuels
    Mult_Stor=MultipleStorageAssets([BatteryStorageModel(),
                                     HydrogenStorageModel()]),
    Mult_aggEV=aggEV.MultipleAggregatedEVs([]),
    gen_list=generators,             # from step 3
    YearRange=[2015, 2015],
)
model.Form_Model()
model.Run_Sizing()                   # needs GLPK (or solver="highs")

print(model.df_capacity)             # optimal built capacities
print(model.df_costs)                # cost breakdown
```

## Where next?

- The [tutorials](../tutorials/index.md) walk through these workflows in
  detail, explaining every argument.
- The [user guide](../user-guide/architecture.md) documents each module.
