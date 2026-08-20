"""
main ui file for tracking win rate. Loads data from json, create report table and handles the module
to insert new data.
"""

from nicegui import Client, ui
from sqlalchemy.orm import sessionmaker
from sqlmodel import create_engine

from src.assets.icons import TAB_ICON2
from src.data import Event
from src.ui_utils import NewMatchDialog, generate_event_list, wr_table
from src.utils import load_db_file, save_db_file


@ui.page("/")
def main_page(client: Client):
    """
    Define the ui main page
    """
    # Setup the DB
    engine = create_engine("sqlite://")
    Event.metadata.create_all(engine)
    session_maker = sessionmaker(bind=engine)

    # Setup the page, strip all default NiceGUI/Quasar padding and force the actual window body
    # to never scroll
    client.content.classes(remove="q-pa-md")
    ui.query("html").style("height: 100vh; overflow: hidden;")
    ui.query("body").style("height: 100vh; overflow: hidden;")

    ui.add_head_html("""
<style>
    /* Target the text label inside the tab */
    .q-tab__label {
        font-size: clamp(12px, 1.2vw, 18px) !important;
    }
    /* Target the icon inside the tab */
    .q-tab__icon {
        font-size: clamp(18px, 2.5vw, 32px) !important;
    }
    /* Optional: Ensure the tab itself has enough padding to scale */
    .q-tab {
        padding: 0.5vw !important;
        min-height: 40px !important;
    }
</style>
""")

    # Setup the main UI elements, buttons and table
    with ui.column().classes("w-full items-center"):
        with (
            ui.splitter(value=10)
            .props("horizontal")
            .classes("w-full h-screen") as splitter
        ):

            with splitter.before:
                # with ui.tabs().props("vertical").classes("w-full") as tabs:
                with (
                    ui.tabs().props("horizontal").classes("w-full text-[1.5vw]") as tabs
                ):
                    # tabs.style("font-size: clamp(14px, 2vw, 24px)")
                    mail = ui.tab("Win Rate", icon="mail")
                    alarm = ui.tab("Events", icon="alarm")
            with splitter.after:
                with (
                    ui.tab_panels(tabs, value=mail)
                    .props("vertical")
                    .classes("size-full")
                ):
                    with ui.tab_panel(mail):
                        with ui.column().classes(
                            "items-end w-full h-[calc(100vh-50px)] p-4 overflow-hidden"
                        ):
                            new_match_dialog = NewMatchDialog(session_maker)
                            with ui.row().classes("w-full"):
                                ui.button(
                                    "Load",
                                    icon="folder_open",
                                    on_click=lambda: load_db_file(
                                        session_maker, wr_table
                                    ),
                                )
                                ui.button(
                                    "Save",
                                    icon="save",
                                    on_click=lambda: save_db_file(engine),
                                )
                                ui.space()
                                ui.button(
                                    "New Match", on_click=new_match_dialog.open
                                ).classes("self-end")

                            wr_table(session_maker)
                    with ui.tab_panel(alarm):
                        generate_event_list()

    with ui.footer(value=True).classes("py-1 bg-gray-800 text-white justify-center"):
        ui.label("© 2026 Vittorio Perera").classes("text-xs")


ui.run(title="Win Rate Tracker", favicon=TAB_ICON2, native=True)
