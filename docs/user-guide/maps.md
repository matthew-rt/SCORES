# Maps and load factors

`maps.py` estimates and visualises renewable load factors across Great
Britain, using the same weather data as the generation models.

!!! danger "maps.py currently fails to import"
    `maps.py` imports fixed-size turbine classes
    (`OffshoreWindModel10000`, `OnshoreWindModel3600`, etc.) that were
    removed from `generation.py` when turbine size became a constructor
    parameter, so `import maps` raises an `ImportError` until the import
    list is updated. The documentation below describes the intended
    behaviour.

## LoadFactorEstimator

Estimates the long-run load factor of a technology at an arbitrary
latitude/longitude by inverse-distance-weighting the load factors of the
nearest weather sites:

```python
from maps import LoadFactorEstimator

lfe = LoadFactorEstimator("s", data_loc="data/solar/")   # "s" = solar
lf = lfe.estimate(lat=51.48, lon=0.00)
```

Technology codes follow the cache-file naming convention from
`fns.get_filename` (e.g. `s` solar, `w` onshore wind, `osw` offshore wind).
Computed load factors are cached so subsequent estimators are fast.

## LoadFactorMap and subclasses

`LoadFactorMap` draws a colour map of load factor over a lat/lon grid,
masking land or sea as appropriate. Convenience subclasses configure the
grid and technology:

- `OffshoreWindMap` — offshore (sea) points only.
- `OnshoreWindMap` — land points, `turbine_size` selectable.
- `SolarMap` — land points.

```python
from maps import OnshoreWindMap
OnshoreWindMap(lat_num=40, lon_num=30, quality="l",
               turbine_size=5.0, data_loc="data/wind/").draw_map()
```

`lat_num`/`lon_num` set grid resolution and `quality` the coastline detail
("l" low … "h" high); high-resolution maps are slow because a generation
model is evaluated for every grid point.

`CorrelationCalculator` produces analogous maps of the correlation between
a candidate site's output and an existing portfolio — useful for finding
sites that *decorrelate* the fleet.

`LandCheck` is a small utility (built on Cartopy shapes) that reports
whether a coordinate is on land, used for masking.

## Related helpers

`Loaderfunctions.py` maps real-world installations onto weather sites:

- `latlongtosite(latitudes, longitudes, sitelist)` — nearest weather site
  for each coordinate (plus a flag for whether it is within 100 km).
- `greatcircledistance(pointa, pointb)` — haversine distance.

`excelloaderexample.py` shows the intended workflow: load a spreadsheet of
real wind farms (locations, turbine counts and sizes), find each farm's
nearest weather site with `latlongtosite`, then build generation models
grouped by turbine size.

`loadfactorplotter.py` is a small script that plots load factor versus
turbine size from CSVs produced by earlier analysis runs.
