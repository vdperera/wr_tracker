"""
Utility function for the main ui
"""

import sqlite3
from typing import Sequence

from nicegui import app, ui
from sqlalchemy.orm import selectinload
from sqlmodel import create_engine, select
from webview import FileDialog

from src.data import ArchetypeData, Event, Game, Match, ResultData


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


def get_archetypes(Session) -> Sequence[str]:
    """
    Query the DB for all the archetypes for which a match was recorded
    """
    with Session() as session:
        statement = select(Match.archetype).distinct()
        autocomplete_options = session.execute(statement).scalars().all()
    return autocomplete_options


def get_archetype_results(Session, archetype) -> ArchetypeData:
    """
    Given a specific archetype (i.e. a label) query the database for the results record and pack
    them nicely in the appropriate dataclass
    """

    with Session() as session:
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


async def native_save(current_engine):
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

            raw_con = current_engine.raw_connection()

            # Create a new connection to the destination file
            dest_con = sqlite3.connect(final_path)

            # Use the backup API to copy everything
            with dest_con:
                raw_con.connection.backup(dest_con)

            dest_con.close()
            ui.notify(f"Saved to {final_path}")
        else:
            raise ValueError("No file path")


async def load_db_file(session, generate_wr_table):
    if app.native.main_window:
        file_path = await app.native.main_window.create_file_dialog(
            dialog_type=FileDialog.OPEN,
            file_types=("Database Files (*.db)", "All files (*.*)"),
            save_filename="matches.db",
        )
        engine = create_engine(f"sqlite:///{file_path[0]}")
        Event.metadata.create_all(engine)
        session.configure(bind=engine)
        generate_wr_table.refresh()
        print(file_path)
    return
