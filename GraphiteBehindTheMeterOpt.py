# %%
import numpy as np
import datetime
import matplotlib.pyplot as plt
import pandas as pd
import Loaderfunctions
import generation
import storage
from system import ElectricitySystem
import aggregatedEVs as aggEV
from opt_con_class import System_LinProg_Model
import cvxopt

# %%
winddatafolder = 'W:/SCORES-DATA/era5wind/'
solardatafolder = 'W:/SCORES-DATA/adjustedsolar/'



# %%
yearmin = 2018
yearmax = 2019

GridConnectionFirm_MW = 240
DemandSite_MW = 420

DemandBTM_MW = DemandSite_MW - GridConnectionFirm_MW
print(DemandBTM_MW)

# %%
# define all limits
solarlimit = 140000
onshorelimit = 42000


onshore_turbine_size_MW = 4

onshorepowercurve=np.loadtxt("W:/SCORES-DATA/genericonshorepowercurve.csv", delimiter=",", skiprows=1)
onshorepowercurve[:,1]*=onshore_turbine_size_MW

# %%
solargenerator=generation.SolarModel(
    sites=[148], 
    year_min=yearmin, 
    year_max=yearmax, 
    data_path=solardatafolder,
    force_run=True,
    limits = [0,solarlimit],
    cost_year=2030
)



# %%
onshoregenerator = generation.OnshoreWindModel(
    sites = [155],
    year_min=yearmin,
    year_max=yearmax,
    data_path=winddatafolder,
    force_run=True,
    power_curve=onshorepowercurve,
    turbine_size= onshore_turbine_size_MW,
    cost_year=2030,
    limits=[0,onshorelimit]
)


# %%
battery = storage.BatteryStorageModel()


# %%
UnabatedGasinstalled_MW = 50
UnabatedGasDispatchable = generation.DispatchableGenerator(
    sites=[1],
    year_min=yearmin,
    year_max=yearmax,
    capacities=[UnabatedGasinstalled_MW],
    gentype="Gas",
    cost_year=2030
)
# %%



# %%
demand = np.array([DemandBTM_MW]*17520)
print(len(demand))

stor_list = [battery]
generators = [solargenerator, onshoregenerator]
dispatchables = [UnabatedGasDispatchable]

# %%
x = System_LinProg_Model(
    surplus=-demand,
    fossilLimit=0.00001,
    Mult_Stor=storage.MultipleStorageAssets(stor_list),
    Mult_aggEV=aggEV.MultipleAggregatedEVs([]),
    gen_list=generators,
    YearRange=[yearmin, yearmax],
    dispatchable_list=dispatchables,
)
# %%
# Form the Linear Program Model
x.Form_Model()
# %%
# print the time sizing started at
print(datetime.datetime.now())
# Solve the Linear Program

# Change this if Gurobi is not installed
solver = "cvxpy"
x.Run_Sizing(solver=solver)

# %%
runname = "graphite1"
# Store Results
x.df_capacity.to_csv(f"log/onerun/{runname}_{solver}_capacities.csv", index=False)
x.df_costs.to_csv(f"log/onerun/{runname}_{solver}_costs.csv", index=False)

