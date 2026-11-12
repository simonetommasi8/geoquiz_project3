"""Draw the charts with the results of a quiz."""

import os

import matplotlib.pyplot as plt
from matplotlib import font_manager

# The colors of the charts: one color for the data, a light grey for the
# empty part of the bars and the grid, and darker greys for the text
DATA_COLOR = "#2a78d6"
TRACK_COLOR = "#eceae5"
TITLE_COLOR = "#0b0b0b"
TEXT_COLOR = "#52514e"

FIGURE_SIZE = (6, 3.5)  # width and height in inches

# The thickness of the bars in the chart of the types, in points
BAR_WIDTH = 14

# The colors of the bars in the chart of the types, from the top: one for
# each of the eight types (the two forms of the border questions are one)
BAR_COLORS = [
    "#e34948",  # red
    "#2a78d6",  # blue
    "#eda100",  # yellow
    "#008300",  # green
    "#6250d6",  # violet
    "#1fa2d6",  # light blue
    "#eb6834",  # orange
    "#e87ba4",  # pink
]

# The font of the charts, with its files in the fonts folder of the project
FONT_NAME = "Poppins"
FONT_FILES = [
    os.path.join("fonts", "Poppins-Regular.ttf"),
    os.path.join("fonts", "Poppins-Bold.ttf"),
]


def use_font():
    """
    Load the font of the charts and use it for all their texts.

    If the files of the font are missing, the charts keep the default font
    of matplotlib.
    """
    for path in FONT_FILES:
        if not os.path.exists(path):
            return
        font_manager.fontManager.addfont(path)
    plt.rcParams["font.family"] = FONT_NAME


def style_axes(ax, title):
    """
    Give the same simple style to the axes of every chart.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes of a chart.
    title : str
        The title of the chart, written in bold on the left.
    """
    # No borders around the chart: the grid and the labels are enough
    for side in ["top", "right", "bottom", "left"]:
        ax.spines[side].set_visible(False)
    ax.tick_params(colors=TEXT_COLOR, length=0)
    ax.xaxis.label.set_color(TEXT_COLOR)
    ax.yaxis.label.set_color(TEXT_COLOR)
    ax.set_title(title, loc="left", fontweight="bold", color=TITLE_COLOR, pad=12)
    # The grid is drawn behind the data
    ax.set_axisbelow(True)


def plot_right_answers_by_type(results):
    """
    Draw the share of right answers for each type of question.

    Parameters
    ----------
    results : pandas.DataFrame
        The results, as returned by ``make_results_table``.

    Returns
    -------
    matplotlib.figure.Figure
        A chart with one rounded bar for each type, like a progress bar:
        the colored part is the share of right answers, and the number of
        right answers out of the questions of the type is written next to it
        (e.g. "2 / 3"). Each bar and its label have a color of
        ``BAR_COLORS``, from the top.
    """
    # The two forms of the border questions are counted together
    types = results["type"].replace("not_border", "border")
    counts = results.groupby(types)["was_right"].agg(["sum", "count"])
    counts = counts.sort_values("count")
    shares = 100 * counts["sum"] / counts["count"]

    use_font()
    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    # The bars are drawn from the bottom (i = 0), the colors go from the top
    colors = []
    for i in range(len(counts)):
        colors.append(BAR_COLORS[len(counts) - 1 - i])

    for i in range(len(counts)):
        # Each bar is a thick line with rounded ends: the grey track is the
        # whole bar, the colored part the right answers
        ax.plot(
            [0, 100],
            [i, i],
            color=TRACK_COLOR,
            linewidth=BAR_WIDTH,
            solid_capstyle="round",
        )
        if shares.iloc[i] > 0:
            ax.plot(
                [0, shares.iloc[i]],
                [i, i],
                color=colors[i],
                linewidth=BAR_WIDTH,
                solid_capstyle="round",
            )
        text = f"{counts['sum'].iloc[i]} / {counts['count'].iloc[i]}"
        ax.text(106, i, text, va="center", color=TEXT_COLOR)

    ax.set_yticks(range(len(counts)), counts.index)
    ax.set_xticks([])
    ax.set_xlim(-4, 118)
    ax.set_ylim(-0.7, len(counts) - 0.3)
    style_axes(ax, "Right answers by type of question")
    # Each label has the color of its bar (after style_axes, which makes
    # all the labels grey)
    for i in range(len(counts)):
        ax.get_yticklabels()[i].set_color(colors[i])
        ax.get_yticklabels()[i].set_fontweight("bold")
    fig.tight_layout()
    return fig


def plot_score_progress(results):
    """
    Draw how the score grows during the quiz.

    Parameters
    ----------
    results : pandas.DataFrame
        The results, as returned by ``make_results_table``.

    Returns
    -------
    matplotlib.figure.Figure
        A line chart with the score after each question, with a light area
        under the line: a full dot for a right answer, an empty dot for a
        wrong one, and the final score written next to the last dot.
    """
    numbers = results.index + 1  # the questions, numbered from 1
    # The score after each question is the sum of the points up to it
    scores = results["points"].cumsum()
    right = results["was_right"]

    use_font()
    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    ax.fill_between(numbers, scores, color=DATA_COLOR, alpha=0.12)
    ax.plot(numbers, scores, color=DATA_COLOR, linewidth=2)
    # Shape, not only color, tells right and wrong answers apart
    ax.scatter(
        numbers[right],
        scores[right],
        color=DATA_COLOR,
        s=60,
        zorder=3,
        label="Right answer",
    )
    ax.scatter(
        numbers[~right],
        scores[~right],
        facecolor="white",
        edgecolor=DATA_COLOR,
        linewidth=2,
        s=60,
        zorder=3,
        label="Wrong answer",
    )
    ax.annotate(
        f"{scores.iloc[-1]:,}",
        (numbers[-1], scores.iloc[-1]),
        xytext=(0, 10),
        textcoords="offset points",
        ha="center",
        fontweight="bold",
        color=TITLE_COLOR,
    )

    ax.set_xticks(list(numbers))
    ax.set_xlim(0.5, len(results) + 0.5)
    # At least 100 points of height, so that a quiz with no points has
    # whole numbers on the axis
    ax.set_ylim(0, max(scores.max(), 100) * 1.2)
    ax.set_xlabel("Question")
    ax.grid(axis="y", color=TRACK_COLOR)
    ax.legend(frameon=False, labelcolor=TEXT_COLOR, loc="upper left")
    style_axes(ax, "Score during the quiz")
    fig.tight_layout()
    return fig
