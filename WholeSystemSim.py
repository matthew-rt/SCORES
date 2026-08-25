"""This script gives an example of a whole system simulation"""
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

demand = np.loadtxt("W:/SCORES-DATA/demand.csv", usecols=2, delimiter=",", skiprows=1)

totaldemand = 352



demandstarttime = datetime.datetime(2009, 1, 1)
yearmin = 2009
yearmax = 2019


starttime = datetime.datetime(yearmin, 1, 1)
endtime = datetime.datetime(yearmax + 1, 1, 1)

startindex = int((starttime - demandstarttime).total_seconds() / 3600)
endindex = int((endtime - demandstarttime).total_seconds() / 3600)

numberofpoints = int((endtime - starttime).total_seconds() / 3600)
demand = demand[startindex:endindex]
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
    yearlysum = np.sum(demand[startindex:endindex])
    scalingfactor = yearlydemand * 10**6 / yearlysum
    demand[startindex:endindex] *= scalingfactor
    currentyear += 1


onshorecapacity = 30
offshorecapacity = 50

existingdata = pd.read_excel("W:/SCORES-DATA/repd-q3-oct-2024-trimmed.xlsx")
existingonshore = existingdata[existingdata["Technology Type"] == "Wind Onshore"].copy()
existingonshore = existingonshore[
    existingonshore["Development Status (short)"] == "Operational"
]
transformer = proj.Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)

existingonshore["Longitude"], existingonshore["Latitude"] = transformer.transform(
    existingonshore["X-coordinate"].values, existingonshore["Y-coordinate"].values
)

offshoredata = pd.read_excel("W:/SCORES-DATA/offshorewindpipeline.xlsx")

offshoredata["Longitude"], offshoredata["Latitude"] = transformer.transform(
    offshoredata["X-coordinate"].values, offshoredata["Y-coordinate"].values
)

winddatafolder = "W:/SCORES-DATA/era5wind/"
windsitelocs = np.loadtxt(winddatafolder + "site_locs.csv", skiprows=1, delimiter=",")
#%%
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
existingonshorenumberofturbines = onshoresitecapacities / 4 #dividing by 4 as we're assuming 4MW turbines
existingonshorenumberofturbines = [int(i) for i in existingonshorenumberofturbines]

existingonshorepowercurve=np.loadtxt("W:/SCORES-DATA/genericonshorepowercurve.csv", delimiter=",", skiprows=1)
existingonshorepowercurve[:,1]*=4 #scale the power curve to 4MW turbines




totalinstalledcapacity = np.sum(onshoresitecapacities)
existingonshoregenerator = generation.OnshoreWindModel(
    sites=existingonshoresites,
    year_min=yearmin,
    year_max=yearmax,
    data_path=winddatafolder,
    n_turbine=existingonshorenumberofturbines,
    force_run=True,
    power_curve=existingonshorepowercurve,
    turbine_size=4,
)

#%%




futureonshoreinstall = onshorecapacity * 10**3 - totalinstalledcapacity

scalesize = futureonshoreinstall / totalinstalledcapacity
scaledcapacities = onshoresitecapacities * scalesize
scalednumberofturbines = scaledcapacities / 7
scalednumberofturbines = [int(i) for i in scalednumberofturbines]

futureonshorepowercurve=np.loadtxt("W:/SCORES-DATA/genericonshorepowercurve.csv", delimiter=",", skiprows=1)
futureonshorepowercurve[:,1]*=7 #scale the power curve to 4MW turbines



futureonshoregenerator = generation.OnshoreWindModel(
    sites=existingonshoresites,
    year_min=yearmin,
    year_max=yearmax,
    data_path=winddatafolder,
    n_turbine=scalednumberofturbines,
    force_run=True,
    power_curve=futureonshorepowercurve,
    turbine_size=7
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

    powercurve=np.loadtxt(
        "W:/SCORES-DATA/genericoffshorepowercurve.csv",
        delimiter=",",
        skiprows=1,
    )
    powercurve[:,1] *= turbsize


    thissizegenerator = generation.OffshoreWindModel(
        sites=sites,
        year_min=yearmin,
        year_max=yearmax,
        data_path=winddatafolder,
        n_turbine=numberofturbines,
        force_run=True,
        power_curve=powercurve,
        turbine_size=turbsize,
    )

    existingoffshoregenerators.append(thissizegenerator)


futureoffshore = offshoredata[
    offshoredata["Estimated operational year"] != "Operational"
].copy()


existingoffshorecapacity = np.sum(
    [i.total_installed_capacity for i in existingoffshoregenerators]
)

futurecapacity = np.sum(futureoffshore["Installed Capacity (MWelec)"])
requiredfuturecapacity = offshorecapacity * 10**3 - existingoffshorecapacity
scalesize = requiredfuturecapacity / futurecapacity

futureoffshoresizes = futureoffshore["Comb turbine size"].unique().tolist()
futureoffshoregenerators = []

for turbsize in futureoffshoresizes:
    thisturbinsizedata = futureoffshore[futureoffshore["Comb turbine size"] == turbsize]
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

    powercurve = np.loadtxt(
        "W:/SCORES-DATA/genericoffshorepowercurve.csv",
        delimiter=",",
        skiprows=1,
    )
    powercurve[:, 1] *= turbsize

    thissizegenerator = generation.OffshoreWindModel(
        sites=sites,
        year_min=yearmin,
        year_max=yearmax,
        data_path=winddatafolder,
        n_turbine=numberofturbines,
        force_run=True,
        power_curve=powercurve,
        turbine_size=turbsize,
    )

    futureoffshoregenerators.append(thissizegenerator)


solardatapath = "W:/SCORES-DATA/adjustedsolar/"


solardata = pd.read_excel(
    "W:/SCORES-DATA/top10solar_modified.xlsx"
)

solardata["site"], solardata["Within 100Km"] = Loaderfunctions.latlongtosite(
    solardata["Latitude"],
    solardata["Longitude"],
    np.loadtxt(f"{solardatapath}site_locs.csv", skiprows=1, delimiter=","),
)

solarcapacity = 45
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

nucleargenerator=generation.NuclearModel(
            sites=[1],
            year_min=2009,
            year_max=2019,
            capacities=[nuclearinstalled*1000],
            loadfactor=0.9,
            hurdlerate=0.089,
            lifetime=60,
        )

generatorlist = (
    [existingonshoregenerator, futureonshoregenerator]
    + existingoffshoregenerators
    + futureoffshoregenerators
    + [solargenerator]+[nucleargenerator]
)

GasCCUSinstalled = 2
H2Pinstalled = 0.1
UnabatedGasinstalled = 32
Biomass = 2.5
BECCS = 0.5
Interconnectors = 12
# %%

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
system = ElectricitySystem(
    generatorlist,
    [lithiumstorage],
    demand=demand,
    DispatchableAssetList=DispatchableAssetList,
    Interconnector=InterconnectorDispatchable,
)
system.update_surplus()
reliability = system.get_reliability()
nyears = yearmax - yearmin + 1

unabatedgaspercent = (
    100 * np.sum(UnabatedGasDispatchable.power_out_array) / np.sum(demand)
)



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


summedoffshorepoweroutarray = np.sum(
    np.vstack([i.power_out_array for i in existingoffshoregenerators]), axis=0
) + np.sum(np.vstack([i.power_out_array for i in futureoffshoregenerators]), axis=0)
totaloffshorecapapcity = np.sum(existingoffshorecapacities) + np.sum(
    futureoffshorecapacities
)


summedonshorepoweroutarray = (
    existingonshoregenerator.power_out_array + futureonshoregenerator.power_out_array
)


totalonshorecapacity = existingonshorecapacity + futureonshorecapacity
curtailedarray = system.storage.curtarray
gaspowerout = UnabatedGasDispatchable.power_out_array
interconnectoroutputarray = InterconnectorDispatchable.power_out_array


print(f"Installed onshore capacity: {existingonshorecapacity + futureonshorecapacity}")
print(
    f"Installed offshore capacity: {np.sum(existingoffshorecapacities + futureoffshorecapacities)}"
)

print(f"Mean onshore load factor: {meanonshoreloadfactor}")
print(f"Yearly onshore power out: {yearlyonshorepowerout} TWh")
print(f"Mean offshore load factor: {meanoffshoreloadfactor}")
print(f"Yearly offshore power out: {yearlyoffshorepowerout} TWh")

yearlysolarpowerout = np.sum(solargenerator.power_out_array) / (nyears * 10**6)
nuclearpowerout = np.sum(nuclearinstalled * nuclearloadfactor * 365.25 * 24) / (10**3)
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
print(f"Yearly clean power out: {cleanpowersum} TWh")
print(f"Yearly biomass power out: {biomasspowerout} TWh")
print(f"Biomass load factor: {BiomassDispatchable.get_load_factor()}")
print(f"clean power fraction:{cleanpowersum/352}")
print(f"Yearly Solar power out: {yearlysolarpowerout} TWh")
print(f"Nuclear power out: {nuclearpowerout} TWh")
# %%

yearindeces = []
years = [i for i in range(yearmin, yearmax + 1)]
startdatetime = datetime.datetime(yearmin, 1, 1)
currentyear = yearmin
currenttime = startdatetime
latestpoint = len(demand)
while currenttime < endtime:
    startindex = int((currenttime - startdatetime).total_seconds() / 3600)
    endindex = int(
        (datetime.datetime(currentyear + 1, 1, 1) - startdatetime).total_seconds()
        / 3600
    )
    if endindex > latestpoint:
        endindex = latestpoint
    yearindeces.append((startindex, endindex))
    currentyear += 1
    currenttime = datetime.datetime(currentyear, 1, 1)


offshoreloadfactors = []
onshoreloadfactors = []
yearlycurtailements = []
yearlyinterconnectorexports = []
yearlyinterconnectorimports = []
yearlygasusage = []


for yearindex in range(len(years)):
    startindex, endindex = yearindeces[yearindex]
    offshoreloadfactor = np.sum(
        100 * summedoffshorepoweroutarray[startindex:endindex]
    ) / (totaloffshorecapapcity * (endindex - startindex))
    offshoreloadfactors.append(offshoreloadfactor)
    onshoreloadfactor = np.sum(
        100 * summedonshorepoweroutarray[startindex:endindex]
    ) / (totalonshorecapacity * (endindex - startindex))
    onshoreloadfactors.append(onshoreloadfactor)

    yearlycurtailement = np.sum(curtailedarray[startindex:endindex]) / 10**6
    yearlycurtailements.append(yearlycurtailement)

    yearinterconnectorarray = interconnectoroutputarray[startindex:endindex]
    yearlyinterconnectorexport = -1 * (
        np.sum(yearinterconnectorarray[yearinterconnectorarray < 0]) / 10**6
    )
    yearlyinterconnectorimport = (
        np.sum(yearinterconnectorarray[yearinterconnectorarray > 0]) / 10**6
    )

    yearlyinterconnectorexports.append(yearlyinterconnectorexport)
    yearlyinterconnectorimports.append(yearlyinterconnectorimport)

    yearlygasusage.append(
        100 * np.sum(gaspowerout[startindex:endindex]) / (totaldemand * 10**6)
    )


# create a plot with 3 rows and 2 columns
sns.set_theme()


palette = sns.color_palette()
fig, ax = plt.subplots(3, 2, figsize=(10, 8))

# plot the onshore load factors on the top left subplot
minwindloadfactor = np.min(onshoreloadfactors)
maxwindloadfactor = np.max(offshoreloadfactors)
axesminpoint = minwindloadfactor - 5
axesmaxpoint = maxwindloadfactor + 5
ax[0, 0].plot(years, onshoreloadfactors, marker="o", color=palette[0])
ax[0, 0].set_title("Onshore Load Factors")
ax[0, 0].set_xlabel("Year")
ax[0, 0].set_ylabel("Load Factor (%)")
ax[0, 0].set_ylim(axesminpoint, axesmaxpoint)

ax[0, 1].plot(years, offshoreloadfactors, marker="o", color=palette[1])
ax[0, 1].set_title("Offshore Load Factors")
ax[0, 1].set_xlabel("Year")
ax[0, 1].set_ylabel("Load Factor (%)")
ax[0, 1].set_ylim(axesminpoint, axesmaxpoint)

mininterconnectorval = np.min(yearlyinterconnectorexports + yearlyinterconnectorimports)
maxinterconnectorval = np.max(yearlyinterconnectorexports + yearlyinterconnectorimports)
interaxesminpoint = mininterconnectorval - 5
interaxesmaxpoint = maxinterconnectorval + 5
ax[1, 0].plot(years, yearlyinterconnectorexports, marker="o", color=palette[2])
ax[1, 0].set_title("Yearly Interconnector Export")
ax[1, 0].set_xlabel("Year")
ax[1, 0].set_ylabel("Export (TWh)")
ax[1, 0].set_ylim(interaxesminpoint, interaxesmaxpoint)

ax[1, 1].plot(years, yearlyinterconnectorimports, marker="o", color=palette[3])
ax[1, 1].set_title("Yearly Interconnector Import")
ax[1, 1].set_xlabel("Year")
ax[1, 1].set_ylabel("Import (TWh)")
ax[1, 1].set_ylim(interaxesminpoint, interaxesmaxpoint)

ax[2, 0].plot(years, yearlycurtailements, marker="o", color=palette[4])
ax[2, 0].set_title("Yearly Curtailment")
ax[2, 0].set_xlabel("Year")
ax[2, 0].set_ylabel("Curtailment (TWh)")
ax[2, 0].set_ylim(np.min(yearlycurtailements) - 5, np.max(yearlycurtailements) + 5)

ax[2, 1].plot(years, yearlygasusage, marker="o", color=palette[5])
ax[2, 1].set_title("Unabated Gas Usage")
ax[2, 1].set_xlabel("Year")
ax[2, 1].set_ylabel("Usage (%)")
ax[2, 1].set_ylim(2, 8)
ax[2, 1].hlines(
    5, yearmin, yearmax, linestyles="dashed", label="Threshold", color="gray"
)
plt.suptitle("Previous load factors")
plt.tight_layout()
plt.show()


# %%

existingonshoreprofile = existingonshoregenerator.power_out_array
futureonshoreprofile = futureonshoregenerator.power_out_array
existingoffshoreoutput = np.sum(
    np.vstack([i.power_out_array for i in existingoffshoregenerators]), axis=0
)
futureoffshoreoutput = np.sum(
    np.vstack([i.power_out_array for i in futureoffshoregenerators]), axis=0
)
solaroutput = solargenerator.power_out_array

powernames = [
    "Existing Onshore",
    "Future Onshore",
    "Existing Offshore",
    "Future Offshore",
    "Solar",
]
powerprofiles = [
    existingonshoreprofile,
    futureonshoreprofile,
    existingoffshoreoutput,
    futureoffshoreoutput,
    solaroutput,
]
numberofweeks = int(len(existingonshoreprofile) / (24 * 7))
powerprofiles = [i[: int(numberofweeks * 24 * 7)] for i in powerprofiles]
powerprofiles = [i / 1000 for i in powerprofiles]
weeklypowerprofiles = [np.mean(i.reshape(-1, 24 * 7), axis=1) for i in powerprofiles]
for i in range(len(powernames)):
    plt.plot(weeklypowerprofiles[i], label=powernames[i])
plt.legend()
plt.ylabel("Power (GW)")
plt.show()
# %%
dispatchablenames = []
dispatchablepowerout = []
for i in DispatchableAssetList:
    dispatchablenames.append(i.name)
    dispatchablepowerout.append(i.power_out_array)
dispatchablepowerout = [i / 1000 for i in dispatchablepowerout]
numberofweeks = int(len(existingonshoreprofile) / (24 * 7))

dispatchablepowerout = [i[: int(numberofweeks * 24 * 7)] for i in dispatchablepowerout]
weeklydispatchablepowerout = [
    np.mean(i.reshape(-1, 24 * 7), axis=1) for i in dispatchablepowerout
]
for i in range(len(dispatchablenames)):
    plt.plot(weeklydispatchablepowerout[i], label=dispatchablenames[i])
plt.legend()
plt.ylabel("Power (GW)")
plt.show()
# %%
