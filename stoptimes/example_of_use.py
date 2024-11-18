import stoptimes as est
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

# Cargar los datos necesarios
stops_measurement = pd.read_csv('stop_times_measurement.csv')
route_stops = pd.read_csv('route_stops.csv')
trip_times = pd.read_csv('trip_times.csv')
trips = pd.read_csv('trips.csv')


resultado_stop_times = est.estimate_stop_times(
    "B", stops_measurement, route_stops, trip_times, trips)
# Mostrar el contenido del DataFrame
print(resultado_stop_times.head(15))
