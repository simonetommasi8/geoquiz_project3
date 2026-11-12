"""Compute the score of a quiz."""

import pandas as pd

# The points of a right answer for each difficulty, in hundreds, so that the
# scores are whole numbers also after the weights of the types
DIFFICULTY_POINTS = {"easy": 100, "medium": 200, "hard": 300}

# Some types of question are harder than others at the same level, so their
# points are multiplied by a weight
TYPE_WEIGHTS = {
    "capital": 1,
    "flag": 1,
    "language": 1,
    "region": 1,
    "currency": 1.25,
    "border": 1.5,
    "not_border": 1.5,
    "comparison": 1.5,
    "numeric": 2,
}


def question_points(question):
    """
    Compute the points of a right answer to a question.

    Parameters
    ----------
    question : dict
        The question, with the keys ``type`` and ``difficulty``.

    Returns
    -------
    int
        The points of the difficulty multiplied by the weight of the type
        (e.g. 300 for a hard capital question, 400 for a medium numeric one).
    """
    points = DIFFICULTY_POINTS[question["difficulty"]] * TYPE_WEIGHTS[question["type"]]
    return round(points)


def make_results_table(questions, answers):
    """
    Build a table with the result of each question of a quiz.

    Parameters
    ----------
    questions : list of dict
        The questions of the quiz.
    answers : list of str
        The answers of the player, in the same order as the questions.

    Returns
    -------
    pandas.DataFrame
        One row for each question, with the columns ``type``,
        ``difficulty``, ``answer``, ``right_answer``, ``was_right``,
        ``points`` (0 for a wrong answer) and ``max_points``.

    Raises
    ------
    ValueError
        If the numbers of questions and answers are different.
    """
    if len(questions) != len(answers):
        raise ValueError("There must be one answer for each question")

    rows = []
    for i in range(len(questions)):
        question = questions[i]
        was_right = answers[i] == question["answer"]
        max_points = question_points(question)
        # A wrong answer gives no points, but it does not remove any
        points = 0
        if was_right:
            points = max_points
        rows.append(
            {
                "type": question["type"],
                "difficulty": question["difficulty"],
                "answer": answers[i],
                "right_answer": question["answer"],
                "was_right": was_right,
                "points": points,
                "max_points": max_points,
            }
        )
    return pd.DataFrame(rows)


def summarize_score(results):
    """
    Compute the total score of a quiz.

    Parameters
    ----------
    results : pandas.DataFrame
        The results, as returned by ``make_results_table``.

    Returns
    -------
    tuple of int
        The points of the player, the points of a quiz with all the answers
        right, and the percentage of these points taken by the player.

    Raises
    ------
    ValueError
        If the table is empty.
    """
    if len(results) == 0:
        raise ValueError("The quiz has no questions")
    points = int(results["points"].sum())
    max_points = int(results["max_points"].sum())
    percentage = round(100 * points / max_points)
    return points, max_points, percentage
