"""Download and load the data about the countries of the world."""

import json
import os

import requests

COUNTRIES_URL = (
    "https://raw.githubusercontent.com/mledoze/countries/master/countries.json"
)
COUNTRIES_PATH = os.path.join("data", "countries.json")


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
    with open(path, encoding="utf-8") as f:
        return json.load(f)