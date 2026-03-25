from datetime import datetime
from random import choice
from typing import Sequence

from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import Session, SQLModel, create_engine, select, text
from tabulate import tabulate

from src.to_db.data import Event, Game, Match


def print_all_tables(metadata):  # Accept metadata as an argument
    from sqlmodel import create_engine

    engine = create_engine("sqlite:///matches.db")

    with Session(engine) as session:
        # Use the specific metadata object passed in
        for table_name, table_obj in metadata.tables.items():
            print(f"\n--- TABLE: {table_name.upper()} ---")

            # Use session.execute().mappings() to get dictionaries
            results = session.execute(select(table_obj)).mappings().all()

            if not results:
                print("No data available.")
                continue

            data = [dict(row) for row in results]
            print(tabulate(data, headers="keys", tablefmt="grid"))


match_results = [[1, 1], [1, 0, 1], [0, 1, 1], [0, 0], [0, 1, 0], [1, 0, 0]]
decks = ["boros", "jeskay blink", "esper blink", "titan", "neoform"]

engine = create_engine("sqlite:///matches.db")


def init_db():
    Event.metadata.create_all(engine)


def generate_data(events: int, matches_per_event: int):
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


if __name__ == "__main__":
    init_db()  # Create the tables
    generate_data(2, 5)
    print_all_tables(Event.metadata)

    with Session(engine) as session:

        statement = select(Match.archetype).distinct()

        # 2. Execute and get the list
        results = session.exec(statement).all()

        for archetype in results:
            statement2 = (
                select(Match)
                .where(Match.archetype == archetype)
                .options(selectinload(Match.games))  # type: ignore
            )

            match_up = session.exec(statement2).unique().all()
            total = len(match_up)
            wins = get_wins(match_up)
            if total:
                print(f"{archetype}\t{total}\t{(wins/total):.3f}")
            else:
                print(f"{archetype}\t{0}\t{0:.3f}")
