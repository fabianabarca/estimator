import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

stops_measurement= pd.read_csv('stop_times_measurement.csv')
route_stops= pd.read_csv('route_stops.csv')
trip_times= pd.read_csv('trip_times.csv')
trips= pd.read_csv('trips.csv')

import estimator as est

# Aplicar la función a cada grupo (trip_id, date)
stops_measurement = stops_measurement.groupby(['trip_id', 'date']).apply(est.calcular_delay)

# Reiniciar el índice del DataFrame resultante
stops_measurement.reset_index(drop=True, inplace=True)

stops_measurement['arrival_time'] = stops_measurement['arrival_time'].dt.strftime('%H:%M:%S')

# Crear columna 'trip_departure_time'
stops_measurement['trip_departure_time'] = stops_measurement.groupby('trip_id')['arrival_time'].transform('first')

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


resultado_stop_times = est.generate_stop_times_df()
# Mostrar el contenido del DataFrame
resultado_stop_times.head(15)
