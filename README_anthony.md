# GTFS Stop Times Estimador

## Tabla de Contenidos
- [GTFS Stop Times Estimador](#gtfs-stop-times-estimador)
  - [Tabla de Contenidos](#tabla-de-contenidos)
  - [Introducción](#introducción)
  - [Inputs](#inputs)
  - [Outputs](#outputs)
  - [Manejo de datos](#manejo-de-datos)
  - [Código y Funcionamiento](#código-y-funcionamiento)
  - [Notas](#notas)

## Introducción
El estimador es una herramienta basada en un algoritmo para aproximar los tiempos de llegada de la tabla `stops_times.csv` en GTFS. Este algoritmo, para realizar la estimación utiliza como base mediciones de tiempos de llegada a cada parada de los viajes establecidos por la empresa transportista.

## Inputs
- `stops_measurement` (tabla): Contiene las mediciones de tiempos de llegada a cada parada de los diferentes viajes. Se le añade durante el código la columna ‘delay’, la cual hace referencia al tiempo de retardo en cada parada con respecto al inicio del viaje.
- `route_id`: Identificador de ruta GTFS.
- `service_id`: Identificador del tipo de servicio GTFS.
- `shape_id`: Identificador de la secuencia de paradas GFTS.
- `polynomials`: Contiene la función polinomial de mejor ajuste para cada parada, dada una combinación única de 'route_id', 'service_id', 'shape_id' y 'stop_id'.
- `start_time`: Hora de inicio del viaje.

## Outputs
La tabla `stops_times.csv` compuesta por las columnas:
- `trip_id`
- `arrival_time`
- `departure_time`
- `stop_id`
- `stop_sequence`
- `timepoint`
- `stop_headsign`
- `pickup_type`
- `drop_off_type`
- `continuous_pickup`
- `continuous_drop_off`

## Manejo de datos
Se utilizan los siguientes paquetes de Python:
- [Pandas](https://pandas.pydata.org/): Manipulación de los dataframes.
- [Numpy](https://pypi.org/project/numpy/): Permite utilizar la función [polyfit](https://numpy.org/doc/stable/reference/generated/numpy.polyfit.html)() y obtener los ajustes polinomiales en cada parada.
- [Matplotlib](https://pypi.org/project/matplotlib/): Visualización del comportamiento de los ajustes polinomiales.

## Código y Funcionamiento

Antes de realizar la función `estimator()`, se debe trabajar en los inputs. Primero, se trabaja en la tabla `stops_measurement`, a la cual se le añaden las columnas `delay` y `trip_departure_time`:

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

stops_measurement = pd.read_csv('stop_times_measurement.csv')
def calcular_delay(group):
    # Convierte la columna 'arrival_time' en objetos de tiempo
    group['arrival_time'] = pd.to_datetime(group['arrival_time'], format='%H:%M:%S')

    # Índice del primer 'stop_id' donde 'timepoint' es igual a 1
    primer_timepoint_idx = group[group['timepoint'] == 1].index[0]

    # Calcula el retraso restando los tiempos de 'arrival_time'
    group['delay'] = (group['arrival_time'] - 
    group.loc[primer_timepoint_idx, 'arrival_time']).dt.total_seconds()

    return group

# Aplicar la función a cada grupo (trip_id, date)
stops_measurement = stops_measurement.groupby(['trip_id', 'date']).apply(calcular_delay)

# Reiniciar el índice del DataFrame resultante
stops_measurement.reset_index(drop=True, inplace=True)

stops_measurement['arrival_time'] = stops_measurement['arrival_time'].dt.strftime('%H:%M:%S')

# Crear columna 'trip_departure_time'
stops_measurement['trip_departure_time'] = stops_measurement.groupby('trip_id')['arrival_time'].transform('first')
``````
Las columnas ‘delay’ y ‘trip_departure_time’ ambas en segundos, serán los argumentos X y Y de la función [polyfit](https://numpy.org/doc/stable/reference/generated/numpy.polyfit.html)() que se aplica a cada parada de las combinaciones únicas de `route_id`, `service_id`, `shape_id` y `stop_id`:

```python
import warnings
warnings.filterwarnings("ignore")

combinations = stops_measurement[['route_id', 'service_id', 'shape_id', 'stop_id']].drop_duplicates()

# Crear un diccionario para almacenar los polinomios
polynomials = {}

for i, combination in combinations.iterrows():
    subset = stops_measurement[(stops_measurement['route_id'] == combination['route_id']) &
                               (stops_measurement['service_id'] == combination['service_id']) &
                               (stops_measurement['shape_id'] == combination['shape_id']) &
                               (stops_measurement['stop_id'] == combination['stop_id'])]

    if not subset.empty:
        x_values = pd.to_datetime(subset['trip_departure_time'], format='%H:%M:%S').dt.hour * 3600 + \
                    pd.to_datetime(subset['trip_departure_time'], format='%H:%M:%S').dt.minute * 60 + \
                    pd.to_datetime(subset['trip_departure_time'], format='%H:%M:%S').dt.second

        degree = 4  # Grado del polinomio, puede ajustarse según las necesidades
        coefficients = np.polyfit(x_values, subset['delay'], degree)
        polynomial = np.poly1d(coefficients)
        polynomials[tuple(combination)] = polynomial
``````
*Opcional*

Si se desea observar el comportamiento del ajuste polinomial en una o varias paradas específicas se puede ejecutar el siguiente código:
```python
# Seleccionar manualmente la combinación que se desea visualizar
selected_combinations = [
    ('bUCR_L2', 'entresemana', 'desde_educacion_sin_milla', 'UCR_0_05'),
    ('bUCR_L2', 'entresemana', 'desde_educacion_sin_milla', 'UCR_0_06'),
]

for selected_combination in selected_combinations:

    # Visualizar el resultado con un gráfico para la combinación seleccionada
    if selected_combination in polynomials:
        subset = stops_measurement[(stops_measurement['route_id'] == selected_combination[0]) &
                                   (stops_measurement['service_id'] == selected_combination[1]) &
                                   (stops_measurement['shape_id'] == selected_combination[2]) &
                                   (stops_measurement['stop_id'] == selected_combination[3])]

        x_values = pd.to_datetime(subset['trip_departure_time'], format='%H:%M:%S').dt.hour * 3600 + \
                    pd.to_datetime(subset['trip_departure_time'], format='%H:%M:%S').dt.minute * 60 + \
                    pd.to_datetime(subset['trip_departure_time'], format='%H:%M:%S').dt.second
        x = np.linspace(20000,50000,60)

        plt.scatter(x_values, subset['delay'], label='Datos reales')
        plt.plot(x, polynomials[selected_combination](x), color='red',
                 label=f'Ajuste polinomial (grado {degree}),{selected_combination[3]}')
        plt.xlabel('Trip Departure Time (s)')
        plt.ylabel('Delay (s)')
        plt.title(f'Ajuste Polinomial para la Combinación {selected_combination}')
        plt.legend()

    else:
        print(f"No hay datos para la combinación {selected_combination}.")
        
plt.show()
``````
Finalmente, el estimador requiere conocer la secuencia de paradas a la que le realizará la estimación de tiempo de llegada, con lo cual se realiza la función auxiliar `get_sequence_of_stops()`:
```python
route_stops= pd.read_csv('route_stops.csv')

def get_sequence_of_stops(route_id, shape_id, route_stops):
    stops_sequence = route_stops[
        (route_stops['route_id'] == route_id) &
        (route_stops['shape_id'] == shape_id)
    ]

    # Encontrar todas las paradas para la combinación dada
    sequence_of_stops = stops_sequence['stop_id'].unique()
    
    return sequence_of_stops
``````
Ahora se tienen todos los datos necesarios para realizar `estimator`:
```python
def estimator(route_id, service_id, shape_id, start_time, polynomials, stops_measurement):
    # Obtener la secuencia de paradas para la combinación dada
    sequence_of_stops = get_sequence_of_stops(route_id, shape_id, stops_measurement)
    
    estimated_arrival_times = {}
    departure_time = pd.to_datetime(start_time, format='%H:%M')

    # Iterar sobre cada parada en la secuencia
    for stop_id in sequence_of_stops:
        if (route_id, service_id, shape_id, stop_id) in polynomials:
            # Obtener la función polinomial correspondiente a esta parada
            polynomial_function = polynomials[(route_id, service_id, shape_id, stop_id)]

            # Calcular el tiempo de llegada estimado usando la función polinomial y el tiempo de inicio especificado
            x_seconds = departure_time.hour * 3600 + departure_time.minute
            estimated_delay = polynomial_function(x_seconds)
            
            # Calcular el tiempo estimado de llegada sumando el retraso a la hora inicial especificada
            estimated_arrival = departure_time + pd.Timedelta(seconds=estimated_delay)
            
            # Guardar el tiempo estimado de llegada para esta parada en el diccionario
            estimated_arrival_times[stop_id] = estimated_arrival.strftime('%H:%M:%S')
        else:
            # No hay datos polinomiales para esta parada
            estimated_arrival_times[stop_id] = "No se puede estimar"

    return sequence_of_stops, estimated_arrival_times
``````
 `estimator` itera sobre cada parada y busca la función polinomial correspondiente a esa parada. Seguidamente convierte el tiempo de salida del viaje a segundos, el cual se sustituye en la función polinomial, esto da como resultado el tiempo de retardo en cada parada. Finalmente se suma ese tiempo de retardo a la hora de inicio del viaje y así se obtiene la hora estimada de llegada.

Utilizando `estimator` es posible generar la tabla `stop_times` GTFS:
```python
def generate_stop_times_df():

    trip_times= pd.read_csv('trip_times.csv')
    trips= pd.read_csv('trips.csv')

    # Crear un DataFrame vacío para acumular los resultados
    stop_times_df = pd.DataFrame(columns=[
        "trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence",
        "timepoint", "shape_dist_traveled", "stop_headsign", "pickup_type",
        "drop_off_type", "continuous_pickup", "continuous_drop_off"
    ])

    # Iterar sobre las filas del DataFrame trip_times
    for index, row in trip_times.iterrows():
        trip_id = row['trip_id']
        start_time = row['trip_departure_time']

        # Reemplazar stops_measurement por trips
        route_id = trips.loc[trips["trip_id"] == trip_id, "route_id"].values[0]
        service_id = trips.loc[trips["trip_id"] == trip_id, "service_id"].values[0]
        shape_id = trips.loc[trips["trip_id"] == trip_id, "shape_id"].values[0]

        # Llamada a la función estimator
        sequence_of_stops, estimated_arrival_times = estimator(route_id, service_id, shape_id, start_time, polynomials)

        timepoint_values = [1 if i == 0 else 0 for i in range(len(sequence_of_stops))]

        # Construcción de stop_times_iteration para esta iteración
        stop_times_iteration = pd.DataFrame({
            "trip_id": [trip_id] * len(sequence_of_stops),
            "arrival_time": list(estimated_arrival_times.values()),
            "departure_time": list(estimated_arrival_times.values()),
            "stop_id": sequence_of_stops,
            "stop_sequence": range(len(sequence_of_stops)),
            "timepoint": timepoint_values,
            "shape_dist_traveled": [0] * len(sequence_of_stops),
            "stop_headsign": [0] * len(sequence_of_stops),
            "pickup_type": [0] * len(sequence_of_stops),
            "drop_off_type": [0] * len(sequence_of_stops),
            "continuous_pickup": [0] * len(sequence_of_stops),
            "continuous_drop_off": [0] * len(sequence_of_stops),
        })

        # Concatenar los resultados de esta iteración al DataFrame principal
        stop_times_df = pd.concat([stop_times_df, stop_times_iteration], ignore_index=True)
    return stop_times_df
``````
## Notas

1. A la hora de generar la tabla completa `stop_times` es necesario importar la siguientes tablas de la base de datos GTFS:
   - trips: se utiliza para que `estimator` identifique sus inputs `route_id`, `service_id`, `shape_id`.
   - trip_times: se utiliza para que `estimator` itere sobre cada viaje de la base de datos GTFS e identifique su input `start_time` (*trip_times es una tabla auxiliar de la base de datos GTFS*).
   - route_stops: se utiliza para obtener la secuencia de paradas que utilizará `estimator`(*route_stops es una tabla auxiliar de la base de datos GTFS*). 
2. La base de datos GTFS utilizada fue la correspondiente a los datos del bus interno UCR.
3. La tabla `stops_measurement` es una tabla auxiliar de la base de datos GTFS.
4. Las funciones polinomiales de mejor ajuste para cada parada están guardadas en el diccionario `polynomials`, el cual tiene como llave o 'key' una combinación específica de 'route_id', 'service_id', 'shape_id' y'stop_id'. Por ejemplo ('bUCR_L1', 'entresemana', 'desde_artes_con_milla', 'UCR_0_03') es la llave del ajuste polinomial de esa combinación específica.
5. Tambien se puede llamar a la función `estimator` de forma que retorne los tiempos estimados de un viaje nuevo. Para ello se le debe indicar una combinación de `route_id`, `service_id`, `shape_id` que exista en la base de datos GTFS, e indicar una hora de inicio de viaje (`start_time`) en formato HH:MM.
