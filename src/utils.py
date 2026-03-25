"""
Utility function for the main ui
"""

from datetime import datetime
from random import choice
from typing import List, Sequence

from sqlalchemy.engine.base import Engine
from sqlmodel import Session, SQLModel, create_engine, select, text

from src.data import Event, Game, Match


def generate_data(engine: Engine, events: int, matches_per_event: int) -> None:
    """
    Generate some random data (i.e., match results) for testing.
    """

    match_results = [[1, 1], [1, 0, 1], [0, 1, 1], [0, 0], [0, 1, 0], [1, 0, 0]]
    decks = ["boros", "jeskay blink", "esper Blink", "titan"]

    with Session(engine) as session:
        for i in range(events):
            matches = []
            for _ in range(matches_per_event):
                deck = choice(decks)
                result = choice(match_results)
                games = []
                for elem in result:
                    games.append(
                        Game(on_the_play=choice([True, False]), win=bool(elem))
                    )
                matches.append(
                    Match(
                        archetype=deck,
                        date=datetime.now().isoformat(),
                        is_match_loss=False,
                        games=games,
                    )
                )
            event = Event(name=f"League_{i+1}", event_type="MTGO", matches=matches)
            session.add(event)
        session.commit()

    return None


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


def is_match_won(match: Match):
    if match.is_match_loss:
        return False
    total = 0
    for game in match.games:
        if game.win:
            total += 1
        else:
            total -= 1

    return total > 0


def get_wins(matches: Sequence[Match]) -> int:

    return len([m for m in matches if is_match_won(m)])


def get_archetype(session) -> Sequence[str]:

    statement = select(Match.archetype).distinct()
    autocomplete_options = session.exec(statement).all()
    return autocomplete_options
