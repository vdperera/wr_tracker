"""
utility function to test code
"""

from datetime import datetime
from random import choice

from sqlalchemy.engine.base import Engine

from src.data import ArchetypeData, Event, Game, Match, ResultData


def generate_data(
    LocalSession: sessionmaker, events: int, matches_per_event: int
) -> None:
    """
    Generate some random data (i.e., match results) for testing.
    """

    match_results = [[1, 1], [1, 0, 1], [0, 1, 1], [0, 0], [0, 1, 0], [1, 0, 0]]
    decks = ["boros", "jeskay blink", "esper Blink", "titan"]

    with LocalSession() as session:
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
