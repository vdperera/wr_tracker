"""
main ui file for tracking win rate. Loads data from json, create report table and handles the module
to insert new data.
"""

# pylint: disable=protected-access
# we need to access the ._classes attribute of many elements either to check their state or to
# change their values

import json
from datetime import datetime
from enum import Enum
from typing import Any, List

from mashumaro.codecs.json import JSONDecoder, JSONEncoder
from nicegui import ui

from src.assets.icons import play_icon, tab_icon2
from src.data import Game, Match, MatchUp
from src.utils import toggle_emoji

encoder = JSONEncoder(List[Match])
decoder = JSONDecoder(List[Match])

try:
    with open("results.json", "r", encoding="utf-8") as in_file:
        match_data = in_file.read()
        ALL_MATCHES = decoder.decode(match_data)
except (FileNotFoundError, json.JSONDecodeError) as e:
    ALL_MATCHES = []

autocomplete_options = list({match.archetype.lower() for match in ALL_MATCHES})


class GameResult(Enum):
    """
    Enum for game state
    """

    WIN = 1
    LOSS = -1
    UNSET = 0


class GameResultButtonPair:
    """
    Class to quickly access the state of a pair of button used to enter the result of a game
    """

    def __init__(self, win_button, loss_button):
        self.win = win_button
        self.loss = loss_button

    @property
    def is_set(self) -> bool:
        """
        Check if one of the two button was set
        """
        return ("grayscale" not in self.win._classes) or (
            "grayscale" not in self.loss._classes
        )

    @property
    def result(self) -> GameResult:
        """
        Check the state of the two button to see if the game was a win, a loss or if no result was
        entered (UNSET)
        """

        if not self.is_set:
            return GameResult.UNSET

        if "grayscale" not in self.win._classes:
            return GameResult.WIN

        return GameResult.LOSS


# The class needs to have many attributes as each refers to a ui element
class NewMatchDialog(ui.dialog):  # pylint: disable=too-many-instance-attributes
    """
    A class for the dialog window used to enter new results. Used to store and proces different
    elements of the ui
    """

    def __init__(self):
        super().__init__()
        with self, ui.card().classes("p-12"):
            with ui.row().classes("absolute top-2 right-2 items-center gap-2"):
                ui.button(icon="close", on_click=self.close_and_reset).props(
                    "flat round dense"
                )
            with ui.row().classes("w-full items-center justify-between"):
                ui.label("Enter Result").classes("text-h6")
            with ui.row():
                self.archetype_input = ui.input(
                    label="Archetype", autocomplete=autocomplete_options
                )

            with ui.grid(columns=4).classes("items-center justify-items-center"):

                # Row 1 - just the 'on the play' icon and 3 placeholders
                ui.label("")
                ui.html(play_icon, sanitize=False).classes("text-3xl").tooltip(
                    '"On the play" checkbox'
                )
                ui.label("")
                ui.label("")

                # Row 2 - game 1
                ui.label("G1").classes("text-2xl -mt-3")
                self.checkbox1 = ui.checkbox().classes("text-3xl -mt-3")
                self.g1_win = ui.label("🙂").classes(
                    "text-3xl cursor-pointer transition-all grayscale opacity-50 -mt-3"
                )
                self.g1_loss = ui.label("🙁").classes(
                    "text-3xl cursor-pointer transition-all grayscale opacity-50 -mt-3"
                )
                self.g1_win.on("click", lambda: toggle_emoji(self.g1_win, self.g1_loss))
                self.g1_loss.on(
                    "click", lambda: toggle_emoji(self.g1_loss, self.g1_win)
                )

                # Row 3 - game 2
                ui.label("G2").classes("text-2xl")
                self.checkbox2 = ui.checkbox().classes("text-3xl")
                self.g2_win = ui.label("🙂").classes(
                    "text-3xl cursor-pointer transition-all grayscale opacity-50"
                )
                self.g2_loss = ui.label("🙁").classes(
                    "text-3xl cursor-pointer transition-all grayscale opacity-50"
                )
                self.g2_win.on("click", lambda: toggle_emoji(self.g2_win, self.g2_loss))
                self.g2_loss.on(
                    "click", lambda: toggle_emoji(self.g2_loss, self.g2_win)
                )

                # Row 4 - game 3
                ui.label("G3").classes("text-2xl")
                self.checkbox3 = ui.checkbox().classes("text-3xl")
                self.g3_win = ui.label("🙂").classes(
                    "text-3xl cursor-pointer transition-all grayscale opacity-50"
                )
                self.g3_loss = ui.label("🙁").classes(
                    "text-3xl cursor-pointer transition-all grayscale opacity-50"
                )
                self.g3_win.on("click", lambda: toggle_emoji(self.g3_win, self.g3_loss))
                self.g3_loss.on(
                    "click", lambda: toggle_emoji(self.g3_loss, self.g3_win)
                )

            with ui.row().classes("w-full justify-center"):
                ui.button("Record", on_click=self.record)

            ui.label("")
            with ui.row().classes("absolute bottom-2 right-2 items-center gap-2"):
                ui.label("Match loss")
                self.match_loss_cb = ui.checkbox()

    def _validate(self) -> bool:
        """
        Validate the input dialg state. if valid return True else False
        """
        validation = True

        # Check if the archetype was entered
        if self.archetype_input.value == "":
            ui.notify("Missing Archetype!", type="warning")
            validation = False

        # Check if all games are set properly
        g1 = GameResultButtonPair(self.g1_win, self.g1_loss)
        g2 = GameResultButtonPair(self.g2_win, self.g2_loss)
        g3 = GameResultButtonPair(self.g3_win, self.g3_loss)
        valid_game_states = [[1, 0, 0], [1, 1, 0], [1, 1, 1]]
        if [g1.is_set, g2.is_set, g3.is_set] not in valid_game_states:
            ui.notify("Missing game result(s)!", type="warning")
            validation = False

        # Check if the game result is valid (e.g. 2-1 is valid but 0-3 is not)
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
        actual_result = [g1.result.value, g2.result.value, g3.result.value]
        if actual_result not in valid_game_results:
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

        g1 = GameResultButtonPair(self.g1_win, self.g1_loss)
        g2 = GameResultButtonPair(self.g2_win, self.g2_loss)
        g3 = GameResultButtonPair(self.g3_win, self.g3_loss)

        new_match = Match(
            self.archetype_input.value.lower(),
            datetime.now().isoformat(),
            self.match_loss_cb.value,
            [],
        )
        for game_result, on_the_play in [
            (g1, self.checkbox1.value),
            (g2, self.checkbox2.value),
            (g3, self.checkbox3.value),
        ]:
            if game_result.is_set:
                new_match.add_game(Game(on_the_play, game_result.result.value == 1))

        ALL_MATCHES.append(new_match)
        global autocomplete_options  # pylint:disable=global-statement
        autocomplete_options = list({match.archetype.lower() for match in ALL_MATCHES})
        generate_wr_table.refresh()

        with open("results.json", "w", encoding="utf-8") as out_file:
            out_file.write(encoder.encode(ALL_MATCHES))

        # dump data
        self.reset_dialog()
        self.close()

    def reset_dialog(self):
        """
        Called before closing the dialog takes care of resetting each element to the initial state
        """

        if "grayscale" not in self.g1_win._classes:
            self.g1_win.classes("grayscale opacity-50")
        if "grayscale" not in self.g1_loss._classes:
            self.g1_loss.classes("grayscale opacity-50")
        if "grayscale" not in self.g2_win._classes:
            self.g2_win.classes("grayscale opacity-50")
        if "grayscale" not in self.g2_loss._classes:
            self.g2_loss.classes("grayscale opacity-50")
        if "grayscale" not in self.g3_win._classes:
            self.g3_win.classes("grayscale opacity-50")
        if "grayscale" not in self.g3_loss._classes:
            self.g3_loss.classes("grayscale opacity-50")

        self.archetype_input.set_value("")
        self.checkbox1.set_value(False)
        self.checkbox2.set_value(False)
        self.checkbox3.set_value(False)

    def close_and_reset(self):
        """
        Properly closes the dialog window
        """
        self.reset_dialog()
        self.close()


@ui.refreshable
def generate_wr_table() -> None:
    """
    Draws the win rate table starting from the raw data
    """

    data: dict[str, MatchUp] = {}
    for match in ALL_MATCHES:
        if match.archetype not in data:
            match_up = MatchUp(match.archetype)
            data[match.archetype] = match_up
        if match.archetype == "Boros":
            print(match)
        data[match.archetype].update(match)
    columns = [
        {
            "name": "archetype",
            "label": "Archetype",
            "field": "archetype",
            "required": True,
            "align": "left",
            "sortable": True,
        },
        {
            "name": "win_rate",
            "label": "Match Win Rate",
            "field": "win_rate",
            "sortable": True,
        },
    ]
    rows: list[dict[str, Any]] = [
        {"archetype": key, "win_rate": value.win_rate()} for key, value in data.items()
    ]
    ui.table(columns=columns, rows=rows, row_key="name")


generate_wr_table()

new_match_dialog = NewMatchDialog()
ui.button("New Match", on_click=new_match_dialog.open)

ui.run(title="Win Rate Tracker", favicon=tab_icon2)
