"""Compare the names of the countries with the values of the questions."""

# Words that do not reveal a country, even if they are in its name
GENERIC_WORDS = {"and", "of", "the", "city", "saint", "la", "de", "new"}

# Two words with this many initial letters in common have the same root
# (e.g. "Comorian" and "Comoros")
ROOT_LENGTH = 5


def get_words(text):
    """
    Split a text into lowercase words.

    Parameters
    ----------
    text : str
        The text, e.g. ``"Guinea-Bissau"``.

    Returns
    -------
    list of str
        The words, e.g. ``["guinea", "bissau"]``.
    """
    return text.replace("-", " ").replace(",", " ").lower().split()


def words_match(word, other):
    """
    Tell whether two words have the same root.

    Two words match if one starts with the other (e.g. "lao" and "laos") or if
    they have the first ``ROOT_LENGTH`` letters in common (e.g. "comorian" and
    "comoros").

    Parameters
    ----------
    word, other : str
        The two words, in lowercase.

    Returns
    -------
    bool
        True if the two words have the same root.
    """
    if word.startswith(other) or other.startswith(word):
        return True
    return len(word) >= ROOT_LENGTH and word[:ROOT_LENGTH] == other[:ROOT_LENGTH]


def reveals_country(value, name, demonym):
    """
    Tell whether a value contains the name or the demonym of a country.

    For instance, "Mexico City" reveals Mexico and "Albanian" reveals Albania:
    as answers, they would make a question too easy.

    Parameters
    ----------
    value : str
        The value, e.g. a capital, a language or a currency.
    name : str
        The name of the country.
    demonym : str
        The demonym of the country, e.g. ``"Albanian"``.

    Returns
    -------
    bool
        True if a word of the value has the same root as a word of the name
        or of the demonym.
    """
    country_words = get_words(name + " " + demonym)
    for word in get_words(value):
        if word in GENERIC_WORDS:
            continue
        for country_word in country_words:
            if country_word not in GENERIC_WORDS and words_match(word, country_word):
                return True
    return False


def shorten_currency(currency, name, demonym):
    """
    Remove the name and the demonym of a country from the name of its currency.

    For instance, "Botswana pula" becomes "pula" and "Swiss franc" becomes
    "franc", so that the name of the currency does not reveal the country.

    Parameters
    ----------
    currency : str
        The name of the currency.
    name : str
        The name of the country.
    demonym : str
        The demonym of the country.

    Returns
    -------
    str
        The short name of the currency, or the full name if nothing is left
        (e.g. "Sierra Leonean leone").
    """
    country_words = get_words(name + " " + demonym)
    short_words = []
    for word in currency.split():
        if (
            not reveals_country(word, name, demonym)
            and word.lower() not in country_words
        ):
            short_words.append(word)
    if len(short_words) == 0:
        return currency
    return " ".join(short_words)
