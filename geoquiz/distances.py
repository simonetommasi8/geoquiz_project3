"""Compute the distances between the countries."""

import numpy as np
import pandas as pd

EARTH_RADIUS_KM = 6371


def haversine_km(lat1, lng1, lat2, lng2):
    """
    Compute the great-circle distance between points on the Earth.

    The arguments can be numbers or NumPy arrays: with arrays, the distances
    are computed element by element, all at once.

    Parameters
    ----------
    lat1, lng1 : float or numpy.ndarray
        Latitude and longitude of the first points, in degrees.
    lat2, lng2 : float or numpy.ndarray
        Latitude and longitude of the second points, in degrees.

    Returns
    -------
    float or numpy.ndarray
        The distances, in km.
    """
    # Convert each value separately: some can be numbers and others arrays
    lat1 = np.radians(lat1)
    lng1 = np.radians(lng1)
    lat2 = np.radians(lat2)
    lng2 = np.radians(lng2)
    a = (
        np.sin((lat2 - lat1) / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin((lng2 - lng1) / 2) ** 2
    )
    a = np.clip(a, 0, 1)  # rounding errors could push a slightly above 1
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))


def distances_from(countries, code):
    """
    Compute the distance of every country from a given country.

    The distance between two countries is the distance between their
    central points (``lat`` and ``lng``). Neighbouring countries are at
    distance 0, since they touch each other.

    Parameters
    ----------
    countries : pandas.DataFrame
        The table of the countries, indexed by ``cca3``.
    code : str
        The ``cca3`` code of the country.

    Returns
    -------
    pandas.Series
        The distances in km, indexed by ``cca3`` (0 for the country itself
        and for its neighbours).
    """
    country = countries.loc[code]
    distances = haversine_km(
        country["lat"],
        country["lng"],
        countries["lat"].to_numpy(),
        countries["lng"].to_numpy(),
    )
    distances = pd.Series(distances, index=countries.index)

    # Neighbouring countries touch each other: their distance is 0, even if
    # their central points are far apart (e.g. Italy and France)
    for neighbour in country["borders"]:
        # Some neighbours are not in the table (e.g. Vatican City)
        if neighbour in distances.index:
            distances.loc[neighbour] = 0
    return distances
