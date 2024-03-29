import numpy as np


def latlongtosite(latitude, longitude, listofsites):
    """takes as input a latitude, longitude, and a list of sites. Returns the index of the closest sites, and a bool: if the closest site is more than
    100km away, the bool is False
    Parameters
    -----
    latitude: float
        latitude of the coordinate, wth + meaning N and - meaning south
    longitude: float
        longitude of the coordinate, with + meaning E and - meaning W
    listofsites: list
        list of the data sites. Header line is: Site, Latitude, Longitude
        Each subsequent line is: siteindex (int), latitude(float), longitude(float)

    Returns
    -----
    lowestsiteindex: int
        index of closest site
    close: bool
        True if distance <100Km, False if more
    """

    sites = listofsites
    # sites=listofsites[1:] #removes header
    greatcircledistances = [
        greatcircledistance([latitude, longitude], [float(i[1]), float(i[2])])
        for i in sites
    ]  # calculates distance between coordinate and each site
    greatcircledistances = np.array(greatcircledistances)
    lowestindex = np.argmin(greatcircledistances, axis=0)
    lowestsiteindex = sites[lowestindex][:, 0]
    # creates a list of the with the lowest distance for each row
    lowestdistance = [
        greatcircledistances[lowestindex[i], i] for i in range(len(lowestindex))
    ]

    close = [i < 100 for i in lowestdistance]
    # if lowestdistance < 100:
    #     close = True
    # else:
    #     close = False

    return lowestsiteindex, close


def greatcircledistance(pointa, pointb):
    """takes 2 points, and calculates the great circle distance between them

    Parameters
    -----
    pointa: list
        list in order [lat, long], in degrees

    pointb: list
        list in order [lat, long], in degrees

    Returns
    -----

    dist: float
        distance between points in km
    """

    longa = np.radians(pointa[0])
    lata = np.radians(pointa[1])
    longb = np.radians(pointb[0])
    latb = np.radians(pointb[1])

    centralangle = np.arccos(
        np.sin(lata) * np.sin(latb)
        + np.cos(lata) * np.cos(latb) * np.cos(abs(longa - longb))
    )
    dist = 6371 * centralangle

    return dist


def generationtiles(generatorkeys, turbinecapacities):
    """takes a list of generator keys and a list of turbine capacities, and returns a list of the closest generator key for each turbine capacity

    Parameters
    -----
    generatorkeys: list
        list of generator keys

    turbinecapacities: list
        list of turbine capacities

    Returns
    -----
    closestgenerator: list
        list of the closest generator key for each turbine capacity
    """

    tiledgens = np.tile(generatorkeys, (len(turbinecapacities), 1))
    tiledcaps = np.tile(turbinecapacities, (len(generatorkeys), 1)).T

    closestgenerator = [
        generatorkeys[i] for i in np.argmin(abs(tiledcaps - tiledgens), axis=1)
    ]

    return closestgenerator
