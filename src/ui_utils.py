"""
module to draw the main ui elements
"""

from datetime import datetime
from typing import Any

from nicegui import app, ui

from src.assets.icons import LOCK_CLOSED_ICON, LOCK_OPEN_ICON, PLAY_ICON
from src.data import ArchetypeData, Event, Game, GameResult, Match
from src.utils import (
    get_active_events,
    get_archetype_results,
    get_archetypes,
    get_event_score,
    get_event_types,
    get_events,
    get_matches_for_event,
    is_dirty,
    mark_dirty,
    save_db_file,
    set_event_active,
    toggle_emoji,
    touch_event_updated_at,
)


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

    # Sentinel option value for "no event" - 0 is safe since SQLite autoincrement ids start at 1
    NO_EVENT_VALUE = 0

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
            with ui.row().classes("px-8") as self.archetype_row:
                self._build_archetype_input()

            # Row with a dropdown to tie the match to one of the currently active events
            with ui.row().classes("px-8") as self.event_row:
                self._build_event_select()

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
            event_id=self.event_select.value or None,
            games=games_to_record,
        )

        with self.session_maker() as session:
            session.add(new_match)
            if new_match.event_id is not None:
                touch_event_updated_at(session, new_match.event_id)
            session.commit()

        mark_dirty()
        wr_table.refresh()
        generate_event_list.refresh()

        self.reset_dialog()
        self.close()

    def _build_archetype_input(self):
        """
        Create the archetype input. Called on init and on reset: recreating the element (rather
        than clearing its value) avoids a stale value lingering client-side
        """
        self.archetype_input = ui.input(
            label="Archetype", autocomplete=get_archetypes(self.session_maker)
        )

    def _build_event_select(self):
        """
        Create the event dropdown, populated with the currently active events ordered from most
        to least recently created, followed by a "No event" option, defaulting to the most
        recent event. Called on init, on reset and whenever the dialog is opened so the options
        reflect the latest active events
        """
        options = {
            event.id: event.name
            for event in get_active_events(self.session_maker)
        }
        options[self.NO_EVENT_VALUE] = "No event"
        self.event_select = ui.select(
            options=options,
            value=next(iter(options)),
            label="Event",
        ).classes("w-full event-select")

    def open(self):
        """
        Refresh the event dropdown, so it reflects the latest active events, before opening
        """
        self.event_row.clear()
        with self.event_row:
            self._build_event_select()
        return super().open()

    def reset_dialog(self):
        """
        Called before closing the dialog takes care of resetting each element to the initial state
        """

        for row in self.game_rows:
            row.reset()

        self.archetype_row.clear()
        with self.archetype_row:
            self._build_archetype_input()

    def close_and_reset(self):
        """
        Properly closes the dialog window
        """
        self.reset_dialog()
        self.close()


class NewEventDialog(ui.dialog):
    """
    A class for the dialog window used to enter a new event
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
                ui.label("Create Event").classes("text-h6")

            # Text fields to enter the event name and event type
            with ui.column().classes("px-8") as self.form_column:
                self._build_inputs()

            # A row with a button to record the new event
            with ui.row().classes("w-full justify-center pb-4"):
                ui.button("Create", on_click=self.create)

    def _build_inputs(self):
        """
        Create the name and event type inputs. Called on init and on reset: recreating the
        elements (rather than clearing their value) avoids a stale value lingering client-side
        """
        self.name_input = ui.input(label="Name")
        self.event_type_input = ui.input(
            label="Event Type", autocomplete=get_event_types(self.session_maker)
        )

    def create(self):
        """
        Add the new event to the database
        """

        new_event = Event(
            name=self.name_input.value,
            event_type=self.event_type_input.value,
        )

        with self.session_maker() as session:
            session.add(new_event)
            session.commit()

        mark_dirty()
        generate_event_list.refresh()

        self.reset_dialog()
        self.close()

    def reset_dialog(self):
        """
        Reset the dialog inputs to their initial state
        """
        self.form_column.clear()
        with self.form_column:
            self._build_inputs()

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
    ui.add_head_html("""
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
    """)

    # Add the table element to the UI
    ui.table(columns=columns, rows=rows, row_key="name").classes(
        "sticky-table w-full flex-grow overflow-auto"
    )


def _toggle_event_active(session_maker, event: Event) -> None:
    """
    Flip an event's active flag in the DB and refresh the event list
    """
    set_event_active(session_maker, event.id, not event.active)
    mark_dirty()
    generate_event_list.refresh()


def _event_lock_icon(session_maker, event: Event) -> None:
    """
    Draw a toggleable lock icon reflecting (and controlling) an event's active flag
    """
    icon = LOCK_OPEN_ICON if event.active else LOCK_CLOSED_ICON
    color = "text-gray-400" if event.active else "text-gray-300"
    ui.html(icon, sanitize=False).classes(f"text-2xl cursor-pointer {color}").on(
        "click", lambda: _toggle_event_active(session_maker, event)
    ).tooltip("Active - click to close" if event.active else "Closed")


def _match_sub_row(match: Match) -> None:
    """
    Draw one sub-row for a match: its archetype and its games' results as a sequence of
    smileys, the same way results are entered in the New Match dialog
    """
    with ui.row().classes(
        "w-full items-center justify-between p-2 border-b border-gray-100 last:border-none"
    ):
        ui.label(match.archetype).classes("text-sm text-gray-600")
        with ui.row().classes("gap-1"):
            for game in match.games:
                ui.label("🙂" if game.win else "🙁").classes("text-xl")


@ui.refreshable
def generate_event_list(session_maker):
    """Generates a row, with a sub-row for each of its matches, for each Event in the database."""
    with ui.column().classes("w-full gap-1"):
        for event in get_events(session_maker):
            matches = get_matches_for_event(session_maker, event.id)

            # Always use the same expansion-based header (disabled when there are no matches
            # to show) so the lock icon lines up identically, and at the same height, whether
            # or not a given event's row is expandable
            with ui.row().classes(
                "w-full items-start border-b border-gray-200"
            ):
                # Align the lock icon to the top (items-start) so it stays put when the
                # expansion grows. Quasar's expansion header is a QItem with a fixed 48px
                # (h-12) min-height regardless of content, so centering the icon within a
                # same-height box lines it up with the header text without depending on any
                # measured/guessed offset
                with ui.row().classes("h-12 items-center"):
                    _event_lock_icon(session_maker, event)
                text_color = "text-gray-300" if not event.active else ""
                expansion = ui.expansion(text=event.name).classes(
                    f"flex-grow text-lg font-medium {text_color}"
                )
                if not matches:
                    # Nothing to expand into: hide the arrow (keeping its layout space so the
                    # header still lines up with expandable rows) and block the click so it
                    # can't toggle open on an empty body. Quasar's own 'disable' prop would
                    # also dim the row's text, which we don't want, so block clicks via our
                    # own CSS instead (see the 'event-expansion-empty' rule in main_ui.py)
                    expansion.props('expand-icon-class="invisible"').classes(
                        "event-expansion-empty"
                    )
                # Override the header slot so the score can be right-aligned next to the name
                # (font size/weight/color are inherited from the expansion's own classes above)
                with expansion.add_slot("header"):
                    with ui.row().classes("w-full items-center justify-between"):
                        ui.label(event.name)
                        wins, losses, draws = get_event_score(matches)
                        ui.label(f"{wins}-{losses}-{draws}")
                with expansion:
                    # Container for sub-rows with left padding (pl-8) for indentation
                    with ui.column().classes("w-full pl-8 pb-2 gap-1 bg-gray-50"):
                        for match in matches:
                            _match_sub_row(match)


async def _save_and_quit(session_maker, dialog: ui.dialog) -> None:
    """
    Save (which also deactivates stale active events) and, only if that succeeds, close the app
    """
    try:
        await save_db_file(session_maker, generate_event_list)
    except ValueError:
        # The user cancelled the native save-file dialog - keep the app open
        return
    dialog.close()
    app.shutdown()


def _confirm_quit(session_maker) -> None:
    """
    If there are unsaved changes, ask whether to quit, save and quit, or cancel. Otherwise
    just quit right away
    """
    if not is_dirty():
        app.shutdown()
        return

    with ui.dialog() as dialog, ui.card():
        ui.label("You have unsaved changes.")
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button("Quit", on_click=app.shutdown).props("flat")
            ui.button(
                "Save & Quit",
                on_click=lambda: _save_and_quit(session_maker, dialog),
            )
    dialog.open()


def _traffic_light(color: str, tooltip: str, on_click) -> None:
    """
    Draw one macOS-style traffic-light title bar button
    """
    ui.element("div").classes(
        f"w-3 h-3 rounded-full cursor-pointer {color}"
    ).on("click", on_click).tooltip(tooltip)


def build_title_bar(session_maker, title: str) -> None:
    """
    Draw a custom title bar mimicking macOS, since the window is frameless and this is the
    only way to close/minimize/maximize it. The close (red) button runs the unsaved-changes
    check before quitting; the title area is a pywebview drag region so the window can still
    be moved by dragging it, like a normal title bar
    """
    is_maximized = {"value": False}

    def toggle_maximized() -> None:
        if is_maximized["value"]:
            app.native.main_window.restore()
        else:
            app.native.main_window.maximize()
        is_maximized["value"] = not is_maximized["value"]

    # The page content has a 1rem padding on all sides; cancel it on the top/left/right here
    # so the bar spans true edge-to-edge, like a native title bar. 'self-start' opts this row
    # out of the parent column's own centering, which would otherwise re-center this
    # wider-than-container, negative-margined box and throw the math off
    with ui.row().classes(
        "w-[calc(100%+2rem)] -ml-4 -mt-4 self-start items-center h-8 bg-white "
        "border-b border-gray-300 flex-nowrap"
    ):
        with ui.row().classes("items-center gap-2 pl-3 w-20"):
            _traffic_light(
                "bg-[#ff5f57]", "Close", lambda: _confirm_quit(session_maker)
            )
            _traffic_light(
                "bg-[#febc2e]",
                "Minimize",
                lambda: app.native.main_window.minimize(),
            )
            _traffic_light("bg-[#28c840]", "Maximize", toggle_maximized)
        with ui.row().classes(
            "flex-grow items-center justify-center pywebview-drag-region"
        ):
            ui.label(title).classes("text-sm font-medium text-gray-600 select-none")
        ui.element("div").classes("w-20")
