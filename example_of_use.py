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

polynomials = est.calcular_polinomios(stops_measurement)

resultado_stop_times = est.generate_stop_times_df()
# Mostrar el contenido del DataFrame
resultado_stop_times.head(15)
