"""Format the numbers shown in the quiz."""

# The numbers are rounded to this many significant digits (e.g. 59 million),
# so that all the options of a question look alike
SIGNIFICANT_DIGITS = 2

# The names of the large numbers, from the largest
LARGE_NUMBER_NAMES = [
    (1_000_000_000_000, "trillion"),
    (1_000_000_000, "billion"),
    (1_000_000, "million"),
]


def round_significant(value, digits=SIGNIFICANT_DIGITS):
    """
    Round a number to a number of significant digits.

    Parameters
    ----------
    value : float
        The number to round, e.g. ``58915656``.
    digits : int, optional
        The number of significant digits. Defaults to ``SIGNIFICANT_DIGITS``.

    Returns
    -------
    float
        The rounded number, e.g. ``59000000``.
    """
    # The format "g" with 2 digits writes the number with 2 significant
    # digits (58915656 becomes "5.9e+07"), and float turns it back into a number
    return float(f"{value:.{digits}g}")


def format_large_number(value):
    """
    Write a number with a word for millions, billions and trillions.

    Parameters
    ----------
    value : float
        The number, e.g. ``59000000``, ``300000`` or ``0.44``.

    Returns
    -------
    str
        The number as text, e.g. ``"59 million"``, ``"300,000"`` or ``"0.44"``.
    """
    # :g drops the useless zeros (59.0 becomes 59), and the comma separates
    # the thousands (300,000)
    for size, name in LARGE_NUMBER_NAMES:
        if value >= size:
            return f"{value / size:g} {name}"
    return f"{value:,g}"


def format_value(value, column):
    """
    Round a value of the table and write it with its unit.

    Parameters
    ----------
    value : float
        The value, e.g. ``301336``.
    column : str
        The column of the value: ``"population"``, ``"area"`` or ``"gdp"``.

    Returns
    -------
    str
        The value as text, e.g. ``"300,000 km²"``, ``"59 million"`` or
        ``"$2.3 trillion"``.
    """
    text = format_large_number(round_significant(value))
    if column == "area":
        return text + " km²"
    if column == "gdp":
        return "$" + text
    return text
