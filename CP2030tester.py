# %%
import numpy as np
import datetime
import matplotlib.pyplot as plt
import pandas as pd
import Loaderfunctions
import pyproj as proj
import generation
import storage

from system import ElectricitySystem
import seaborn as sns

sns.set_theme()
basedemand = np.loadtxt("w:/SCORES-DATA/demand.csv", usecols=2, delimiter=",", skiprows=1)


totaldemand = 352

powercurvechoice = "Net"

demandstarttime = datetime.datetime(2009, 1, 1)
yearmin = 2009
yearmax = 2019


varcapacitylists = [[19 + 2 * i, 19 + 4 * i] for i in range(15)]

curtailplotlist = []
gaspoweroutplotlist = []


starttime = datetime.datetime(yearmin, 1, 1)
endtime = datetime.datetime(yearmax + 1, 1, 1)

startindex = int((starttime - demandstarttime).total_seconds() / 3600)
endindex = int((endtime - demandstarttime).total_seconds() / 3600)

numberofpoints = int((endtime - starttime).total_seconds() / 3600)
basedemand = basedemand[startindex:endindex]
numberofyears = yearmax - yearmin + 1
# scale demand so the total demand per year is 570TWh. Demand is currently in MWh

yearlydemand = totaldemand

# each year needs to be scaled seperately
currentyear = yearmin
for year in range(numberofyears):
    endofyear = datetime.datetime(yearmin + year + 1, 1, 1) - datetime.timedelta(
        hours=1
    )
    startindex = int(
        (datetime.datetime(currentyear, 1, 1) - starttime).total_seconds() / 3600
    )
    endindex = int((endofyear - starttime).total_seconds() / 3600)
    yearlysum = np.sum(basedemand[startindex:endindex])
    scalingfactor = yearlydemand * 10**6 / yearlysum
    basedemand[startindex:endindex] *= scalingfactor
    currentyear += 1


#assuming 8000MW of data centre demand 
demand=basedemand+8000

existingdata = pd.read_excel("w:/SCORES-DATA/repd-q3-oct-2024-trimmed.xlsx")
existingonshore = existingdata[existingdata["Technology Type"] == "Wind Onshore"].copy()
existingonshore = existingonshore[
    existingonshore["Development Status (short)"] == "Operational"
]
transformer = proj.Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)

existingonshore["Longitude"], existingonshore["Latitude"] = transformer.transform(
    existingonshore["X-coordinate"].values, existingonshore["Y-coordinate"].values
)
offshoredata = pd.read_excel("w:/SCORES-DATA/offshorewindpipeline.xlsx")

offshoredata["Longitude"], offshoredata["Latitude"] = transformer.transform(
    offshoredata["X-coordinate"].values, offshoredata["Y-coordinate"].values
)

winddatafolder = "w:/SCORES-DATA/era5wind/"
windsitelocs = np.loadtxt(winddatafolder + "site_locs.csv", skiprows=1, delimiter=",")

(
    existingonshore["site"],
    existingonshore["Within 100Km"],
) = Loaderfunctions.latlongtosite(
    existingonshore["Latitude"],
    existingonshore["Longitude"],
    windsitelocs,
)

existingonshore["site"] = existingonshore["site"].astype(int)

(
    offshoredata["site"],
    offshoredata["Within 100Km"],
) = Loaderfunctions.latlongtosite(
    offshoredata["Latitude"],
    offshoredata["Longitude"],
    windsitelocs,
)

# round the turbine size of offshore to the nearest 1MW
offshoredata["Comb turbine size"] = np.round(offshoredata["Comb turbine size"])

existingoffshore = offshoredata[
    offshoredata["Estimated operational year"] == "Operational"
].copy()

existingonshoresites = existingonshore["site"].unique().tolist()
onshoresitecapacities = np.zeros(len(existingonshoresites))
for i, site in enumerate(existingonshoresites):
    onshoresitecapacities[i] = np.sum(
        existingonshore[existingonshore["site"] == site]["Installed Capacity (MWelec)"]
    )
existingonshorenumberofturbines = onshoresitecapacities / 4
existingonshorenumberofturbines = [int(i) for i in existingonshorenumberofturbines]

powercurvelocation = "w:/SCORES-DATA/DNV power curves/CSV/"
if powercurvechoice == "Gross":
    existingonshorepowercurve = np.loadtxt(
        powercurvelocation + "4_MW.csv", delimiter=",", skiprows=1
    )
else:
    existingonshorepowercurve = 4 * np.loadtxt(
        "w:/SCORES-DATA/genericonshorepowercurve.csv",
        delimiter=",",
        skiprows=1,
    )


gaspercent = []
additionaldemandlist = []
offshorewindreduction = []

totalinstalledcapacity = np.sum(onshoresitecapacities)
existingonshoregenerator = generation.OnshoreWindModel(
    sites=existingonshoresites,
    turbine_size=4,
    year_min=yearmin,
    year_max=yearmax,
    data_path=winddatafolder,
    n_turbine=existingonshorenumberofturbines,
    force_run=True,
    power_curve=existingonshorepowercurve,
)
onshorecapacity = 30
futureonshoreinstall = onshorecapacity * 10**3 - totalinstalledcapacity

scalesize = futureonshoreinstall / totalinstalledcapacity
scaledcapacities = onshoresitecapacities * scalesize
scalednumberofturbines = scaledcapacities / 7
scalednumberofturbines = [int(i) for i in scalednumberofturbines]

if powercurvechoice == "Gross":
    futureonshorepowercurve = np.loadtxt(
        powercurvelocation + "7_MW.csv", delimiter=",", skiprows=1
    )
else:
    futureonshorepowercurve = 7 * np.loadtxt(
        "w:/SCORES-DATA/genericonshorepowercurve.csv",
        delimiter=",",
        skiprows=1,
    )

futureonshoregenerator = generation.OnshoreWindModel(
    turbine_size=7,
    sites=existingonshoresites,
    year_min=yearmin,
    year_max=yearmax,
    data_path=winddatafolder,
    n_turbine=scalednumberofturbines,
    force_run=True,
    power_curve=futureonshorepowercurve,
    v_cut_out=25,
)

existingoffshoresizes = existingoffshore["Comb turbine size"].unique().tolist()
existingoffshoregenerators = []
for turbsize in existingoffshoresizes:
    thisturbinsizedata = existingoffshore[
        existingoffshore["Comb turbine size"] == turbsize
    ]
    sites = thisturbinsizedata["site"].unique().tolist()
    sites = [int(i) for i in sites]
    capacities = np.zeros(len(sites))
    for i, site in enumerate(sites):
        capacities[i] = np.sum(
            thisturbinsizedata[thisturbinsizedata["site"] == site][
                "Installed Capacity (MWelec)"
            ]
        )
    numberofturbines = capacities / turbsize
    numberofturbines = [int(i) for i in numberofturbines]

    if powercurvechoice == "Gross":
        powercurve = np.loadtxt(
            powercurvelocation + f"{int(turbsize)}_MW.csv",
            delimiter=",",
            skiprows=1,
        )
    elif powercurvechoice == "Net":
        powercurve = np.loadtxt(
            "w:/SCORES-DATA/genericoffshorepowercurve.csv",
            delimiter=",",
            skiprows=1,)
        powercurve[:, 1] *= turbsize

    thissizegenerator = generation.OffshoreWindModel(
        turbine_size=turbsize,
        sites=sites,
        year_min=yearmin,
        year_max=yearmax,
        data_path=winddatafolder,
        n_turbine=numberofturbines,
        force_run=True,
        power_curve=powercurve,
    )
    existingoffshoregenerators.append(thissizegenerator)

futureoffshore = offshoredata[
    offshoredata["Estimated operational year"] != "Operational"
].copy()

existingoffshorecapacity = np.sum(
    [i.total_installed_capacity for i in existingoffshoregenerators]
)

futurecapacity = np.sum(futureoffshore["Installed Capacity (MWelec)"])
offshorecapacity = 50
requiredfuturecapacity = offshorecapacity * 10**3 - existingoffshorecapacity
scalesize = requiredfuturecapacity / futurecapacity

futureoffshoresizes = futureoffshore["Comb turbine size"].unique().tolist()
futureoffshoregenerators = []

for turbsize in futureoffshoresizes:
    thisturbinsizedata = futureoffshore[
        futureoffshore["Comb turbine size"] == turbsize
    ]
    sites = thisturbinsizedata["site"].unique().tolist()
    sites = [int(i) for i in sites]

    capacities = np.zeros(len(sites))
    for i, site in enumerate(sites):
        capacities[i] = np.sum(
            thisturbinsizedata[thisturbinsizedata["site"] == site][
                "Installed Capacity (MWelec)"
            ]
        )
    capacities *= scalesize
    numberofturbines = capacities / turbsize
    numberofturbines = [int(i) for i in numberofturbines]

    if powercurvechoice == "Gross":
        powercurve = np.loadtxt(
            powercurvelocation + f"{int(turbsize)}_MW.csv",
            delimiter=",",
            skiprows=1,
        )
    elif powercurvechoice == "Net":
        powercurve =np.loadtxt(
            "w:/SCORES-DATA/genericoffshorepowercurve.csv",
            delimiter=",",
            skiprows=1,
        )
        powercurve[:, 1] *= turbsize

    thissizegenerator = generation.OffshoreWindModel(
        turbine_size=turbsize,
        sites=sites,
        year_min=yearmin,
        year_max=yearmax,
        data_path=winddatafolder,
        n_turbine=numberofturbines,
        force_run=True,
        power_curve=powercurve,
    )
    futureoffshoregenerators.append(thissizegenerator)

solardatapath = "w:/SCORES-DATA/adjustedsolar/"

solardata = pd.read_excel(
    "w:/SCORES-DATA//top10solar_modified.xlsx"
)

solardata["site"], solardata["Within 100Km"] = Loaderfunctions.latlongtosite(
    solardata["Latitude"],
    solardata["Longitude"],
    np.loadtxt(f"{solardatapath}site_locs.csv", skiprows=1, delimiter=","),
)

solarcapacity = 47
solardata["site"] = solardata["site"].astype(int)
solarsites = solardata["site"].unique()

solarcaps = [solarcapacity * 10**3 / len(solarsites)] * len(solarsites)

solargenerator = generation.SolarModel(
    sites=solarsites,
    year_min=yearmin,
    year_max=yearmax,
    data_path=solardatapath,
    plant_capacities=solarcaps,
    force_run=True,
)




nuclearinstalled = 3
GasCCUSinstalled = 2
H2Pinstalled = 0.1
UnabatedGasinstalled = 32
Biomass = 2.5
BECCS = 0.5
Interconnectors = 12

nucleargenerator = generation.NuclearModel(
    sites=[1],
    year_min=yearmin,
    year_max=yearmax,
    capacities=[nuclearinstalled * 10**3],
    loadfactor=0.83,
)
print(nucleargenerator.power_out[0:100])
generatorlist = (
    [existingonshoregenerator, futureonshoregenerator]
    + existingoffshoregenerators
    + futureoffshoregenerators
    + [solargenerator]
    + [nucleargenerator]
)
longdurationstorage = storage.StorageModel(
    cost_params_file=None,
    storage_param_entry=None,
    technical_params_file=None,
    capacity=40 * 10**3,
    max_c_rate=10,
    max_d_rate=10,
    self_dis=0,
    eff_in=0.84,
    eff_out=0.84,
    storageCapex=1,
    storageFixedOpex=1,
    storagelifetime=1,
    storageVarOpex=1,
    chargeCapex=1,
    chargeFixedOpex=1,
    chargeVarOpex=1,
    chargeLifetime=1,
    dischargeCapex=1,
    dischargeFixedOpex=1,
    dischargeVarOpex=1,
    dischargeLifetime=1,
    hurdleRate=1,
)
lithiumstorage = storage.BatteryStorageModel(capacity=120 * 10**3)

CCSDispatchable = generation.DispatchableGenerator(
    sites=[1],
    year_min=yearmin,
    year_max=yearmax,
    capacities=[GasCCUSinstalled * 10**3],
    gentype="GasCCS",
)
H2PDispatchable = generation.DispatchableGenerator(
    sites=[1],
    year_min=yearmin,
    year_max=yearmax,
    capacities=[H2Pinstalled * 10**3],
    gentype="H2P",
)
UnabatedGasDispatchable = generation.DispatchableGenerator(
    sites=[1],
    year_min=yearmin,
    year_max=yearmax,
    capacities=[UnabatedGasinstalled * 10**3],
    gentype="Gas",
)
BiomassDispatchable = generation.DispatchableGenerator(
    sites=[1],
    year_min=yearmin,
    year_max=yearmax,
    capacities=[Biomass * 10**3],
    gentype="Biomass",
)
BECCSDispatchable = generation.DispatchableGenerator(
    sites=[1],
    year_min=yearmin,
    year_max=yearmax,
    capacities=[BECCS * 10**3],
    gentype="BECCS",
)
InterconnectorDispatchable = generation.Interconnector(
    sites=[1],
    year_min=yearmin,
    year_max=yearmax,
    capacities=[Interconnectors * 10**3],
    gentype="Interconnector",
)

DispatchableAssetList = [
    BECCSDispatchable,
    BiomassDispatchable,
    H2PDispatchable,
    CCSDispatchable,
    InterconnectorDispatchable,
    UnabatedGasDispatchable,
]

for i in range(len(futureoffshoregenerators)):
    print(
        f"Gensize:{futureoffshoregenerators[i].turbine_size}\tLoadFactor:{futureoffshoregenerators[i].get_load_factor()}"
    )
nuclearloadfactor = 0.83
# demand = basedemand + (additionaldemand / 4) * 1000
system = ElectricitySystem(
    generatorlist,
    [lithiumstorage, longdurationstorage],
    demand,
    DispatchableAssetList=DispatchableAssetList,
    Interconnector=InterconnectorDispatchable,
)
system.update_surplus()
reliability = system.get_reliability()
nyears = yearmax - yearmin + 1
unabatedgaspercent = (
    100 * np.sum(UnabatedGasDispatchable.power_out_array) / np.sum(demand)
)
gaspercent.append(unabatedgaspercent)
print(
    f"Unabated gas %: {round(unabatedgaspercent, 2)}\tUnabated gas power out: {unabatedgaspercent*352/100} TWh"
)
print(
    f"Reliability:{round(reliability, 4)}\tLoss of load hours: {365.25*24*(100-reliability)/100}"
)
yearlycurtailement = system.storage.analyse_usage()[2] / (nyears * 10**6)
print(f"Yearly curtailment: {yearlycurtailement} TWh")
Interconnectorexport = InterconnectorDispatchable.total_exported / (nyears * 10**6)
Interconnectorimport = InterconnectorDispatchable.total_imported / (nyears * 10**6)
print(f"Interconnector export: {Interconnectorexport} TWh")
print(f"Interconnector import: {Interconnectorimport} TWh")

existingonshoreloadfactor = existingonshoregenerator.get_load_factor()
futureonshoreloadfactor = futureonshoregenerator.get_load_factor()
existingonshorecapacity = np.sum(existingonshoregenerator.total_installed_capacity)
futureonshorecapacity = np.sum(futureonshoregenerator.total_installed_capacity)
meanonshoreloadfactor = np.average(
    [existingonshoreloadfactor, futureonshoreloadfactor],
    weights=[existingonshorecapacity, futureonshorecapacity],
)

totalonshorepowerout = np.sum(existingonshoregenerator.power_out_array) + np.sum(
    futureonshoregenerator.power_out_array
)
yearlyonshorepowerout = totalonshorepowerout / (nyears * 10**6)

existingoffshoreloadfactors = [
    i.get_load_factor() for i in existingoffshoregenerators
]
existingoffshorecapacities = [
    i.total_installed_capacity for i in existingoffshoregenerators
]
futureoffshoreloadfactors = [i.get_load_factor() for i in futureoffshoregenerators]
futureoffshorecapacities = [
    i.total_installed_capacity for i in futureoffshoregenerators
]
meanoffshoreloadfactor = np.average(
    existingoffshoreloadfactors + futureoffshoreloadfactors,
    weights=existingoffshorecapacities + futureoffshorecapacities,
)

totaloffshorepowerout = np.sum(
    [np.sum(i.power_out_array) for i in existingoffshoregenerators]
) + np.sum([np.sum(i.power_out_array) for i in futureoffshoregenerators])
yearlyoffshorepowerout = totaloffshorepowerout / (nyears * 10**6)

summedoffshorepoweroutarray = np.sum(
    np.vstack([i.power_out_array for i in existingoffshoregenerators]), axis=0
) + np.sum(np.vstack([i.power_out_array for i in futureoffshoregenerators]), axis=0)
totaloffshorecapapcity = np.sum(existingoffshorecapacities) + np.sum(
    futureoffshorecapacities
)

summedonshorepoweroutarray = (
    existingonshoregenerator.power_out_array
    + futureonshoregenerator.power_out_array
)

totalonshorecapacity = existingonshorecapacity + futureonshorecapacity
curtailedarray = system.storage.curtarray
gaspowerout = UnabatedGasDispatchable.power_out_array
interconnectoroutputarray = InterconnectorDispatchable.power_out_array

yearlysolarpowerout = np.sum(solargenerator.power_out_array) / (nyears * 10**6)
nuclearpowerout = np.sum(nucleargenerator.power_out_array) / (nyears * 10**6)
biomasspowerout = np.sum(BiomassDispatchable.power_out_array) / (nyears * 10**6)
beccspowerout = np.sum(BECCSDispatchable.power_out_array) / (nyears * 10**6)
cleanpowersum = (
    yearlyonshorepowerout
    + yearlyoffshorepowerout
    + yearlysolarpowerout
    + nuclearpowerout
    + biomasspowerout
    + beccspowerout
)
print(f"Yearly onshore power out: {yearlyonshorepowerout} TWh")
print(f"Yearly offshore power out: {yearlyoffshorepowerout} TWh")
print(f"Yearly solar power out: {yearlysolarpowerout} TWh")
print(f"Yearly clean power out: {cleanpowersum} TWh")
print(f"Yearly biomass power out: {biomasspowerout} TWh")
print(f"BECCS power out: {beccspowerout} TWh")
print(f"Biomass load factor: {BiomassDispatchable.get_load_factor()}")
print(f"clean power fraction:{cleanpowersum/(totaldemand+(8*365.25*24)/1000)}")
print(f"Yearly Solar power out: {yearlysolarpowerout} TWh")
print(f"Nuclear power out: {nuclearpowerout} TWh")
quit()

# %
np.save("gaspercent.npy", gaspercent)
np.save("unabatedgaspercent.npy", gaspercent)
# %%

Interconnectorimport = InterconnectorDispatchable.total_imported / (nyears * 10**6)

existingoffshoreloadfactors = [i.get_load_factor() for i in existingoffshoregenerators]
existingoffshorecapacities = [
    i.total_installed_capacity for i in existingoffshoregenerators
]
futureoffshoreloadfactors = [i.get_load_factor() for i in futureoffshoregenerators]
futureoffshorecapacities = [
    i.total_installed_capacity for i in futureoffshoregenerators
]
meanoffshoreloadfactor = np.average(
    existingoffshoreloadfactors + futureoffshoreloadfactors,
    weights=existingoffshorecapacities + futureoffshorecapacities,
)

totaloffshorepowerout = np.sum(
    [np.sum(i.power_out_array) for i in existingoffshoregenerators]
) + np.sum([np.sum(i.power_out_array) for i in futureoffshoregenerators])
yearlyoffshorepowerout = totaloffshorepowerout / (nyears * 10**6)
# %%
sns.set_theme()
plt.plot(additionaldemandlist, gaspercent)
# plot a horizontal line at 5%


plt.axhline(y=5, color="r", linestyle="--")
# plt.xlabel("Additional demand (GW)")
plt.xlabel("Offshore wind reduction (GW)")
plt.ylabel("Gas generation as % of total generation")
plt.title("Offshore wind redution vs gas generation")
plt.show()

# %%u
