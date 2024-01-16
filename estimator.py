import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def calcular_delay(group):
    # Convierte la columna 'arrival_time' en objetos de tiempo
    group['arrival_time'] = pd.to_datetime(group['arrival_time'], format='%H:%M:%S')

    # Índice del primer 'stop_id' donde 'timepoint' es igual a 1
    primer_timepoint_idx = group[group['timepoint'] == 1].index[0]

    # Calcula el retraso restando los tiempos de 'arrival_time'
    group['delay'] = (group['arrival_time'] - 
    group.loc[primer_timepoint_idx, 'arrival_time']).dt.total_seconds()

    return group


def get_sequence_of_stops(route_id, shape_id, route_stops):
    stops_sequence = route_stops[
        (route_stops['route_id'] == route_id) &
        (route_stops['shape_id'] == shape_id)
    ]

    # Encontrar todas las paradas para la combinación dada
    sequence_of_stops = stops_sequence['stop_id'].unique()
    
    return sequence_of_stops

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


