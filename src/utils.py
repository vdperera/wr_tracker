"""
Utility function for the main ui
"""

from datetime import datetime
from random import choice
from typing import List, Sequence

from src.data import Game, Match
from src.to_db.data import Match as MatchDB

match_results = [[1, 1], [1, 0, 1], [0, 1, 1], [0, 0], [0, 1, 0], [1, 0, 0]]
decks = ["boros", "jeskay blink", "esper Blink", "titan"]


def generate_data(total: int) -> List[Match]:
    """
    Generate some random data (i.e., match results) for testing
    """

    all_matches = []
    for _ in range(total):
        deck = choice(decks)

        new_match = Match(deck, datetime.now().isoformat(), False, [])
        result = choice(match_results)
        play = choice([True, False])

        for elem in result:
            new_match.add_game(Game(play, bool(elem)))
            if elem:
                play = False
            else:
                play = True
        all_matches.append(new_match)
    return all_matches


def generate_sigle_affinity_match():
    """
    Generate a single match with a specific archetype name (affiity)
    """

    new_match = Match("Affinity", datetime.now().isoformat(), [])
    result = choice(match_results)
    play = choice([True, False])
    for elem in result:
        new_match.add_game(Game(play, bool(elem)))
        if elem:
            play = False
        else:
            play = True
    return new_match


def toggle_emoji(button1, button2) -> None:
    """
    Toggle a pair of emoji. When clicking on a grayed out, remove the greyscale filter from the
    emoji clicked and add it to the other emoji in the pair
    """

    button1_grayed = "grayscale" in button1._classes  # pylint: disable=protected-access
    button2_grayed = "grayscale" in button2._classes  # pylint: disable=protected-access

    # initial state, grey button2
    if button1_grayed and button2_grayed:
        button1.classes(remove="grayscale opacity-50")

    if button1_grayed and not button2_grayed:
        button2.classes("grayscale opacity-50")
        button1.classes(remove="grayscale opacity-50")

    if not button1_grayed and button2_grayed:
        button1.classes("grayscale opacity-50")


def is_match_won(match: MatchDB):
    if match.is_match_loss:
        return False
    total = 0
    for game in match.games:
        if game.win:
            total += 1
        else:
            total -= 1

    return total > 0


def get_wins(matches: Sequence[MatchDB]) -> int:

    return len([m for m in matches if is_match_won(m)])
