"""Build the table of the countries and print some data about it."""

from geoquiz.cleaning import build_countries_table


def main():
    """Build the table of the countries and print its size and one country."""
    countries = build_countries_table()
    print(countries.shape)
    print(countries.loc["ITA"])


# The code runs only when the file is executed, not when it is imported
if __name__ == "__main__":
    main()
