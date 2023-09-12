# GTFS Stop Times Estimator

An utility tool to estimate the arrival and departure times of the `stop_times` table in GTFS, based on several algorithms.

## Inputs and outputs

### Inputs

- `trip_id`:
- `trip_departure_time`:
- `trip_arrival_time`:
- `route_stops` (table):
- `anchor_times` (table):
- `stops` (table):
- `shapes` (table):

### Intermediate variables

- `distance_from_last_stop`: 

### Outputs

- A `stop_times` table with the estimation of departure/arrival times to each stop for a given trip.


## Premises

### The way it is done in Costa Rica

- This is not a universal estimator of stop times.
- In Costa Rica, schedules are usually for fixed-times : a departure time.
- We define a "route" as a service having all trips with a single shape (trajectory) and a fixed sequence of stops, therefore, a service that might start and end in the same place (e.g., "Turrialba") but follows a different set of stops (e.g., "Expreso" and "Colectivo") are two separate routes (e.g., "Turrialba Expreso" and "Turrialba Colectivo").

### GTFS

- This package uses the GTFS revision of March 14, 2023.
- The fields of the `stop_times.txt` table are:
    - ***trip_id***
    - ***arrival_time***
    - departure_time
    - ***stop_id***
    - ***stop_sequence***
    - stop_headsign
    - pickup_type
    - drop_off_type
    - continuous_pickup
    - continuous_drop_off
    - ***shape_dist_traveled***
    - ***timepoint***

### Data handling

- Data will be handled with [Pandas](https://pandas.pydata.org/)
- Geospatial data (e.g. `shapes.txt`) will be handled with [GeoPandas](https://geopandas.org/)

Note: geospatial data > geometries > (point, line, polygon, multipolygon)


```python
import trips2stoptimes as t2s

stops = t2s.get_stops_from_file('stops.txt')

stops = t2s.get_stops_from_db(asdfasdj)
```

### Possible functions

- `get_stops()`: reading and validation of stops data.
- `geojson_to_shapes`: converting a GeoJSON file to a valid GTFS `shapes.txt` file.

### Notes to self

- Generalize `trip_departure_time` and `trip_arrival_time` with `trip_anchor_time` where the departure time ("first stop") and arrival time ("last stop") are set as such by default, but allowing other "inner" stops to be set as well, thus allowing the special cases like San Gabriel where we have "los Mangos" as fixed time and then San Gabriel as well.