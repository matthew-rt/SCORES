# %%
from generation import OnshoreWindModel
import pandas as pd
import numpy as np
import Loaderfunctions
import rasterio
import pyproj as proj
import datetime
import json

onshoresitelist = pd.read_excel("c:/Users/Ryantuckerm1/Documents/grosstonet/onshorewithsite.xlsx")

winddatafolder = "W:/SCORES-DATA/era5wind/"
windsitelocs = np.loadtxt(winddatafolder + "site_locs.csv", skiprows=1, delimiter=",")

pressuredata = "W:/SCORES-DATA/pressure/"
temperaturedata = "W:/SCORES-DATA/temp/"

pressuresitelocs = np.loadtxt(
    pressuredata + "site_locs.csv", skiprows=1, delimiter=","
)
temperaturesitelocs = np.loadtxt(
    temperaturedata + "site_locs.csv", skiprows=1, delimiter=","
)
(
    onshoresitelist["site"],
    onshoresitelist["Within 100Km"],
) = Loaderfunctions.latlongtosite(
    onshoresitelist["Latitude"], onshoresitelist["Longitude"], windsitelocs
)

onshoresitelist["pressure site"], onshoresitelist["Within 100Km"] = Loaderfunctions.latlongtosite(
    onshoresitelist["Latitude"],
    onshoresitelist["Longitude"],
    pressuresitelocs,
)
onshoresitelist["temperature site"], onshoresitelist["Within 100Km"] = Loaderfunctions.latlongtosite(
    onshoresitelist["Latitude"],
    onshoresitelist["Longitude"],
    temperaturesitelocs,
)


# convert site numbers to integers
onshoresitelist["site"] = onshoresitelist["site"].astype(int)
onshoresitelist["pressure site"] = onshoresitelist["pressure site"].astype(int)
onshoresitelist["temperature site"] = onshoresitelist["temperature site"].astype(int)
#save the onshore list to the same location as the excel file
onshoresitelist.to_excel("c:/Users/Ryantuckerm1/Documents/grosstonet/onshorewithsite.xlsx", index=False)
# %%
meanwindspeeds = np.loadtxt(
    winddatafolder + "meanwindspeeds.csv", skiprows=1, delimiter=",", usecols=1
)

yearmin = 2020
yearmax = 2023

startdatetime = datetime.datetime(yearmin, 1, 1, 0, 0, 0)
enddatetime = datetime.datetime(yearmax, 12, 31, 23, 0, 0)
currenttime = startdatetime
datetimestringlist = []
while currenttime <= enddatetime:
    datetimestringlist.append(currenttime.strftime("%Y-%m-%d %H:%M:%S"))
    currenttime += datetime.timedelta(hours=1)

raster_file = "w:/SCORES-DATA/GBR_wind-speed_100m.tif"
outputfolder = "c:/Users/Ryantuckerm1/Documents/grosstonet/nodensity/"
src = rasterio.open(raster_file)
print(src.crs)
# %%
for index, row in onshoresitelist.iterrows():
    latitude, longitude = row["Latitude"], row["Longitude"]
    print(latitude, longitude)
    name = row["Site Name"]
    hubheight = row["Hub Height"]
    folderlocation = (
        f"W:/SCORES-DATA/onshorewindfarms/{name}/greedy/"
    )
    coords = np.loadtxt(
        folderlocation + "turbinecoordinates.csv", delimiter=",", skiprows=1
    )
    sitemetadata = json.load(
        open(
            f"{folderlocation}siteinfo.json"
        ))
    
    gwavals = []
    # gwaval = list(src.sample([(longitude, latitude)]))

    for coord in coords:
        longtitude, latitude = coord[0], coord[1]
        samplevalue = src.sample([(coord[1], coord[0])])
        samplevalue = list(samplevalue)

        gwavals.append(samplevalue[0][0])
    gwaval = np.mean(gwavals)
    elevation= sitemetadata["Elevation"]
    site = row["site"]
    turbinesize= float(row["Turbine Capacity (MW)"])
    # turbinesize = round(2 * row["Turbine Capacity (MW)"]) / 2
    # if turbinesize - turbinesize // 1 == 0:
    #     turbinesizelabel = f"{str(int(turbinesize))}_MW"
    # else:
    #     turbinesizelabel = f"{str(turbinesize)}_MW"
    
    powercurve=np.loadtxt(f"C:/Users/Ryantuckerm1/Documents/WT_PowerCurveModel-master/sitespecificcurves/{name}.csv", delimiter=',', skiprows=1, usecols=(0, 8))
    densitypowercurves=f"C:/Users/Ryantuckerm1/Documents/WT_PowerCurveModel-master/sitespecificcurves/{name}.csv"
    # densitypowercurves = "C:/Users/Ryantuckerm1/Documents/powercurvesim/powercurvesim.csv"
    print(meanwindspeeds[site - 1], gwaval)
    print(f"Site: {name}")
    print(f"Site hub height {hubheight}m")
    generatorobject = OnshoreWindModel(
        sites=[site],
        n_turbine=[1],
        technical_params_file=None,
        year_min=yearmin,
        year_max=yearmax,
        data_path=winddatafolder,
        turbine_size=turbinesize,
        era_mean_wind_speed=[meanwindspeeds[site - 1]],
        gwa_mean_wind_speed=[gwaval],
        density_correction=False,
        pressurefile=pressuredata,
        temperaturefile=temperaturedata,
        pressuresites=[row["pressure site"]],
        temperaturesites=[row["temperature site"]],
        siteelevations= [elevation],
        supplementalpowercurves= densitypowercurves,
        force_run=True,
        hub_height=hubheight,
        v_cut_in=3,
        v_cut_out=28,
        rated_wind_speed=12,
        power_curve=powercurve,
        rotor_diameter=row["Turbine Diameter"]
    )
    print(np.max(generatorobject.power_out_array))
    print(f"Turbine size {turbinesize} MW")
    powerout = generatorobject.power_out_array / turbinesize
    print(f"load factor {generatorobject.get_load_factor()}")
    print(f"---")
    with open(f"{outputfolder}{name}.csv", "w") as f:
        f.write("datetime,Load factor\n")
        for i, power in enumerate(powerout):
            f.write(f"{datetimestringlist[i]},{power}\n")
# %%
