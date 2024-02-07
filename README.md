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
1. Route (e.g.: San Gabriel): `DataFrame` with the route's record.
2. Direction (e.g.: 0, to San José): `int` (0 or 1).
3. Calendar (e.g.: weekdays): `DataFrame` with the calendar's record.
4. (*Optional*) Shape (e.g.: `hacia_sanjose`, this shape will tipically be the same): `GeoDataFrame` with the shape's record.
5. Trip departure time: Python's `DateTime` object.
6. (*Optional*) Trip arrival time (for method A): Python's `DateTime` object.

Auxiliary tables (not part of GTFS):
- `route_stops`: provides the sequence of stops that a route follows in a given shape (trajectory), under the premise (our premise) that a route always follows the same sequence of stops for a given shape. Provided as a `DataFrame` with the records for the combination of `route_id` and `shape_id`.
- `trip_times`: provides the `arrival_time`/`departure_time` of selected "anchor" stops with `timepoint = 1`. Tipically, each trip will only need the specification of the `departure_time` at the first stop. Provided as a `DataFrame`.
- (*Optional*) `stop_times_measurements`: from where the table `polynomials` is created for method B.

These auxiliary tables are created when a new **route** is created.

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

