"""
Utility function for the main ui
"""

import sqlite3
from datetime import datetime
from typing import Sequence

from nicegui import app, ui
from sqlalchemy.orm import selectinload
from sqlmodel import create_engine, select
from webview import FileDialog

from src.data import ArchetypeData, Event, Game, Match, ResultData


def mark_dirty() -> None:
    """
    Flag the current client's session as having unsaved changes
    """
    app.storage.client["dirty"] = True


def is_dirty() -> bool:
    """
    Check whether the current client's session has unsaved changes
    """
    return app.storage.client.get("dirty", False)


def clear_dirty() -> None:
    """
    Flag the current client's session as having no unsaved changes (e.g. after a save/load)
    """
    app.storage.client["dirty"] = False


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


def get_match_result(match: Match) -> str:
    """
    Classify a Match as "win", "loss" or "draw" based on its games' results
    """
    if match.is_match_loss:
        return "loss"

    total = sum(1 if game.win else -1 for game in match.games)
    if total > 0:
        return "win"
    if total < 0:
        return "loss"
    return "draw"


def get_event_score(matches: Sequence[Match]) -> tuple[int, int, int]:
    """
    Return the (wins, losses, draws) record for a sequence of Matches
    """
    results = [get_match_result(match) for match in matches]
    return (
        results.count("win"),
        results.count("loss"),
        results.count("draw"),
    )


def get_event_types(session_maker) -> Sequence[str]:
    """
    Query the DB for all the event types for which an event was recorded
    """
    with session_maker() as session:
        statement = select(Event.event_type).distinct()
        autocomplete_options = session.execute(statement).scalars().all()
    return autocomplete_options


def get_events(session_maker) -> Sequence[Event]:
    """
    Query the DB for all the recorded events, ordered from most to least recently created
    """
    with session_maker() as session:
        statement = select(Event).order_by(Event.created_at.desc())
        events = session.execute(statement).scalars().all()
    return events


def get_active_events(session_maker) -> Sequence[Event]:
    """
    Query the DB for all active events, ordered from most to least recently created
    """
    with session_maker() as session:
        statement = (
            select(Event)
            .where(Event.active.is_(True))
            .order_by(Event.created_at.desc())
        )
        events = session.execute(statement).scalars().all()
    return events


def get_matches_for_event(session_maker, event_id: int) -> Sequence[Match]:
    """
    Query the DB for all the matches (with their games) recorded for a given event
    """
    with session_maker() as session:
        statement = (
            select(Match)
            .where(Match.event_id == event_id)
            .options(selectinload(Match.games))
        )
        matches = session.execute(statement).unique().scalars().all()
    return matches


def set_event_active(session_maker, event_id: int, active: bool) -> None:
    """
    Update the active flag for a given event
    """
    with session_maker() as session:
        event = session.get(Event, event_id)
        event.active = active
        session.add(event)
        session.commit()


def touch_event_updated_at(session, event_id: int) -> None:
    """
    Bump an event's updated_at to now, within an already-open session. Used to track which
    event was most recently edited (e.g. by recording a match against it)
    """
    event = session.get(Event, event_id)
    event.updated_at = datetime.now()
    session.add(event)


def deactivate_stale_events(session_maker) -> None:
    """
    Among the currently active events, keep only the most recently edited one active and
    deactivate the rest. Intended to be called right before saving, so the saved DB reflects
    a single "current" active event
    """
    with session_maker() as session:
        statement = (
            select(Event)
            .where(Event.active.is_(True))
            .order_by(Event.updated_at.desc())
        )
        active_events = session.execute(statement).scalars().all()
        for event in active_events[1:]:
            event.active = False
            session.add(event)
        session.commit()


def get_archetypes(session_maker) -> Sequence[str]:
    """
    Query the DB for all the archetypes for which a match was recorded
    """
    with session_maker() as session:
        statement = select(Match.archetype).distinct()
        autocomplete_options = session.execute(statement).scalars().all()
    return autocomplete_options


def get_archetype_results(session_maker, archetype) -> ArchetypeData:
    """
    Given a specific archetype (i.e. a label) query the database for the results record and pack
    them nicely in the appropriate dataclass
    """

    with session_maker() as session:
        # match results query
        match_statement = (
            select(Match)
            .where(Match.archetype == archetype)
            .options(selectinload(Match.games))  # type: ignore
        )
        match_query_result = session.execute(match_statement).unique().scalars().all()
        match_data = ResultData(
            played=len(match_query_result), won=get_wins(match_query_result)
        )

        # game results query
        game_statement = (
            select(Game).join(Match).where(Match.archetype == archetype).distinct()
        )
        game_query_result = session.execute(game_statement).scalars().all()

        game_data = ResultData(
            played=len(game_query_result),
            won=len([game for game in game_query_result if game.win]),
        )

        otp_game_data = ResultData(
            played=len([game for game in game_query_result if game.on_the_play]),
            won=len(
                [game for game in game_query_result if game.on_the_play and game.win]
            ),
        )

        otd_game_data = ResultData(
            played=len([game for game in game_query_result if not game.on_the_play]),
            won=len(
                [
                    game
                    for game in game_query_result
                    if not game.on_the_play and game.win
                ]
            ),
        )

    return ArchetypeData(
        matches=match_data,
        games=game_data,
        otp_games=otp_game_data,
        otd_games=otd_game_data,
    )


async def save_db_file(session_maker, *refreshables):
    """
    Deactivate stale active events, then save the current DB to file and refresh the given
    refreshable elements (e.g. generate_event_list)
    """
    if app.native.main_window:
        file_path = await app.native.main_window.create_file_dialog(
            dialog_type=FileDialog.SAVE,
            file_types=("Database Files (*.db)", "All files (*.*)"),
            save_filename="matches.db",
        )
        if file_path:
            final_path = (
                file_path[0] if isinstance(file_path, (list, tuple)) else file_path
            )

            deactivate_stale_events(session_maker)

            # Create a new connection to the destination and use backup to save. The engine is
            # read from the session_maker (rather than passed in separately) so this always
            # saves whatever DB is currently bound, even after a Load rebinds it
            engine = session_maker.kw["bind"]
            raw_con = engine.raw_connection()
            dest_con = sqlite3.connect(final_path)
            with dest_con:
                raw_con.connection.backup(dest_con)
            dest_con.close()

            clear_dirty()
            for refreshable in refreshables:
                refreshable.refresh()
            ui.notify(f"Saved to {final_path}")
        else:
            # We shouldn't ever get here
            raise ValueError("No file path")


async def load_db_file(session, *refreshables):
    """
    Load an existing db and refresh the given refreshable elements (e.g. wr_table,
    generate_event_list)
    """
    if app.native.main_window:
        file_path = await app.native.main_window.create_file_dialog(
            dialog_type=FileDialog.OPEN,
            file_types=("Database Files (*.db)", "All files (*.*)"),
            save_filename="matches.db",
        )

        if file_path:
            # Create a new engine and bind the session to it
            engine = create_engine(f"sqlite:///{file_path[0]}")
            Event.metadata.create_all(engine)
            session.configure(bind=engine)
            clear_dirty()
            for refreshable in refreshables:
                refreshable.refresh()
            ui.notify(f"Loaded from {file_path[0]}")
    return
