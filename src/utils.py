"""
Utility function for the main ui
"""

from datetime import datetime
from random import choice
from typing import Sequence, Tuple

from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from src.data import Event, Game, GameStats, Match


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


def is_match_won(match: Match) -> bool:
    """
    Check if a Match was won
    """
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
    """
    Return how many, out of a sequence of Matches, were won
    """

    return len([m for m in matches if is_match_won(m)])


def get_archetypes(session) -> Sequence[str]:
    """
    Query the DB for all the archetypes for which a match was recorded
    """

    statement = select(Match.archetype).distinct()
    autocomplete_options = session.exec(statement).all()
    return autocomplete_options


def get_match_win(session, archetype) -> Tuple[int, int]:
    """
    For a given archetype, get the toal match played and how many were won
    """

    statement = (
        select(Match)
        .where(Match.archetype == archetype)
        .options(selectinload(Match.games))  # type: ignore
    )

    match_up = session.exec(statement).unique().all()
    total = len(match_up)
    wins = get_wins(match_up)

    return total, wins


def get_game_stats(session, archetype) -> GameStats:
    statement = select(Game).join(Match).where(Match.archetype == archetype).distinct()
    games = session.exec(statement).all()
    games_played = len(games)
    games_won = len([game for game in games if game.win])

    on_the_play_games_played = len([game for game in games if game.on_the_play])
    on_the_play_games_won = len(
        [game for game in games if game.on_the_play and game.win]
    )

    on_the_draw_games_played = len([game for game in games if not game.on_the_play])
    on_the_draw_games_won = len(
        [game for game in games if not game.on_the_play and game.win]
    )

    game_stats = GameStats(
        games_played=games_played,
        games_won=games_won,
        on_the_play_games_played=on_the_play_games_played,
        on_the_play_games_won=on_the_play_games_won,
        on_the_draw_games_played=on_the_draw_games_played,
        on_the_draw_games_won=on_the_draw_games_won,
    )

    return game_stats
