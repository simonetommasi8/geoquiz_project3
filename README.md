# GeoQuiz

A multiple-choice geography quiz generator, developed as the Python project
for the *Coding for Data Science and Data Management* course (A.Y. 2026/27).

> **Status:** work in progress.

## About the Project

GeoQuiz automatically generates geography quizzes about the countries of the world.

- Each quiz has **one question** and **four possible answers**, only one of which is correct.
- The **difficulty** can be chosen: in harder quizzes, the wrong answers are more
  similar to the correct one.
- A player answers the quizzes and receives an **overall score**, which takes into
  account the difficulty of each question.

## Data

### Sources

- [World countries](https://github.com/mledoze/countries) by mledoze: names, capitals,
  regions, borders, coordinates, area, currencies, languages and flags of the countries.
  Released under the [ODbL](https://opendatacommons.org/licenses/odbl/) license.
- [World Bank Indicators API](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation):
  the most recent available value of the population (`SP.POP.TOTL`) and of the GDP
  in current US$ (`NY.GDP.MKTP.CD`) of each country.

Both sources are downloaded automatically when the program runs: no data file
needs to be downloaded by hand.

### Cleaning

The two sources are joined into a single table, with one row for each country,
identified by its ISO 3166-1 alpha-3 code (e.g. `ITA`). All the questions of
the quiz read their data from this table.

- Only the countries marked as **UN members** are kept (194): the 193 member states
  plus Vatican City, which the dataset marks as a member although it is an
  observer state.
- The World Bank data are joined with a left join on the country code, so the
  aggregates of the World Bank (e.g. *World*, *Euro area*) are dropped.
- Countries without population or GDP data are excluded: **Vatican City**
  (no population and GDP) and **North Korea** (no GDP). The quiz uses
  **192 countries**.
- Two columns are computed: the **population density** (inhabitants per km²)
  and the **GDP per capita** (US$).

## Libraries

| Library | Used for |
|---------|----------|
| `requests` | downloading the countries dataset and calling the World Bank API |
| `pandas` | building, merging and cleaning the table of the countries |

Exact versions are listed in [`requirements.txt`](requirements.txt).

## Project Structure

```
geoquiz_project3/
├── README.md           # project description and instructions
├── requirements.txt    # Python libraries needed by the project
├── data/               # downloaded data (not tracked by Git)
├── geoquiz/            # source code
│   ├── data.py         # download and load the data
│   ├── cleaning.py     # build the table of the countries
│   └── main.py
└── notebooks/
```

## Setup

The project requires **Python 3.12, 3.13 or 3.14** and an internet connection.

```bash
git clone https://github.com/simonetommasi8/geoquiz_project3.git
cd geoquiz_project3
python3 -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

At the moment, the project builds the table of the countries and prints some
data about it. From the root folder of the project, with the virtual environment
active, run:

```bash
python -m geoquiz.main
```

The quiz will be played through a **Streamlit** web app, which is still in
development: this section will be updated with the instructions to start it.

## Author

Simone Tommasi