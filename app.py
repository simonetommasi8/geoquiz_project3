"""
GeoQuiz - Streamlit web app.

The app only shows the questions and collects the answers: the questions,
the score, the leaderboard and the charts come from the ``geoquiz`` package.

Run with:  streamlit run app.py
"""

import matplotlib.pyplot as plt
import requests
import streamlit as st

from geoquiz.cleaning import build_countries_table
from geoquiz.leaderboard import (
    MAX_NAME_LENGTH,
    add_score,
    get_top_scores,
    is_new_record,
    load_leaderboard,
    save_leaderboard,
)
from geoquiz.plots import plot_right_answers_by_type, plot_score_progress
from geoquiz.questions import make_next_question, next_difficulty
from geoquiz.scoring import make_results_table, question_points, summarize_score

N_QUESTIONS = 10

# The modes of the quiz, with the difficulty of a fixed mode
# (None for the adaptive mode, the only one in the leaderboard)
MODES = {
    "Adaptive (ranked in the leaderboard)": None,
    "Easy": "easy",
    "Medium": "medium",
    "Hard": "hard",
}

# The data are downloaded again once a day, to follow the World Bank updates
ONE_DAY = 24 * 60 * 60  # in seconds

st.set_page_config(page_title="GeoQuiz", page_icon="🌍", layout="centered")


# --- Helper functions -------------------------------------------------------


@st.cache_data(ttl=ONE_DAY, show_spinner="Downloading the data of the countries...")
def load_countries():
    """Build the table of the countries, only once a day thanks to the cache."""
    return build_countries_table()


def start_quiz(name, mode):
    """Save the settings of a new quiz in the session state and go to the questions."""
    st.session_state.name = name
    st.session_state.adaptive = MODES[mode] is None
    if st.session_state.adaptive:
        st.session_state.difficulty = "medium"  # the adaptive mode starts here
    else:
        st.session_state.difficulty = MODES[mode]
    st.session_state.used_codes = []
    st.session_state.questions = []
    st.session_state.answers = []
    st.session_state.saved = False
    st.session_state.screen = "question"
    new_question()


def new_question():
    """Generate the next question and save it in the session state."""
    question = make_next_question(
        countries, st.session_state.difficulty, st.session_state.used_codes
    )
    st.session_state.used_codes.append(question["code"])
    st.session_state.question = question
    st.session_state.answered = False


def current_score():
    """Compute the score of the questions answered so far."""
    if len(st.session_state.answers) == 0:
        return 0
    results = make_results_table(st.session_state.questions, st.session_state.answers)
    # Only the points are shown: _ stands for the values not used
    points, _, _ = summarize_score(results)
    return points


def show_flag(url):
    """Show a flag with a thin grey border, so that white flags are visible."""
    st.markdown(
        f'<img src="{url}" style="width:220px; max-width:100%; '
        f'border:1px solid #c9c7c1; border-radius:4px; margin-bottom:16px;">',
        unsafe_allow_html=True,
    )


@st.dialog("🏆 New record!")
def show_new_record(name, points):
    """Open a pop-up that celebrates a new record of the leaderboard."""
    st.subheader(f"Congratulations, {name}!")
    st.write(f"With **{points:,} points** you are the new number 1 of GeoQuiz.")
    if st.button("Great!", type="primary", width="stretch"):
        st.rerun()  # close the pop-up


def show_leaderboard():
    """Show the 10 best scores, or a message if there are none yet."""
    top = get_top_scores(load_leaderboard())
    if len(top) == 0:
        st.info("No scores yet: be the first one!")
    else:
        st.dataframe(top, width="stretch")


# --- Data -------------------------------------------------------------------

try:
    countries = load_countries()
except (requests.RequestException, ValueError) as error:
    st.error(
        "The data of the countries could not be downloaded. "
        f"Please try again in a few minutes. ({error})"
    )
    st.stop()

if "screen" not in st.session_state:
    st.session_state.screen = "start"


# --- Start screen -----------------------------------------------------------

if st.session_state.screen == "start":
    st.title("🌍 GeoQuiz")
    st.write(
        f"Test your knowledge of the countries of the world: {N_QUESTIONS} "
        "questions, four answers each, only one of them right."
    )

    name = st.text_input("Your name", max_chars=MAX_NAME_LENGTH)
    mode = st.selectbox("Mode", list(MODES))
    st.caption(
        "In the adaptive mode, each question is harder after a right answer "
        "and easier after a wrong one. Harder questions are worth more points."
    )

    if st.button(
        "Start the quiz", type="primary", disabled=name.strip() == "", width="stretch"
    ):
        start_quiz(name.strip(), mode)
        st.rerun()

    st.subheader("🏆 Leaderboard")
    show_leaderboard()


# --- Question screen --------------------------------------------------------

elif st.session_state.screen == "question":
    question = st.session_state.question
    # The current question is already in used_codes, also after the answer
    number = len(st.session_state.used_codes)

    col_number, col_level, col_score = st.columns(3)
    col_number.metric("Question", f"{number} / {N_QUESTIONS}")
    col_level.metric("Level", question["difficulty"].capitalize())
    col_score.metric("Score", current_score())

    st.subheader(question["text"])
    if "image" in question:
        show_flag(question["image"])

    if not st.session_state.answered:
        # One button for each option, two on each row (on a phone the rows
        # are one under the other, so the options keep their order)
        options = question["options"]
        for row in range(0, len(options), 2):
            columns = st.columns(2)
            for col in range(2):
                i = row + col
                if columns[col].button(options[i], key=f"option_{i}", width="stretch"):
                    st.session_state.questions.append(question)
                    st.session_state.answers.append(options[i])
                    st.session_state.answered = True
                    st.rerun()
    else:
        answer = st.session_state.answers[-1]
        was_right = answer == question["answer"]
        if was_right:
            st.success(
                f"✅ Right! **{answer}** is the answer: +{question_points(question)} points"
            )
        else:
            st.error(
                f"❌ Wrong: you answered {answer}, the answer was **{question['answer']}**"
            )

        if number < N_QUESTIONS:
            if st.button("Next question ➜", type="primary", width="stretch"):
                if st.session_state.adaptive:
                    st.session_state.difficulty = next_difficulty(
                        st.session_state.difficulty, was_right
                    )
                new_question()
                st.rerun()
        elif st.button("See the results ➜", type="primary", width="stretch"):
            st.session_state.screen = "end"
            st.rerun()


# --- End screen -------------------------------------------------------------

elif st.session_state.screen == "end":
    results = make_results_table(st.session_state.questions, st.session_state.answers)
    # Only the points are shown: _ stands for the values not used
    points, _, _ = summarize_score(results)

    st.title(f"🎉 Well done, {st.session_state.name}!")
    st.metric("Score", f"{points:,}")

    if st.session_state.adaptive:
        # The score is saved once, even if the page is shown again
        if not st.session_state.saved:
            leaderboard = load_leaderboard()
            # The record is checked before the new score is added
            new_record = is_new_record(leaderboard, points)
            leaderboard = add_score(leaderboard, st.session_state.name, points)
            save_leaderboard(leaderboard)
            st.session_state.saved = True
            if new_record:
                show_new_record(st.session_state.name, points)
        st.subheader("🏆 Leaderboard")
        show_leaderboard()
    else:
        st.caption("Only the adaptive mode is ranked in the leaderboard.")

    st.subheader("📊 Your results")
    for fig in [plot_right_answers_by_type(results), plot_score_progress(results)]:
        st.pyplot(fig)
        plt.close(fig)  # free the memory of the chart

    if st.button("🔄 Play again", type="primary", width="stretch"):
        st.session_state.screen = "start"
        st.rerun()
