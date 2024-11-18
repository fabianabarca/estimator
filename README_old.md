# GTFS Stop Times Estimator

An utility tool to estimate the arrival and departure times of the `stop_times` table in GTFS, based on several algorithms.

## Methods for creating a trip

These are the steps followed by the user of the system when creating a new trip, for which the stop times data must be generated:

GTFS data provides:

- Route
- Direction
- Calendar
- Shape
- Stops

System **user** selects, when entering a new trip:
1. Route (e.g.: San Gabriel): `route_id`.
2. Direction (e.g.: 0, to San José): `int` (0 or 1).
3. Calendar (e.g.: weekdays): `string` with the calendar's `service_id`.
4. Shape (e.g.: `hacia_sanjose`, this shape will tipically be the same for a given route): `shape_id`.
5. Trip times: `DataFrame` with the `trip_times` fields, i.e., `trip_id`, `stop_id`, `trip_time`, selected from a list of stops for a given route and shape, that is, from the `route_stops` table.
6. (*Optional*) Trip arrival time (for method A): Python's `DateTime` object.

Auxiliary tables (not part of GTFS):

- `route_stops`: provides the sequence of stops that a route follows in a given shape (trajectory), under the premise (our premise) that a route always follows the same sequence of stops for a given shape. Provided as a `DataFrame` with the records for the combination of `route_id` and `shape_id`.
- `trip_times`: provides the `arrival_time`/`departure_time` of selected "anchor" stops with `timepoint = 1`. Tipically, each trip will only need the specification of the `departure_time` at the first stop. Provided as a `DataFrame`.
- (*Optional*) `stop_times_measurements`: from where the table `polynomials` is created for method B.

These auxiliary tables are created when a new **route** is created.

#### API sketch

```python
# views.py

import databus_stoptimes as st
import pandas as pd
import geopandas as gpd
from .models import Route, GeoShape, RouteStop, Trip, StopTime, Stop

# Get here the data from the DB
def create_trip(request):
    """Creates a record on the trips table and estimates the stop times for the stop_times table

    """
    
    method = request.POST["method"]
    route_id = request.POST["request_id"]
    route = Route.objects.filter(route_id=route_id)
    route = pd.DataFrame(route) # tal vez
    direction_id = request.POST["direction_id"]
    service_id = request.POST["service_id"]
    shape_id = request.POST["shape_id"]
    shape = GeoShape.objects.filter(shape_id=shape_id)
    shape = gpd.GeoDataFrame(shape) # tal vez
    route_stops = RouteStops.objects.filter(route_id=route_id, shape_id=shape_id)
    route_stops = pd.DataFrame(route_stops)
    stops = [Stop.objects.get(stop_id=i) for i in route_stops["stop_id"]]
    stops = pd.DataFrame(stops)
    trip_times = request.POST["trip_times"]
    trip_times = pd.DataFrame(trip_times) # seguramente así no
    trip_id = f"{shape_id}{service_id}{trip_times[0]}"

    trip = Trip(
        route_id=route_id,
        service_id=service_id,
        trip_id=trip_id,
        direction_id=direction_id,
        shape_id=shape_id,
    )
    trip.save()

    stop_times = st.estimate(
        method=method,
        trip_id=trip_id,
        route=route,
        shape=shape,
        route_stops=route_stops,
        stops=stops,
        trip_times=trip_times,
    )
    StopTimes.objects.create(stop_times) # algo así
```

where:

- `stop_times` is a `DataFrame` built for a new trip with the following columns:
    - `trip_id`
    - `arrival_time`
    - `departure_time`
    - `stop_id`
    - `stop_sequence`
    - `timepoint`
    - `shape_dist_traveled`
    - (Other fields will be ignored, for now.)
- `method` chooses between our two algorithms: A and B (when available)
- `route` is a `DataFrame` with the route's record from `route_id`
- `shape` is a `GeoDataFrame` with the shape's record in the `GeoShape` model with the `shape_id`
- `trip_times` is a `DataFrame` with the following columns:
    - `trip_id`
    - `stop_id`
    - `trip_time`
- `route_stops` is a `DataFrame` containing the records of the `route_stops` database table for the combination of `route_id` and `shape_id`

### Method A: without historical data

### Method B: with historical data

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

    1. ***trip_id***
    2. ***arrival_time***
    3. departure_time
    4. ***stop_id***
    5. ***stop_sequence***
    6. stop_headsign
    7. pickup_type
    8. drop_off_type
    9. continuous_pickup
    10. continuous_drop_off
    11. ***shape_dist_traveled***
    12. ***timepoint***

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

### Estimator

```python
estimator(
    route=route_id,
    shape=shape_id,
    route_stops=tabla_paradas_rutas, # posiblemente hay que buscarlo directo en la DB
    stops=tabla_paradas, # posiblemente hay que buscarlo directo en la DB
    method={A, B},
    initial_stop=stop_id, 
    time_initial_stop=time_object, 
    last_stop=stop_id,
    time_last_stop=time_object,
)
```

returns:

- stop_id
- stop_sequence
- arrival_time `TimeDeltaObject` from time_initial_stop
- departure_time `TimeDeltaObject` from time_initial_stop

trip_departure_time: 6:10

P2 (timedelta) 120 (6:12)
P3 180 (6:13)
P4
P5

¿Qué hay dentro de la tabla de mediciones? (Más o menos lo de la tabla pivot)

stop_time_measurements

route_id shape_id trip_id date stop_id arrival_time departure_time

Recomendaciones:

- Construir una tabla stop_time_measurements de mentiras
- Calcular la función polinomial de mejor ajuste para una combinación (route_id shape_id trip_id date stop_id) como función de la hora de salida de la parada inicial
- Utilizar la función para hacer estimaciones de una nueva hora de salida.

Una función para estimar la función polinomial y otra aparte es "estimator" para una nueva hora del día.

Ejemplo: si f(t) = 3t^7 + 2.375t^6 - ... + 35 (unidad: segundos) para arrival_time de la parada stop_id (Educación), entonces el TimeDelta para una nueva hora del día es:

f(12:35) = 3(12:35)^7 + 2.375(12:35)^6 - ... + 35 = 264 segundos

Crear función f(t) para cada stop_id, para arrival_time y (por separado) para departure_time que describe el deltaT entre la parada anterior y la parada actual

Recordar que Python tiene formas de encontrar una curva polinomial de mejor ajuste.
