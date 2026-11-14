# GeoQuiz

A multiple-choice geography quiz generator, developed as the Python project
for the *Coding for Data Science and Data Management* course (A.Y. 2026/27).

**▶ Play online: [https://geoquizsimo.streamlit.app](https://geoquizsimo.streamlit.app)**

> If the app has not been used for a while, Streamlit puts it to sleep: click
> the button to wake it up and wait about a minute.

## About the Project

GeoQuiz automatically generates geography quizzes about the countries of the world,
and lets a player answer them in a **Streamlit** web app.

- Each question has **four possible answers**, only one of which is correct.
- There are eight types of questions:

| Type | Example |
|------|---------|
| Capital | *What is the capital of Italy?* |
| Flag | *Which country does this flag belong to?* |
| Currency | *Which currency is used in Botswana?* |
| Language | *Which of these is an official language of Belgium?* |
| Borders | *Which of these countries shares a land border with Italy?* (or *does not share*) |
| Region | *In which region of the world is San Marino?* |
| Comparison | *Which of these countries has the largest population?* (also GDP and area, largest or smallest) |
| Number | *What is the area of Italy?* (also the population) |

- The **difficulty** can be fixed (easy, medium or hard) or **adaptive**, following
  the answers of the player: in harder questions, the countries are less known and
  the wrong answers are more similar to the right one.
- A player answers the quizzes and receives an **overall score**, which takes into
  account the difficulty of each question.

### How the Difficulty Works

The difficulty of a question depends on two criteria.

1. **How well known the country is.** The countries are ranked by GDP, since the
   largest economies are the best known: easy questions are about the 50 largest
   economies, medium questions about the 51st to the 120th, hard questions about
   the others.
2. **How similar the wrong answers are.** The other countries are ranked from the
   nearest to the farthest, and the wrong answers come from the 10 nearest (hard),
   from the 11th to the 40th (medium) or beyond the 100th (easy).

The distance between two countries is the great-circle distance between their
central points, computed with the haversine formula on a spherical Earth.
Neighbouring countries are considered at distance 0, since they touch each other
even when their central points are far apart (e.g. Italy and France).

Some types of questions follow their own rules:

- **Borders:** at the hard level, the wrong answers are near countries that are
  not neighbours. In the negative form, the three wrong answers are neighbours
  and the right one is a near country that is not.
- **Region:** with only five regions (Africa, Americas, Asia, Europe, Oceania),
  the wrong answers cannot be made harder, so these questions are always easy.
  The regions are the ones of the dataset, also for transcontinental countries
  (Russia in Europe, Turkey in Asia).
- **Comparison:** the difficulty depends on how close the values are. The
  countries are ranked by the value, and the second country is 40 or more
  positions after the right answer (easy), from 10 to 39 (medium) or less than
  10 (hard). The right value is always at least 5% larger (or smaller) than the
  others, so the answer does not depend on the year of the data.
- **Number:** the four options are like the steps of a ladder, each one 4 (easy),
  2 (medium) or 1.3 (hard) times the previous one, with the right answer on a
  random step. All the options are rounded to two significant digits (e.g.
  *59 million*, *300,000 km²*), so the right one does not look more precise,
  and no option is larger or smaller than every country.

In the **adaptive** mode, the quiz starts at the medium level, and each question
is one level harder after a right answer and one level easier after a wrong one.
In every quiz, each question is about a different country.

Some answers contain the name of their country, which makes a question easy:
capitals such as *Mexico City*, languages such as *Albanian*, currencies such as
*Botswana pula*. The currencies are shown without the name of the country
(*pula*, *franc*, *dollar*); the capitals and the languages that still reveal
their country are only used in easy questions, whatever the GDP of the country.

Every question has a single right answer: the values shared with the country
(e.g. the euro of its neighbours) and the flags that look almost the same
(Indonesia and Monaco, Chad and Romania, Netherlands and Luxembourg) are never
used as wrong answers. In the same way, the neighbours with a similar name
(*Niger* and *Nigeria*, *Sudan* and *South Sudan*) are the right answer of a
border question only at the easy level.

### Score

A right answer is worth **100**, **200** or **300** points for an easy, medium
or hard question. Some types of questions are harder than others at the same
level, so their points are multiplied by a weight:

| Type | Weight |
|------|--------|
| Capital, Flag, Language, Region | 1 |
| Currency | 1.25 |
| Borders, Comparison | 1.5 |
| Number | 2 |

A wrong answer is worth 0 points, without penalties. Since the type of each
question is random, the luck of the questions plays a small part in the score,
as in many arcade games; the difficulty matters more, since a right answer
in the adaptive mode leads to harder questions, which are worth more points.

### Leaderboard

At the end of a quiz in the **adaptive** mode, the player writes a name and the
score is added to a leaderboard with the 10 best scores. Only the adaptive mode
is ranked, since all the players start at the same level and the scores can be
compared. The scores are saved in a CSV file (`data/leaderboard.csv`, not tracked
by Git): when the app runs online, the file is reset every time the app restarts.

### Charts

At the end of a quiz, two charts show the results: the right answers for each
type of question, and the score after each question.


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
- The **demonym** of each country (e.g. *Italian*) is kept, and the names of the
  currencies are shortened by removing the name and the demonym of the country
  (e.g. *Botswana pula* becomes *pula*).
- The **borders** with countries that are not in the table are removed (e.g.
  Vatican City for Italy, Western Sahara for Morocco): South Korea is left with
  no neighbours, like the island countries.

## Libraries

| Library | Used for |
|---------|----------|
| `requests` | downloading the countries dataset and calling the World Bank API |
| `pandas` | building, merging and cleaning the table of the countries |
| `numpy` | computing the distances between the countries |
| `matplotlib` | drawing the charts with the results of a quiz |
| `streamlit` | the web app of the quiz |

Exact versions are listed in [`requirements.txt`](requirements.txt).

## Project Structure

```
geoquiz_project3/
├── README.md           # project description and instructions
├── requirements.txt    # Python libraries needed by the project
├── app.py              # the Streamlit web app
├── .streamlit/
│   └── config.toml     # colors and font of the app
├── data/               # downloaded data and leaderboard (not tracked by Git)
├── fonts/              # the Poppins font of the charts, with its license
├── geoquiz/            # source code
│   ├── data.py         # download and load the data
│   ├── cleaning.py     # build the table of the countries
│   ├── names.py        # compare the names of the countries with the answers
│   ├── distances.py    # distances between the countries (NumPy)
│   ├── formatting.py   # write the numbers in a readable way
│   ├── questions.py    # generate the questions of the quiz
│   ├── scoring.py      # compute the score of a quiz
│   ├── leaderboard.py  # keep the best scores of the players
│   ├── plots.py        # draw the charts with the results (matplotlib)
│   └── main.py         # build the table of the countries and print it
```

The logic of the quiz is in the `geoquiz` package, while `app.py` only shows
the questions and collects the answers: the same functions can be used in a
notebook or in a script.

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

The quiz can be played online at [https://geoquizsimo.streamlit.app](https://geoquizsimo.streamlit.app),
or on your own computer. From the root folder of the project, with the virtual environment active, run:

```bash
streamlit run app.py
```

The app opens in the browser at `http://localhost:8501`. The first time, the
data of the countries are downloaded, which takes a few seconds; then they are
kept in memory for one day. To stop the app, press `Ctrl + C` in the terminal.

To check that the data are downloaded and cleaned correctly, without the app,
run:

```bash
python -m geoquiz.main
```

It prints the size of the table of the countries (192 rows) and the data of Italy.

## Limitations

- The leaderboard is saved in a CSV file: in the online app, it is reset every
  time the app restarts or is updated.
- The difficulty of a country depends on its GDP, which is a good but not
  perfect measure of how well known it is.
- The languages are the official ones of the dataset, which can differ from the
  languages actually spoken (e.g. French is widely spoken in Morocco, but it is
  not an official language there).
- The type of each question is random, so the score also depends on the luck of
  the questions.

## Credits

The charts use the [Poppins](https://fonts.google.com/specimen/Poppins) font
by the Poppins Project Authors, released under the
[SIL Open Font License](fonts/OFL.txt).

## Author

Simone Tommasi