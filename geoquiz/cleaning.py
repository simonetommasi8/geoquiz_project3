"""Clean the country data and build the table used by the quiz."""

import os

import pandas as pd

from geoquiz.data import (
    COUNTRIES_PATH,
    INDICATORS,
    download_countries,
    fetch_indicator,
    load_countries,
)


def get_currency_names(currencies):
    """
    Get the names of the currencies of a country.

    Parameters
    ----------
    currencies : dict
        Mapping ``currency code -> {"name": ..., "symbol": ...}``.

    Returns
    -------
    list of str
        The names of the currencies, e.g. ``["Euro"]``.
    """
    names = []
    for code in currencies:
        names.append(currencies[code]["name"])
    return names


def get_language_names(languages):
    """
    Get the names of the languages of a country.

    Parameters
    ----------
    languages : dict
        Mapping ``language code -> language name``.

    Returns
    -------
    list of str
        The names of the languages, e.g. ``["Italian"]``.
    """
    names = []
    for code in languages:
        names.append(languages[code])
    return names


def build_basic_table(countries):
    """
    Keep the UN member states and turn their data into simple columns.

    Parameters
    ----------
    countries : list of dict
        The countries, as returned by ``load_countries``.

    Returns
    -------
    pandas.DataFrame
        One row for each UN member state.
    """
    df = pd.DataFrame(countries)
    un_countries = df[df["unMember"]]

    table = pd.DataFrame()
    table["cca3"] = un_countries["cca3"]
    table["name"] = un_countries["name"].apply(lambda name: name["common"])
    table["capitals"] = un_countries["capital"]
    table["flag"] = un_countries["flag"]
    table["region"] = un_countries["region"]
    table["subregion"] = un_countries["subregion"]
    table["lat"] = un_countries["latlng"].apply(lambda latlng: latlng[0])
    table["lng"] = un_countries["latlng"].apply(lambda latlng: latlng[1])
    table["area"] = un_countries["area"]
    table["borders"] = un_countries["borders"]
    table["currencies"] = un_countries["currencies"].apply(get_currency_names)
    table["languages"] = un_countries["languages"].apply(get_language_names)
    return table


def add_world_bank_data(table, population, gdp):
    """
    Add the population and the GDP, and drop the countries without them.

    Parameters
    ----------
    table : pandas.DataFrame
        The countries, with a ``cca3`` column.
    population : pandas.DataFrame
        The population, as returned by ``fetch_indicator``.
    gdp : pandas.DataFrame
        The GDP, as returned by ``fetch_indicator``.

    Returns
    -------
    pandas.DataFrame
        The countries with the ``population`` and ``gdp`` columns.

    Raises
    ------
    ValueError
        If the merge duplicates some countries.
    """
    population_clean = population[["cca3", "value"]].rename(
        columns={"value": "population"}
    )
    gdp_clean = gdp[["cca3", "value"]].rename(columns={"value": "gdp"})

    rows_before = len(table)
    table = table.merge(population_clean, on="cca3", how="left")
    table = table.merge(gdp_clean, on="cca3", how="left")
    # A country code repeated in the World Bank data would duplicate the country
    if len(table) != rows_before:
        raise ValueError("The merge with the World Bank data duplicated some rows")

    # Countries without population or GDP (Vatican City, North Korea) are excluded
    return table.dropna(subset=["population", "gdp"])


def add_computed_columns(table):
    """
    Add the population density and the GDP per capita.

    Parameters
    ----------
    table : pandas.DataFrame
        The countries, with the ``area``, ``population`` and ``gdp`` columns.

    Returns
    -------
    pandas.DataFrame
        The countries with the ``density`` and ``gdp_per_capita`` columns.

    Raises
    ------
    ValueError
        If an area or a population is not positive.
    """
    # Both columns are used as divisors
    if not (table["area"] > 0).all():
        raise ValueError("Some countries have an area that is not positive")
    if not (table["population"] > 0).all():
        raise ValueError("Some countries have a population that is not positive")

    table["density"] = table["population"] / table["area"]
    table["gdp_per_capita"] = table["gdp"] / table["population"]
    return table


def build_countries_table(path=COUNTRIES_PATH):
    """
    Build the table of the countries used by the quiz.

    The countries file is downloaded if it is missing, and the population
    and the GDP are fetched from the World Bank API.

    Parameters
    ----------
    path : str, optional
        Path of the countries file. Defaults to ``COUNTRIES_PATH``.

    Returns
    -------
    pandas.DataFrame
        One row for each country, indexed by its ``cca3`` code.

    Raises
    ------
    ValueError
        If the country codes are not unique.
    """
    if not os.path.exists(path):
        download_countries(path=path)

    table = build_basic_table(load_countries(path))
    population = fetch_indicator(INDICATORS["population"])
    gdp = fetch_indicator(INDICATORS["gdp"])
    table = add_world_bank_data(table, population, gdp)
    table = add_computed_columns(table)

    table = table.set_index("cca3")
    if not table.index.is_unique:
        raise ValueError("The country codes (cca3) are not unique")
    return table
