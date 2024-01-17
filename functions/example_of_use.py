import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

stops_measurement= pd.read_csv('stop_times_measurement.csv')
route_stops= pd.read_csv('route_stops.csv')
trip_times= pd.read_csv('trip_times.csv')
trips= pd.read_csv('trips.csv')

import estimator as est

resultado_stop_times = est.generate_stop_times_df()
# Mostrar el contenido del DataFrame
resultado_stop_times.head(15)
