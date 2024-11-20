import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString
import geopandas as gpd


def estimate_stop_times(
    method, trip_id, route, shape, route_stops, trip_times, trip_durations, stops
) -> pd.DataFrame:
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
        A GeoDataFrame containing the data of the shape of route.
    route_stops : DataFrame
        A DataFrame containing the sequence of stops for the given combination of route and shape.
    trip_times : DataFrame
        The stop_id and departure time (time object) for the given trip_id, shape_id and service_id for a given time range (start_time, end_time) for trip_time.
    trip_durations : DataFrame, optional
        The trip_id and trip duration (timedelta object) for the given trip_id, shape_id and service_id for a given time range (start_time, end_time) for trip_time. Mandatory for method A.
    stops : DataFrame, optional
        A DataFrame containing the stop data for the list of stops. Mandatory for method A.

    Returns
    -------
    DataFrame
        A DataFrame containing the estimated stop times for the given trip_id, with the fields:
        trip_id, arrival_time, departure_time, stop_id, stop_sequence, timepoint, shape_dist_traveled
    """
    # Data validation here

    if method == "A":
        return _estimate_method_A(
            trip_id, route, shape, route_stops, trip_times, trip_durations, stops
        )
    elif method == "B":
        return _estimate_method_B(trip_id, route, shape, route_stops, trip_times)
    else:
        raise ValueError("Invalid method. Use 'A' or 'B'.")


def _estimate_method_A(
    trip_id, route, shape, route_stops, trip_times, trip_durations, stops
):
    """Implementation of estimation method A."""

    # Data validation here
    if trip_id not in trip_times["trip_id"].values:
        raise ValueError("El trip_id proporcionado no existe en los tiempos de viaje.")

    # Filtrar datos relevantes para el trip_id
    selected_route = route[route["trip_id"] == trip_id]
    selected_shape = shape[shape["shape_id"] == selected_route["shape_id"].iloc[0]]
    selected_stops = route_stops[route_stops["trip_id"] == trip_id]

    # Calcular distancias entre las paradas usando la forma geográfica
    distances = []
    for i in range(len(selected_stops) - 1):
        stop_1 = stops[stops["stop_id"] == selected_stops.iloc[i]["stop_id"]].iloc[0]
        stop_2 = stops[stops["stop_id"] == selected_stops.iloc[i + 1]["stop_id"]].iloc[
            0
        ]
        point_1 = Point(stop_1["longitude"], stop_1["latitude"])
        point_2 = Point(stop_2["longitude"], stop_2["latitude"])

        # Usar distancia geodésica o euclidiana según sea necesario
        line = LineString([point_1, point_2])
        distances.append(line.length)

    # Calcular tiempos estimados usando distancias y velocidad promedio
    average_speed_kmph = 40  # Suponiendo una velocidad promedio
    estimated_times = [
        (dist / average_speed_kmph) * 60 for dist in distances
    ]  # Tiempo en minutos

    # Crear un DataFrame con los tiempos estimados
    result = pd.DataFrame(
        {
            "stop_id": selected_stops["stop_id"].iloc[
                :-1
            ],  # Todas las paradas excepto la última
            "estimated_time_minutes": estimated_times,
        }
    )

    return result

    """     
    # Convert the shape data in shape["geometry"] to a Shapely LineString
    shape_line = shape["geometry"].iloc[0]

    stop_times = pd.DataFrame(
        columns=[
            "trip_id",
            "arrival_time",
            "departure_time",
            "stop_id",
            "stop_sequence",
            "timepoint",
            "shape_dist_traveled",
        ]
    )

    return stop_times 
    """


def _estimate_method_B(
    stops_measurement, route_stops, trip_times, trips
) -> pd.DataFrame:
    """Generate the stop times for a GTFS feed in the Databús platform.

    Parameters
    ----------

    route_id : str
        The route_id for which to estimate stop times.
    service_id : str
        The service_id for which to estimate stop times.

    """

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
        start_time = row["trip_time"]

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


# -----------
# LEGACY CODE
# -----------


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
    stops_measurement = stops_measurement.groupby(["trip_id", "date"]).apply(get_delay)

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


# El problema de estimación de modelos de tiempos de llegada (polinomios) se resuelve en otra parte, posiblemente en Django como una tarea periódica, aunque tal vez este paquete ofrezca también una función para hacerlo


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
