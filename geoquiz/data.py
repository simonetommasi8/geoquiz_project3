"""Download and load the data about the countries of the world."""

import json
import os

import pandas as pd
import requests

# The countries dataset, from the GitHub repository of mledoze
COUNTRIES_URL = (
    "https://raw.githubusercontent.com/mledoze/countries/master/countries.json"
)
COUNTRIES_PATH = os.path.join("data", "countries.json")  # path: "data/countries.json"

WORLD_BANK_URL = "https://api.worldbank.org/v2/country/all/indicator/"

INDICATORS = {
    "population": "SP.POP.TOTL",
    "gdp": "NY.GDP.MKTP.CD",
}


def download_countries(url=COUNTRIES_URL, path=COUNTRIES_PATH):
    """
    Download the countries dataset and save it to a JSON file.

    Parameters
    ----------
    url : str, optional
        URL of the dataset. Defaults to ``COUNTRIES_URL``.
    path : str, optional
        Path of the file to write. Defaults to ``COUNTRIES_PATH``.

    Raises
    ------
    requests.HTTPError
        If the server answers with an error.
    """
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write(response.text)


def load_countries(path=COUNTRIES_PATH):
    """
    Load the countries dataset from a JSON file.

    Parameters
    ----------
    path : str, optional
        Path of the JSON file. Defaults to ``COUNTRIES_PATH``.

    Returns
    -------
    list of dict
        One dictionary for each country.
    """
    # Open the file in UTF-8, to read all the special characters
    with open(path, encoding="utf-8") as f:
        return json.load(f)  # convert the JSON text into Python lists and dicts


def fetch_indicator(indicator):
    """
    Download the most recent value of a World Bank indicator for every country.

    Parameters
    ----------
    indicator : str
        Code of the indicator, e.g. ``"SP.POP.TOTL"`` for the population.

    Returns
    -------
    pandas.DataFrame
        One row per country, with columns ``cca3``, ``year`` and ``value``.

    Raises
    ------
    requests.HTTPError
        If the server answers with an error.
    ValueError
        If the API does not return any data for the indicator.
    """
    # Build the URL of the request using the API rules
    url = WORLD_BANK_URL + indicator + "?format=json&mrnev=1&per_page=500"

    # Send the request, and stop if the server answers with an error
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    # The answer is a list with two parts: [information, data]
    # If the indicator code is wrong, the server still answers "OK" (200),
    # but the list only contains the error message, without the data.
    answer = response.json()
    if len(answer) < 2 or answer[1] is None:
        raise ValueError(f"No data for the indicator {indicator}")
    records = answer[1]  # the list of dictionaries, one for each country

    # For each country, keep only its code, the year and the value
    rows = []
    for record in records:
        country_code = record["countryiso3code"]
        year = int(record["date"])
        value = record["value"]
        rows.append({"cca3": country_code, "year": year, "value": value})

    return pd.DataFrame(rows)
