"""
module to draw the main ui elements
"""

from datetime import datetime
from typing import Any

from nicegui import ui

from src.assets.icons import PLAY_ICON
from src.data import ArchetypeData, Game, GameResult, Match
from src.utils import get_archetype_results, get_archetypes, toggle_emoji


class ResultRow:
    """
    One row, in the game grid
    """

    def __init__(self, row_label: str):
        ui.label(row_label).classes("text-2xl -mt-3")
        self.otp_checkbox = ui.checkbox().classes("text-3xl -mt-3")
        self.win_button = ui.label("🙂").classes(
            "text-3xl cursor-pointer transition-all grayscale opacity-50 -mt-3"
        )
        self.loss_button = ui.label("🙁").classes(
            "text-3xl cursor-pointer transition-all grayscale opacity-50 -mt-3"
        )
        self.win_button.on(
            "click",
            lambda: toggle_emoji(self.win_button, self.loss_button),
        )
        self.loss_button.on(
            "click",
            lambda: toggle_emoji(self.loss_button, self.win_button),
        )

    @property
    def is_set(self) -> bool:
        """
        Check if one of the two button was set
        """
        return ("grayscale" not in self.win_button.classes) or (
            "grayscale" not in self.loss_button.classes
        )

    @property
    def result(self) -> GameResult:
        """
        Check the state of the two button to see if the game was a win, a loss or if no result was
        entered (UNSET)
        """

        if not self.is_set:
            return GameResult.UNSET

        if "grayscale" not in self.win_button.classes:
            return GameResult.WIN

        return GameResult.LOSS

    def reset(self):
        """
        Reset the row, set the buttons to greyscale and the checkbox to un-marked
        """
        if "grayscale" not in self.win_button.classes:
            self.win_button.classes("grayscale opacity-50")
        if "grayscale" not in self.loss_button.classes:
            self.loss_button.classes("grayscale opacity-50")
        self.otp_checkbox.set_value(False)


# The class needs to have many attributes as each refers to a ui element
class NewMatchDialog(ui.dialog):  # pylint: disable=too-many-instance-attributes
    """
    A class for the dialog window used to enter new results. Used to store and proces different
    elements of the ui
    """

    def __init__(self, session_maker):
        super().__init__()
        self.session_maker = session_maker

        # Set p-0 for a tight layout
        with self, ui.card().classes("p-0"):

            # Add a close button to the top right of the dialog box
            with ui.row().classes("items-center justify-end w-full"):
                ui.button(icon="close", on_click=self.close_and_reset).props(
                    "flat round dense"
                )

            # Initial row with the dialog title as a label
            with ui.row().classes("w-full items-center justify-between px-8 -mt-4"):
                ui.label("Enter Result").classes("text-h6")

            # Second row to with an auto-complete text input to add the archetype value
            with ui.row().classes("px-8"):
                self.archetype_input = ui.input(
                    label="Archetype", autocomplete=get_archetypes(self.session_maker)
                )

            # A 4x4 Grid to enter the match result. A first row to set up the table and three
            # additional rows one for each game.
            with ui.grid(columns=4).classes("items-center justify-items-center px-8"):

                # Row 1 - just the 'on the play' icon and 3 placeholders
                ui.label("")
                ui.html(PLAY_ICON, sanitize=False).classes("text-3xl").tooltip(
                    '"On the play" checkbox'
                )
                ui.label("")
                ui.label("")

                # Remaining rows
                g1_row = ResultRow("G1")
                g2_row = ResultRow("G2")
                g3_row = ResultRow("G3")

                self.game_rows = [g1_row, g2_row, g3_row]

            # One more row with a button to record the match result
            with ui.row().classes("w-full justify-center"):
                ui.button("Record", on_click=self.record)

            # Last row with a checkbox to track match losses (e.g., time out on mtgo)
            ui.label("")
            with ui.row().classes("justify-end items-center gap-2 w-full"):
                ui.label("Match loss")
                self.match_loss_cb = ui.checkbox()

    def _validate_result_rows_state(self) -> bool:
        """
        Helper function to take the three ResultRow and make sure they are set correctly (e.g.,
        we cannot have the first and third set but not the second)
        """

        valid_game_states = [[1, 0, 0], [1, 1, 0], [1, 1, 1]]
        return [row.is_set for row in self.game_rows] in valid_game_states

    def _validate_result_rows_value(self) -> bool:
        """
        Helper function to check the three ResultRow provide a valid result (e.g. a match can be
        won 2-0 but cannot be lost 0-3)
        """

        valid_game_results = [
            [1, -1, 1],
            [-1, 1, 1],
            [1, -1, -1],
            [1, 1, 0],
            [-1, -1, 0],
            [-1, 1, -1],
            [1, 0, 0],
            [-1, 0, 0],
            [1, -1, 0],
            [-1, 1, 0],
        ]
        return [row.result.value for row in self.game_rows] in valid_game_results

    def _validate(self) -> bool:
        """
        Validate the input dialg state. If valid return True else False
        """
        validation = True

        # Check if the archetype was entered
        if self.archetype_input.value == "":
            ui.notify("Missing Archetype!", type="warning")
            validation = False

        if not self._validate_result_rows_state():
            ui.notify("Missing game result(s)!", type="warning")
            validation = False

        if not self._validate_result_rows_value():
            ui.notify("Invalid Result", type="warning")
            validation = False

        return validation

    def record(self):
        """
        Record the result of a game. First validate the user input the add it to the data being
        saved
        """

        validation = self._validate()
        if not validation:
            return

        games_to_record = [
            Game(
                on_the_play=row.otp_checkbox.value,
                win=row.result.value == 1,
            )
            for row in self.game_rows
            if row.is_set
        ]

        new_match = Match(
            archetype=self.archetype_input.value.lower(),
            date=datetime.now().isoformat(),
            is_match_loss=self.match_loss_cb.value,
            games=games_to_record,
        )

        with self.session_maker() as session:
            session.add(new_match)
            session.commit()

        self.archetype_input.set_autocomplete(get_archetypes(self.session_maker))
        wr_table.refresh()

        self.reset_dialog()
        self.close()

    def reset_dialog(self):
        """
        Called before closing the dialog takes care of resetting each element to the initial state
        """

        for row in self.game_rows:
            row.reset()

        self.archetype_input.set_value("")

    def close_and_reset(self):
        """
        Properly closes the dialog window
        """
        self.reset_dialog()
        self.close()


@ui.refreshable
def wr_table(session) -> None:
    """
    Draws the win rate table starting from the raw data
    """

    # Prepare the rows and column lists
    rows: list[dict[str, Any]] = []
    columns: list[dict[str, Any]] = [
        {
            "name": "archetype",
            "label": "Archetype",
            "field": "archetype",
            "required": True,
            "align": "left",
            "sortable": True,
        },
        {
            "name": "match_win_rate",
            "label": "Match Win Rate",
            "field": "match_win_rate",
            "align": "center",
            "sortable": True,
        },
        {
            "name": "total_matches",
            "label": "Total Matches",
            "field": "total_matches",
            "align": "center",
            "sortable": True,
        },
        {
            "name": "game_win_rate",
            "label": "Game Win Rate",
            "field": "game_win_rate",
            "align": "center",
        },
        {
            "name": "total_games",
            "label": "Total Games",
            "field": "total_games",
            "align": "center",
        },
        {
            "name": "otp_game_win_rate",
            "label": "On the Play Game Win Rate",
            "field": "otp_game_win_rate",
            "align": "center",
        },
        {
            "name": "otd_game_win_rate",
            "label": "On the Draw Game Win Rate",
            "field": "otd_game_win_rate",
            "align": "center",
        },
    ]

    # Get all the archetypes from autocomplete
    autocomplete_options = get_archetypes(session)

    # For each matchup get win rate and total matches
    grand_total = ArchetypeData()

    for archetype in autocomplete_options:

        results = get_archetype_results(session, archetype)
        grand_total += results

        # Add the values to rows
        rows.append(
            {
                "archetype": archetype,
                "match_win_rate": results.matches.win_rate,
                "total_matches": results.matches.played,
                "game_win_rate": results.games.win_rate,
                "otp_game_win_rate": results.otp_games.win_rate,
                "otd_game_win_rate": results.otd_games.win_rate,
                "total_games": results.games.played,
            }
        )

    rows.append(
        {
            "archetype": "Total",
            "match_win_rate": grand_total.matches.win_rate,
            "total_matches": grand_total.matches.played,
            "game_win_rate": grand_total.games.win_rate,
            "otp_game_win_rate": grand_total.otp_games.win_rate,
            "otd_game_win_rate": grand_total.otd_games.win_rate,
            "total_games": grand_total.games.played,
        }
    )

    # CSS needed to style (bold and sticky) the first and last rows
    ui.add_head_html(
        """
        <style>
            /* Sticky Header */
            .sticky-table thead tr:first-child th {
                background-color: white;
                position: sticky;
                top: 0;
                z-index: 20;
            }
            /* Sticky & Bold Last Row */
            .sticky-table tbody tr:last-child td {
                background-color: #f8f8f8; /* Light gray to distinguish it */
                position: sticky;
                bottom: 0;
                z-index: 10;
                font-weight: bold;
                border-top: 2px solid #ddd;
            }
        </style>
    """
    )

    # Add the table element to the UI
    ui.table(columns=columns, rows=rows, row_key="name").classes(
        "sticky-table w-full flex-grow overflow-auto"
    )
