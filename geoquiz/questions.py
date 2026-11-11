"""Generate the questions of the quiz."""

import random

from geoquiz.distances import distances_from
from geoquiz.names import reveals_country

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

# Pairs of flags that look almost the same: they are never in the same question
LOOK_ALIKE_FLAGS = {
    "IDN": ["MCO"],  # Indonesia and Monaco
    "MCO": ["IDN"],
    "TCD": ["ROU"],  # Chad and Romania
    "ROU": ["TCD"],
    "NLD": ["LUX"],  # Netherlands and Luxembourg
    "LUX": ["NLD"],
}


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


def reveals_all(countries, code, column):
    """
    Tell whether all the values of a country in a column reveal the country.

    Parameters
    ----------
    countries : pandas.DataFrame
        The table of the countries, indexed by ``cca3``.
    code : str
        The ``cca3`` code of the country.
    column : str
        The column with the lists of values (e.g. ``"languages"``).

    Returns
    -------
    bool
        True if every value reveals the country (e.g. Albania and Albanian).
    """
    country = countries.loc[code]
    for value in country[column]:
        if not reveals_country(value, country["name"], country["demonym"]):
            return False
    return True


def get_country_pool(
    countries, difficulty, column=None, check_reveal=False, easy_only=False
):
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
    column : str, optional
        If given, only the countries with at least one value in this column
        are kept (e.g. Micronesia has no currency).
    check_reveal : bool, optional
        If True, the countries whose values in ``column`` all reveal the
        country (e.g. Albania and Albanian) are easy questions: they are
        added to the easy pool and removed from the others. Defaults to False.
    easy_only : bool, optional
        If True, the type of question is easy for every country (e.g. the
        region): all the countries are in the easy pool, whatever the GDP,
        and the other pools are empty. Defaults to False.

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
    in_range = by_gdp[start:end]

    pool = []
    for code in by_gdp:
        if column is not None and len(countries.loc[code, column]) == 0:
            continue
        if easy_only or (check_reveal and reveals_all(countries, code, column)):
            # A question that is easy by nature is easy, whatever the GDP
            if difficulty == "easy":
                pool.append(code)
        elif code in in_range:
            pool.append(code)
    return pool


def choose_country(
    countries, difficulty, code=None, column=None, check_reveal=False, easy_only=False
):
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
    column, check_reveal, easy_only : optional
        Passed to ``get_country_pool``.

    Returns
    -------
    str
        The ``cca3`` code of the country.
    """
    check_difficulty(difficulty)
    if code is not None:
        return code
    return random.choice(
        get_country_pool(countries, difficulty, column, check_reveal, easy_only)
    )


def rank_by_distance(countries, code):
    """
    Rank the other countries from the nearest to the farthest.

    Parameters
    ----------
    countries : pandas.DataFrame
        The table of the countries, indexed by ``cca3``.
    code : str
        The ``cca3`` code of the country.

    Returns
    -------
    list of str
        The ``cca3`` codes of the other countries, from the nearest.
    """
    # The country itself must not be among its own wrong options
    distances = distances_from(countries, code).drop(index=code)
    return distances.sort_values().index.tolist()


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
    start, end = RANK_RANGES[difficulty]
    return rank_by_distance(countries, code)[start:end]


def shares_word(value, others):
    """
    Tell whether a value has a word in common with any of the other values.

    Parameters
    ----------
    value : str
        The value to check, e.g. ``"German"``.
    others : list of str
        The other values, e.g. ``["Swiss German", "French"]``.

    Returns
    -------
    bool
        True if a word of ``value`` is also in one of ``others``.
    """
    words = set(value.lower().split())
    for other in others:
        if words & set(other.lower().split()):
            return True
    return False


def make_options(
    countries, code, difficulty, answer, column, excluded=None, similar=False
):
    """
    Build the four options of a question: the right answer and three wrong ones.

    The wrong options are values of ``column`` for countries chosen with
    ``get_candidates``, so the harder the question, the nearer these
    countries are to the country of the question. The values that are also
    right (``excluded``) or already chosen are skipped: if the candidates
    are not enough, the other countries are used, from the nearest.

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
    excluded : list of str, optional
        Values that cannot be wrong options, since they are also right
        (e.g. all the currencies of the country). Defaults to ``[answer]``.
    similar : bool, optional
        If True, the values with a word in common with ``excluded`` are
        skipped too (e.g. "German" when "Swiss German" is right).
        Defaults to False.

    Returns
    -------
    list of str
        The four options, shuffled.

    Raises
    ------
    ValueError
        If there are not enough different wrong options.
    """
    if excluded is None:
        excluded = [answer]

    candidates = get_candidates(countries, code, difficulty)
    random.shuffle(candidates)
    for other_code in rank_by_distance(countries, code):
        if other_code not in candidates:
            candidates.append(other_code)

    options = [answer]
    for candidate in candidates:
        values = countries.loc[candidate, column]
        # Some columns contain lists (e.g. capitals, currencies)
        if not isinstance(values, list):
            values = [values]
        for value in values:
            if value in excluded or value in options:
                continue
            if similar and shares_word(value, excluded):
                continue
            options.append(value)
            break
        if len(options) == N_WRONG_OPTIONS + 1:
            break

    if len(options) < N_WRONG_OPTIONS + 1:
        raise ValueError(f"Not enough different values in the column {column}")
    random.shuffle(options)
    return options


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
    # A look-alike flag would be a second right answer
    excluded = [answer]
    for look_alike in LOOK_ALIKE_FLAGS.get(code, []):
        if look_alike in countries.index:
            excluded.append(countries.loc[look_alike, "name"])

    return {
        "type": "flag",
        "difficulty": difficulty,
        "text": "Which country does this flag belong to?",
        "image": FLAG_URL + code.lower() + ".svg",
        "options": make_options(countries, code, difficulty, answer, "name", excluded),
        "answer": answer,
    }


def make_list_question(
    countries,
    difficulty,
    code,
    column,
    question_type,
    text,
    similar=False,
    check_reveal=False,
):
    """
    Generate a question whose answer is one of the values of a list column.

    Parameters
    ----------
    countries : pandas.DataFrame
        The table of the countries, indexed by ``cca3``.
    difficulty : str
        One of ``DIFFICULTIES``.
    code : str or None
        The ``cca3`` code of the country, or None for a random country.
    column : str
        The column with the lists of values (e.g. ``"capitals"``).
    question_type : str
        The type of the question (e.g. ``"capital"``).
    text : str
        The text of the question, with ``{name}`` for the name of the country.
    similar : bool, optional
        Passed to ``make_options``. Defaults to False.
    check_reveal : bool, optional
        If True, the values that reveal the country (e.g. "Mexico City")
        are the answer only of easy questions. Defaults to False.

    Returns
    -------
    dict
        The question, with the keys ``type``, ``difficulty``, ``text``,
        ``options`` and ``answer``.
    """
    code = choose_country(countries, difficulty, code, column, check_reveal)
    country = countries.loc[code]
    values = country[column]

    answers = []
    for value in values:
        # At medium and hard, a value that reveals the country is not an answer
        if (
            check_reveal
            and difficulty != "easy"
            and reveals_country(value, country["name"], country["demonym"])
        ):
            continue
        answers.append(value)
    # A country with only revealing values, asked with a given code
    if len(answers) == 0:
        answers = values
    # Any value of the country is right, so none of them can be a wrong option
    answer = random.choice(answers)

    return {
        "type": question_type,
        "difficulty": difficulty,
        "text": text.format(name=country["name"]),
        "options": make_options(
            countries, code, difficulty, answer, column, values, similar
        ),
        "answer": answer,
    }


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
    return make_list_question(
        countries,
        difficulty,
        code,
        "capitals",
        "capital",
        "What is the capital of {name}?",
        # Capitals such as Mexico City reveal the country: easy questions only
        check_reveal=True,
    )


def make_currency_question(countries, difficulty="easy", code=None):
    """
    Generate a question about the currency of a country.

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
    return make_list_question(
        countries,
        difficulty,
        code,
        "short_currencies",
        "currency",
        "Which currency is used in {name}?",
        # Currencies with similar names (e.g. pula and Botswana pula) are skipped
        similar=True,
        # Currencies still named after the country (e.g. Sierra Leonean leone)
        check_reveal=True,
    )


def make_language_question(countries, difficulty="easy", code=None):
    """
    Generate a question about an official language of a country.

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
    return make_list_question(
        countries,
        difficulty,
        code,
        "languages",
        "language",
        "Which of these is an official language of {name}?",
        # Languages with similar names (e.g. German and Swiss German) are skipped
        similar=True,
        # Languages such as Albanian reveal the country: easy questions only
        check_reveal=True,
    )


def choose_non_neighbour(countries, code, difficulty):
    """
    Choose a country that does not share a land border with a given country.

    The harder the question, the nearer the chosen country.

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
    str
        The ``cca3`` code of the chosen country.

    Raises
    ------
    ValueError
        If every other country is a neighbour.
    """
    borders = countries.loc[code, "borders"]
    candidates = []
    for other_code in get_candidates(countries, code, difficulty):
        if other_code not in borders:
            candidates.append(other_code)
    if len(candidates) > 0:
        return random.choice(candidates)

    # All the candidates are neighbours (e.g. China at the hard level):
    # the nearest country that is not a neighbour is chosen
    for other_code in rank_by_distance(countries, code):
        if other_code not in borders:
            return other_code
    raise ValueError(f"All the countries share a border with {code}")


def make_border_question(countries, difficulty="easy", code=None, negative=None):
    """
    Generate a question about the countries that border a country.

    The question asks which of the options shares a land border with the
    country, or, if ``negative`` is True, which of them does not.

    Parameters
    ----------
    countries : pandas.DataFrame
        The table of the countries, indexed by ``cca3``.
    difficulty : str, optional
        One of ``DIFFICULTIES``. Defaults to ``"easy"``.
    code : str, optional
        The ``cca3`` code of the country. Defaults to a random country with
        at least one neighbour, chosen according to the difficulty.
    negative : bool, optional
        If True, the right answer is the only option that is not a
        neighbour. Defaults to a random choice, when the country has at
        least ``N_WRONG_OPTIONS`` neighbours.

    Returns
    -------
    dict
        The question, with the keys ``type``, ``difficulty``, ``text``,
        ``options`` and ``answer``.

    Raises
    ------
    ValueError
        If the country has no neighbours, or if ``negative`` is True and
        the country has fewer than ``N_WRONG_OPTIONS`` neighbours.
    """
    code = choose_country(countries, difficulty, code, "borders")
    country = countries.loc[code]
    neighbours = []
    for neighbour_code in country["borders"]:
        neighbours.append(countries.loc[neighbour_code, "name"])
    if len(neighbours) == 0:
        raise ValueError(f"{country['name']} has no neighbours in the table")

    if negative is None:
        # The three wrong options of a negative question are neighbours
        negative = len(neighbours) >= N_WRONG_OPTIONS and random.choice([True, False])

    if negative:
        if len(neighbours) < N_WRONG_OPTIONS:
            raise ValueError(f"{country['name']} has too few neighbours")
        other_code = choose_non_neighbour(countries, code, difficulty)
        answer = countries.loc[other_code, "name"]
        options = random.sample(neighbours, N_WRONG_OPTIONS) + [answer]
        random.shuffle(options)
        question_type = "not_border"
        text = "Which of these countries does not share a land border with {name}?"
    else:
        answers = []
        for neighbour in neighbours:
            # At medium and hard, a neighbour with a similar name (e.g. Niger
            # and Nigeria) is not the answer
            if difficulty != "easy" and reveals_country(
                neighbour, country["name"], country["demonym"]
            ):
                continue
            answers.append(neighbour)
        if len(answers) == 0:
            answers = neighbours
        answer = random.choice(answers)
        # All the neighbours are right, so none of them can be a wrong option
        options = make_options(countries, code, difficulty, answer, "name", neighbours)
        question_type = "border"
        text = "Which of these countries shares a land border with {name}?"

    return {
        "type": question_type,
        "difficulty": difficulty,
        "text": text.format(name=country["name"]),
        "options": options,
        "answer": answer,
    }


def make_region_question(countries, difficulty="easy", code=None):
    """
    Generate a question about the region of a country (e.g. Europe).

    There are only five regions, so the wrong options cannot be made harder:
    this type of question is easy for every country.

    Parameters
    ----------
    countries : pandas.DataFrame
        The table of the countries, indexed by ``cca3``.
    difficulty : str, optional
        One of ``DIFFICULTIES``. Defaults to ``"easy"``, the only difficulty
        with countries for this type when ``code`` is not given.
    code : str, optional
        The ``cca3`` code of the country. Defaults to a random country.

    Returns
    -------
    dict
        The question, with the keys ``type``, ``difficulty``, ``text``,
        ``options`` and ``answer``.
    """
    code = choose_country(countries, difficulty, code, easy_only=True)
    country = countries.loc[code]
    answer = country["region"]
    text = "In which region of the world is {name}?"

    return {
        "type": "region",
        "difficulty": difficulty,
        "text": text.format(name=country["name"]),
        "options": make_options(countries, code, difficulty, answer, "region"),
        "answer": answer,
    }


# Each type of question, with the column that a country needs to have at
# least one value in (e.g. Micronesia has no currency), whether the values
# that reveal the country make the question easy, and whether the type is
# easy for every country
QUESTION_MAKERS = [
    (make_capital_question, "capitals", True, False),
    (make_flag_question, "name", False, False),
    (make_currency_question, "short_currencies", True, False),
    (make_language_question, "languages", True, False),
    (make_border_question, "borders", False, False),
    (make_region_question, None, False, True),
]


def make_next_question(countries, difficulty, used_codes):
    """
    Generate a question of a random type about a country not asked yet.

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
        The question, with also the key ``code``.

    Raises
    ------
    ValueError
        If all the countries of the difficulty have already been asked.
    """
    makers = []
    for maker in QUESTION_MAKERS:
        easy_only = maker[3]
        # The types that are easy for every country are only in easy questions
        if difficulty == "easy" or not easy_only:
            makers.append(maker)
    make_question, column, check_reveal, easy_only = random.choice(makers)

    available = []
    pool = get_country_pool(countries, difficulty, column, check_reveal, easy_only)
    for code in pool:
        if code not in used_codes:
            available.append(code)
    if len(available) == 0:
        raise ValueError(f"No more countries to ask at the {difficulty} level")

    code = random.choice(available)
    question = make_question(countries, difficulty, code=code)
    question["code"] = code
    return question


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
    """
    used_codes = []
    questions = []
    for i in range(n_questions):
        question = make_next_question(countries, difficulty, used_codes)
        used_codes.append(question["code"])
        questions.append(question)
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
