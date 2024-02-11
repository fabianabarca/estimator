import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def estimate(method, trip_id, route, shape, route_stops, stops, trip_times):
    """Validate incoming data and call the appropriate estimation method.

    Parameters
    ----------
    method : str
        The estimation method to use. Either "A" or "B".
    trip_id : str
        The trip_id for which to estimate stop times.
    route : DataFrame
        A DataFrame containing the route data.
    shape : GeoDataFrame
        A GeoDataFrame containing the shape data.
    route_stops : DataFrame
        A DataFrame containing the sequence of stops for the given combination of route and shape.
    stops : DataFrame
        A DataFrame containing the stop data for the list of stops.
    trip_times : DataFrame

    Returns
    -------
    DataFrame
        A DataFrame containing the estimated stop times for the given trip_id.
    """
    # Data validation here

    if method == "A":
        return estimate_method_A(trip_id, route, shape, route_stops, stops, trip_times)
    elif method == "B":
        return estimate_method_B(trip_id, route, shape, route_stops, stops, trip_times)
    else:
        raise ValueError("Invalid method. Use 'A' or 'B'.")


def get_delay(group):
    # Convierte la columna 'arrival_time' en objetos de tiempo
    group["arrival_time"] = pd.to_datetime(group["arrival_time"], format="%H:%M:%S")

    # Índice del primer 'stop_id' donde 'timepoint' es igual a 1
    primer_timepoint_idx = group[group["timepoint"] == 1].index[0]

    # Calcula el retraso restando los tiempos de 'arrival_time'
    group["delay"] = (
        group["arrival_time"] - group.loc[primer_timepoint_idx, "arrival_time"]
    ).dt.total_seconds()

    return group


def get_sequence_of_stops(route_id, shape_id, route_stops):
    stops_sequence = route_stops[
        (route_stops["route_id"] == route_id) & (route_stops["shape_id"] == shape_id)
    ]

    # Encontrar todas las paradas para la combinación dada
    sequence_of_stops = stops_sequence["stop_id"].unique()

    return sequence_of_stops


def get_polynomials(stops_measurement):
    # Aplicar la función a cada grupo (trip_id, date)
    stops_measurement = stops_measurement.groupby(["trip_id", "date"]).apply(
        get_delay
    )

    # Reiniciar el índice del DataFrame resultante
    stops_measurement.reset_index(drop=True, inplace=True)

    stops_measurement["arrival_time"] = stops_measurement["arrival_time"].dt.strftime(
        "%H:%M:%S"
    )

    # Crear columna 'trip_departure_time'
    stops_measurement["trip_departure_time"] = stops_measurement.groupby("trip_id")[
        "arrival_time"
    ].transform("first")

    combinations = stops_measurement[
        ["route_id", "service_id", "shape_id", "stop_id"]
    ].drop_duplicates()

    # Crear un diccionario para almacenar los polinomios
    polynomials = {}

    for i, combination in combinations.iterrows():
        subset = stops_measurement[
            (stops_measurement["route_id"] == combination["route_id"])
            & (stops_measurement["service_id"] == combination["service_id"])
            & (stops_measurement["shape_id"] == combination["shape_id"])
            & (stops_measurement["stop_id"] == combination["stop_id"])
        ]

        if not subset.empty:
            x_values = (
                pd.to_datetime(subset["trip_departure_time"], format="%H:%M:%S").dt.hour
                * 3600
                + pd.to_datetime(
                    subset["trip_departure_time"], format="%H:%M:%S"
                ).dt.minute
                * 60
                + pd.to_datetime(
                    subset["trip_departure_time"], format="%H:%M:%S"
                ).dt.second
            )

            degree = 4  # Grado del polinomio, puede ajustarse según las necesidades
            coefficients = np.polyfit(x_values, subset["delay"], degree)
            polynomial = np.poly1d(coefficients)
            polynomials[tuple(combination)] = polynomial

    return polynomials


def estimate(route_id, service_id, shape_id, start_time, polynomials, route_stops):
    # Obtener la secuencia de paradas para la combinación dada
    sequence_of_stops = get_sequence_of_stops(route_id, shape_id, route_stops)

    estimated_arrival_times = {}
    departure_time = pd.to_datetime(start_time, format="%H:%M")

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
            estimated_arrival_times[stop_id] = estimated_arrival.strftime("%H:%M:%S")
        else:
            # No hay datos polinomiales para esta parada
            estimated_arrival_times[stop_id] = "No se puede estimar"

    return sequence_of_stops, estimated_arrival_times


def generate(stops_measurement, route_stops, trip_times, trips):
    # Crear un DataFrame vacío para acumular los resultados
    stop_times_df = pd.DataFrame(
        columns=[
            "trip_id",
            "arrival_time",
            "departure_time",
            "stop_id",
            "stop_sequence",
            "timepoint",
            "shape_dist_traveled",
            "stop_headsign",
            "pickup_type",
            "drop_off_type",
            "continuous_pickup",
            "continuous_drop_off",
        ]
    )

    # Iterar sobre las filas del DataFrame trip_times
    for index, row in trip_times.iterrows():
        trip_id = row["trip_id"]
        start_time = row["trip_departure_time"]

        # Reemplazar stops_measurement por trips
        route_id = trips.loc[trips["trip_id"] == trip_id, "route_id"].values[0]
        service_id = trips.loc[trips["trip_id"] == trip_id, "service_id"].values[0]
        shape_id = trips.loc[trips["trip_id"] == trip_id, "shape_id"].values[0]

        polynomials = get_polynomials(stops_measurement)

        # Llamada a la función estimator
        sequence_of_stops, estimated_arrival_times = estimate(
            route_id, service_id, shape_id, start_time, polynomials, route_stops
        )

        timepoint_values = [1 if i == 0 else 0 for i in range(len(sequence_of_stops))]

        # Construcción de stop_times_iteration para esta iteración
        stop_times_iteration = pd.DataFrame(
            {
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
            }
        )

        # Concatenar los resultados de esta iteración al DataFrame principal
        stop_times_df = pd.concat(
            [stop_times_df, stop_times_iteration], ignore_index=True
        )
    return stop_times_df
