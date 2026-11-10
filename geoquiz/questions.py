"""Generate the questions of the quiz."""

import random

from geoquiz.distances import distances_from

N_WRONG_OPTIONS = 3

# For each difficulty, the positions of the candidates for the wrong options
# in the ranking from the nearest to the farthest: the nearer, the harder
RANK_RANGES = {
    "easy": (100, None),  # beyond the 100th nearest country
    "medium": (10, 40),  # from the 11th to the 40th
    "hard": (0, 10),  # the 10 nearest countries
}

# For each difficulty, the positions of the country of the question in the
# ranking by GDP: the countries with the largest economies are the best known
GDP_RANK_RANGES = {
    "easy": (0, 50),  # the 50 largest economies
    "medium": (50, 120),  # from the 51st to the 120th
    "hard": (120, None),  # the other countries
}

DIFFICULTIES = list(RANK_RANGES)

FLAG_URL = "https://raw.githubusercontent.com/mledoze/countries/master/data/"


def check_difficulty(difficulty):
    """
    Check that a difficulty is valid.

    Parameters
    ----------
    difficulty : str
        The difficulty to check.

    Raises
    ------
    ValueError
        If the difficulty is not one of ``DIFFICULTIES``.
    """
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"Unknown difficulty: {difficulty}")


def get_country_pool(countries, difficulty):
    """
    Get the countries that can be chosen for a question of a given difficulty.

    The harder the question, the less known the countries: they are ranked
    by GDP, since the largest economies are the best known.

    Parameters
    ----------
    countries : pandas.DataFrame
        The table of the countries, indexed by ``cca3``.
    difficulty : str
        One of ``DIFFICULTIES``.

    Returns
    -------
    list of str
        The ``cca3`` codes of the countries.

    Raises
    ------
    ValueError
        If the difficulty is not valid.
    """
    check_difficulty(difficulty)
    by_gdp = countries.sort_values("gdp", ascending=False).index.tolist()
    start, end = GDP_RANK_RANGES[difficulty]
    return by_gdp[start:end]


def choose_country(countries, difficulty, code=None):
    """
    Choose the country of a question.

    Parameters
    ----------
    countries : pandas.DataFrame
        The table of the countries, indexed by ``cca3``.
    difficulty : str
        One of ``DIFFICULTIES``.
    code : str, optional
        The ``cca3`` code of the country. Defaults to a random country,
        chosen with ``get_country_pool``.

    Returns
    -------
    str
        The ``cca3`` code of the country.
    """
    check_difficulty(difficulty)
    if code is not None:
        return code
    return random.choice(get_country_pool(countries, difficulty))


def get_candidates(countries, code, difficulty):
    """
    Get the countries that can be used for the wrong options of a question.

    The harder the question, the nearer the candidates are to the country.

    Parameters
    ----------
    countries : pandas.DataFrame
        The table of the countries, indexed by ``cca3``.
    code : str
        The ``cca3`` code of the country of the question.
    difficulty : str
        One of ``DIFFICULTIES``.

    Returns
    -------
    list of str
        The ``cca3`` codes of the candidate countries.

    Raises
    ------
    ValueError
        If the difficulty is not valid.
    """
    check_difficulty(difficulty)

    # The country of the question must not be among its own wrong options
    distances = distances_from(countries, code).drop(index=code)
    nearest_first = distances.sort_values().index.tolist()
    start, end = RANK_RANGES[difficulty]
    return nearest_first[start:end]


def make_options(countries, code, difficulty, answer, column):
    """
    Build the four options of a question: the right answer and three wrong ones.

    The wrong options are the values of ``column`` for three countries
    chosen with ``get_candidates``, so the harder the question, the nearer
    these countries are to the country of the question.

    Parameters
    ----------
    countries : pandas.DataFrame
        The table of the countries, indexed by ``cca3``.
    code : str
        The ``cca3`` code of the country of the question.
    difficulty : str
        One of ``DIFFICULTIES``.
    answer : str
        The right answer.
    column : str
        The column of ``countries`` with the values of the options.

    Returns
    -------
    list of str
        The four options, shuffled.
    """
    candidates = get_candidates(countries, code, difficulty)
    wrong_codes = random.sample(candidates, N_WRONG_OPTIONS)

    options = [answer]
    for wrong_code in wrong_codes:
        value = countries.loc[wrong_code, column]
        # Some columns contain lists (e.g. capitals): take the first value
        if isinstance(value, list):
            value = value[0]
        options.append(value)
    random.shuffle(options)
    return options


def make_capital_question(countries, difficulty="easy", code=None):
    """
    Generate a question about the capital of a country.

    Parameters
    ----------
    countries : pandas.DataFrame
        The table of the countries, indexed by ``cca3``.
    difficulty : str, optional
        One of ``DIFFICULTIES``. Defaults to ``"easy"``.
    code : str, optional
        The ``cca3`` code of the country. Defaults to a random country,
        chosen according to the difficulty.

    Returns
    -------
    dict
        The question, with the keys ``type``, ``difficulty``, ``text``,
        ``options`` and ``answer``.
    """
    code = choose_country(countries, difficulty, code)
    country = countries.loc[code]
    # Some countries have more capitals (e.g. South Africa): any of them is right
    answer = random.choice(country["capitals"])

    return {
        "type": "capital",
        "difficulty": difficulty,
        "text": f"What is the capital of {country['name']}?",
        "options": make_options(countries, code, difficulty, answer, "capitals"),
        "answer": answer,
    }


def make_flag_question(countries, difficulty="easy", code=None):
    """
    Generate a question about the country of a flag.

    Parameters
    ----------
    countries : pandas.DataFrame
        The table of the countries, indexed by ``cca3``.
    difficulty : str, optional
        One of ``DIFFICULTIES``. Defaults to ``"easy"``.
    code : str, optional
        The ``cca3`` code of the country. Defaults to a random country,
        chosen according to the difficulty.

    Returns
    -------
    dict
        The question, with the keys ``type``, ``difficulty``, ``text``,
        ``image``, ``options`` and ``answer``. ``image`` is the URL of the
        flag, since flag emojis are not shown on every operating system.
    """
    code = choose_country(countries, difficulty, code)
    answer = countries.loc[code, "name"]

    return {
        "type": "flag",
        "difficulty": difficulty,
        "text": "Which country does this flag belong to?",
        "image": FLAG_URL + code.lower() + ".svg",
        "options": make_options(countries, code, difficulty, answer, "name"),
        "answer": answer,
    }


QUESTION_MAKERS = [make_capital_question, make_flag_question]


def make_quiz(countries, difficulty, n_questions):
    """
    Generate the questions of a quiz, each about a different country.

    Parameters
    ----------
    countries : pandas.DataFrame
        The table of the countries, indexed by ``cca3``.
    difficulty : str
        One of ``DIFFICULTIES``.
    n_questions : int
        The number of questions.

    Returns
    -------
    list of dict
        The questions, of random types.

    Raises
    ------
    ValueError
        If there are fewer countries than questions for the difficulty.
    """
    pool = get_country_pool(countries, difficulty)
    if n_questions > len(pool):
        raise ValueError(
            f"At most {len(pool)} questions can be asked at the {difficulty} level"
        )

    # Different countries, so that no question is repeated
    codes = random.sample(pool, n_questions)
    questions = []
    for code in codes:
        make_question = random.choice(QUESTION_MAKERS)
        questions.append(make_question(countries, difficulty, code=code))
    return questions


def next_difficulty(difficulty, was_right):
    """
    Choose the difficulty of the next question of an adaptive quiz.

    After a right answer the next question is one level harder, after a
    wrong answer one level easier, within the levels of ``DIFFICULTIES``.

    Parameters
    ----------
    difficulty : str
        The difficulty of the last question, one of ``DIFFICULTIES``.
    was_right : bool
        Whether the last question was answered correctly.

    Returns
    -------
    str
        The difficulty of the next question.
    """
    check_difficulty(difficulty)
    level = DIFFICULTIES.index(difficulty)
    if was_right:
        level = min(level + 1, len(DIFFICULTIES) - 1)
    else:
        level = max(level - 1, 0)
    return DIFFICULTIES[level]


def make_next_question(countries, difficulty, used_codes):
    """
    Generate a question about a country not asked yet in the quiz.

    Parameters
    ----------
    countries : pandas.DataFrame
        The table of the countries, indexed by ``cca3``.
    difficulty : str
        One of ``DIFFICULTIES``.
    used_codes : list of str
        The ``cca3`` codes of the countries already asked in the quiz.

    Returns
    -------
    dict
        The question, of a random type, with also the key ``code``.
    """
    available = []
    for code in get_country_pool(countries, difficulty):
        if code not in used_codes:
            available.append(code)

    code = random.choice(available)
    make_question = random.choice(QUESTION_MAKERS)
    question = make_question(countries, difficulty, code=code)
    question["code"] = code
    return question
