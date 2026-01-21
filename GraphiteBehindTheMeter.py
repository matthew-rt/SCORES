# %%
import numpy as np
import datetime
import matplotlib.pyplot as plt
import pandas as pd
import Loaderfunctions
import generation
import storage
from system import ElectricitySystem
# %%
winddatafolder = 'W:/SCORES-DATA/era5wind/'
solardatafolder = 'W:/SCORES-DATA/adjustedsolar/'
onshorepowercurve=np.loadtxt("W:/SCORES-DATA/genericonshorepowercurve.csv", delimiter=",", skiprows=1)



# %%
yearmin = 2000
yearmax = 2022
nyears = yearmax - yearmin + 1



# %%

solarcaps_MW = [80]

onshore_turbine_size_MW = 4
numberofturbines = [20]

onshorepowercurve[:,1]*=onshore_turbine_size_MW

# %%
solargenerator=generation.SolarModel(
    sites=[165], 
    year_min=yearmin, 
    year_max=yearmax, 
    data_path=solardatafolder,
    plant_capacities=solarcaps_MW,
    force_run=True,
)

print(solargenerator.get_load_factor())
solarpowerout=solargenerator.power_out_array

# print(f"Solar length:{len(solarpowerout)}")
# plt.plot(solarpowerout)
# plt.show()



# %%
onshoregenerator = generation.OnshoreWindModel(
    sites = [155],
    year_min=yearmin,
    year_max=yearmax,
    data_path=winddatafolder,
    n_turbine=numberofturbines,
    force_run=True,
    power_curve=onshorepowercurve,
    turbine_size= onshore_turbine_size_MW
)

print(onshoregenerator.get_load_factor())

# print(f"Wind length:{len(windpowerout)}")
# plt.plot(windpowerout)
#plt.show()


# %%
battery_MWh = 800
battery = storage.BatteryStorageModel(
    capacity=battery_MWh,
    max_d_rate=25,
    max_c_rate=25,
#    initial_charge = 0
    )


# %%
UnabatedGasinstalled_MW = 200
UnabatedGasDispatchable = generation.DispatchableGenerator(
    sites=[1],
    year_min=yearmin,
    year_max=yearmax,
    capacities=[UnabatedGasinstalled_MW],
    gentype="Gas",
)



# %%
GridConnectionFirm_MW = 200
DemandSite_MW =300

DemandBTM_MW = DemandSite_MW - GridConnectionFirm_MW
print(DemandBTM_MW)


# %%
gridconnection = generation.NuclearModel(
    sites=[1],
    year_min=yearmin,
    year_max=yearmax,
    capacities=[GridConnectionFirm_MW],
    loadfactor=1
    )


# %%
# making demand daily profile
baseline = [0.0409, 0.0408, 0.0407, 0.0407, 0.0408, 0.0409,
                                         0.0411, 0.0413, 0.0415, 0.042, 0.0422, 0.0424,
                                         0.0425, 0.0426, 0.0427, 0.0426, 0.0425, 0.0424, 
                                         0.0422, 0.042, 0.0418, 0.0414, 0.0411, 0.0409 ]

alt_lthbu = [0.0393, 0.0392, 0.0392, 0.0392, 0.0395, 0.04,
                                         0.0404, 0.0408, 0.0419, 0.0434, 0.0435, 0.0437,
                                         0.0439, 0.044, 0.044, 0.044, 0.0439, 0.0435, 
                                         0.043, 0.0421, 0.0414, 0.0406, 0.04, 0.0395 ]

alt_lownight = [0.01, 0.01, 0.02, 0.03, 0.04, 0.04, 
                0.06, 0.06, 0.06, 0.06, 0.06, 0.07, 
                0.07, 0.07, 0.07, 0.06, 0.05, 0.04,
                0.03, 0.03, 0.02, 0.02, 0.01, 0.01]

# daily_load_proportion_hourly = alt_lownight
# print(np.sum(daily_load_proportion_hourly))
# plt.plot(daily_load_proportion_hourly)
# %%
# num_days = int(len(solarpowerout)/24)
# print(num_days)

# scale_factor = DemandSite_MW / np.max(daily_load_proportion_hourly)
# demand = np.array(daily_load_proportion_hourly*num_days)*scale_factor
# print(len(demand) == len(solarpowerout))
# plt.plot(demand[0:168])
# plt.ylim(0, 500)
# plt.ylabel("MW")
# print(min(demand), max(demand))

# %%
# making demand flat
demand = [DemandSite_MW]*len(solarpowerout)
# print(len(demand))



# %%
generatorlist = ([onshoregenerator] + 
                 [solargenerator] + 
                 [gridconnection]
                 )
DispatchableAssetList = [UnabatedGasDispatchable]
storagelist = [battery]
# %%
system = ElectricitySystem(
    generatorlist,
    storagelist,
    demand=demand,
    # DispatchableAssetList=DispatchableAssetList,
)

# plt.plot(system.surplus)

system.update_surplus()
reliability = system.get_reliability()
print(reliability)


# %%
batteryprofile = [0]*len(solarpowerout)
battery_discharge = [0]*len(solarpowerout)
# print(battery.SOC)
battery_MW = battery.capacity * battery.max_d_rate/100
print(battery.capacity)
print(battery.max_d_rate)
print(battery_MW)
a = 0
b = len(solarpowerout)
for i in range(a, b): # len(solarpowerout)):
    batt_SOC_change = battery.SOC[i] - battery.SOC[i-1]
    # print(battery.SOC[i], batt_SOC_change)
    batteryprofile[i] = batt_SOC_change *-1# * battery_MW #*battery.eff_in/100*battery.eff_out/100
    battery_discharge[i] = min(0, batt_SOC_change *-1) #* battery_MW) #*battery.eff_in/100*battery.eff_out/100)

batt_MW_used = -min(batteryprofile)
batt_MWh_disch = -np.sum(battery_discharge)
# print(batt_MW_used)
# print(batt_MWh_disch)

# plt.plot(np.array(batteryprofile)[a:b])
# plt.plot(demand[a:b])
# plt.plot(solargenerator.power_out_array[a:b] + onshoregenerator.power_out_array[a:b])
# %%

barlabels = ["Demand", "Grid", "Solar PV", "Onshore Wind", "Gas", "Battery"]
caps_MW = [DemandSite_MW, 
           np.max(gridconnection.power_out),
           np.max(solargenerator.power_out_array), 
           np.max(onshoregenerator.power_out_array),
           np.max(UnabatedGasDispatchable.power_out_array), 
           batt_MW_used]

demand_MWh = np.sum(demand)
gen_TWh = [demand_MWh / 10**6,
           np.sum(gridconnection.power_out) / 10**6,
           np.sum(solargenerator.power_out_array) / 10**6,
           np.sum(onshoregenerator.power_out_array)/ 10**6,
           np.sum(UnabatedGasDispatchable.power_out_array)/ 10**6,
           batt_MWh_disch/ 10**6
           ]


# %%

fig, ax = plt.subplots()
ax.bar(barlabels, caps_MW)
ax.set_ylabel("MW")


# %%
fig, ax = plt.subplots()
ax.bar(barlabels, gen_TWh)
ax.set_ylabel("TWh")

# %%
fig, ax = plt.subplots()
# ax.set_ylim(0,1000)
ax.set_ylabel("MW")
ax.set_xlabel("Time")
ax.plot(onshoregenerator.power_out_array
        + solargenerator.power_out_array
        + np.array(gridconnection.power_out)
        -batteryprofile
        + np.array(UnabatedGasDispatchable.power_out_array)
        , label = "generation")
# ax.plot(system.storage.curtarray, label = "excess")
# ax.plot(np.array(batteryprofile)*-1, label = "battery")
# ax.plot(np.array(battery_discharge)*-1, label = "battery disch")
ax.plot(demand, label = "demand")
ax.plot(gridconnection.power_out, label = "grid")
# ax.plot(system.surplus)
ax.legend()
# ax.set_xlim(0, 300)
# %%
totalgen = (np.sum(gridconnection.power_out)+
           np.sum(solargenerator.power_out_array)+
           np.sum(onshoregenerator.power_out_array)+
           np.sum(UnabatedGasDispatchable.power_out_array)
           -np.sum(system.storage.curtarray)
           )
print("site total: ", totalgen/10**6/nyears)
print("demand annual TWh: ", np.sum(demand)/10**6/nyears)
print("share demand met: ", totalgen/np.sum(demand))
print("curtailed/reduced grid: ", np.sum(system.storage.curtarray)/10**6/nyears)
for i in range(0, len(barlabels)):
    print(barlabels[i], caps_MW[i], "MW ", gen_TWh[i]/nyears, "TWh/year")
print("gas remaining TWh: ", (np.sum(demand) - totalgen)/10**6/nyears)
# print(np.array(caps_MW))
# print(np.array(gen_TWh))
# print(np.array(gen_TWh)/nyears)
# %%
a = 0
b = len(solarpowerout)
export = [0] * len(solarpowerout)
curtailed = [0] * len(solarpowerout)

for i in range(a, b):
    curtailed[i] = max(0, system.storage.curtarray[i]-GridConnectionFirm_MW)
    export[i] = min(system.storage.curtarray[i], GridConnectionFirm_MW)

print("exported TWh: ", np.sum(export)/10**6/nyears)
print("curtailed TWh ", np.sum(curtailed)/10**6/nyears)
# plt.plot(system.storage.curtarray[a:b])
# plt.plot(curtailed[a:b])
# plt.plot(export[a:b])
# plt.plot(demand[a:b])
# plt.plot(np.array(export[a:b]) + np.array(curtailed[a:b]))
# plt.plot(onshoregenerator.power_out_array[a:b])
# %%
# print(np.sum(solargenerator.power_out_array)/np.sum(demand)*100)
# print(np.sum(onshoregenerator.power_out_array)/np.sum(demand)*100)
# print(np.sum(UnabatedGasDispatchable.power_out_array)/np.sum(demand)*100)
# print(np.sum(gridconnection.power_out)/np.sum(demand)*100)
# print(np.sum(system.storage.curtarray)/np.sum(demand)*100)
# %%
