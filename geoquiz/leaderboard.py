"""Keep the leaderboard with the best scores of the players."""

import os

import pandas as pd

LEADERBOARD_PATH = os.path.join("data", "leaderboard.csv")  # "data/leaderboard.csv"

LEADERBOARD_COLUMNS = ["name", "score", "date"]

# The longest name accepted, so that a long name does not break the table
MAX_NAME_LENGTH = 20

# How many scores are shown in the leaderboard
TOP_SCORES = 10


def clean_name(name):
    """
    Check the name of a player and remove the spaces around it.

    Parameters
    ----------
    name : str
        The name written by the player, e.g. ``"  Simone "``.

    Returns
    -------
    str
        The name without the spaces around it, e.g. ``"Simone"``.

    Raises
    ------
    ValueError
        If the name is empty or longer than ``MAX_NAME_LENGTH``.
    """
    name = name.strip()
    if len(name) == 0:
        raise ValueError("The name cannot be empty")
    if len(name) > MAX_NAME_LENGTH:
        raise ValueError(f"The name can have at most {MAX_NAME_LENGTH} characters")
    return name


def load_leaderboard(path=LEADERBOARD_PATH):
    """
    Load the leaderboard from a CSV file.

    Parameters
    ----------
    path : str, optional
        Path of the CSV file. Defaults to ``LEADERBOARD_PATH``.

    Returns
    -------
    pandas.DataFrame
        One row for each score, with the columns of ``LEADERBOARD_COLUMNS``.
        The table is empty if the file does not exist yet.
    """
    if not os.path.exists(path):
        return pd.DataFrame(columns=LEADERBOARD_COLUMNS)
    return pd.read_csv(path)


def save_leaderboard(leaderboard, path=LEADERBOARD_PATH):
    """
    Save the leaderboard to a CSV file.

    Parameters
    ----------
    leaderboard : pandas.DataFrame
        The leaderboard, as returned by ``load_leaderboard``.
    path : str, optional
        Path of the CSV file. Defaults to ``LEADERBOARD_PATH``.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    leaderboard.to_csv(path, index=False)


def add_score(leaderboard, name, score):
    """
    Add the score of a player to the leaderboard.

    Parameters
    ----------
    leaderboard : pandas.DataFrame
        The leaderboard, as returned by ``load_leaderboard``.
    name : str
        The name of the player, checked with ``clean_name``.
    score : int
        The points of the player.

    Returns
    -------
    pandas.DataFrame
        The leaderboard with a new row, dated today.
    """
    today = pd.Timestamp.today().strftime("%Y-%m-%d")  # e.g. "2026-11-12"
    new_row = pd.DataFrame([{"name": clean_name(name), "score": score, "date": today}])
    # The first score is the new leaderboard, since the old one is empty
    if len(leaderboard) == 0:
        return new_row
    return pd.concat([leaderboard, new_row], ignore_index=True)


def get_top_scores(leaderboard, n=TOP_SCORES):
    """
    Get the best scores of the leaderboard.

    Parameters
    ----------
    leaderboard : pandas.DataFrame
        The leaderboard, as returned by ``load_leaderboard``.
    n : int, optional
        How many scores to get. Defaults to ``TOP_SCORES``.

    Returns
    -------
    pandas.DataFrame
        The ``n`` best scores, from the highest, numbered from 1. With the
        same score, the player who got it first comes first.
    """
    # A stable sort keeps the order of the rows with the same score
    top = leaderboard.sort_values("score", ascending=False, kind="stable").head(n)
    top.index = range(1, len(top) + 1)
    return top
