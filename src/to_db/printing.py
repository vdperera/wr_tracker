from typing import Optional

from sqlmodel import Field, Session, SQLModel, create_engine, select, text
from tabulate import tabulate


# 1. Define your Models
class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    headquarters: str


class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    secret_name: str
    age: Optional[int] = None
    team_id: Optional[int] = Field(default=None, foreign_key="team.id")


# 2. Setup the Engine (using SQLite in-memory for this example)
sqlite_url = "sqlite://"
engine = create_engine(sqlite_url)

# 3. Create the actual tables in the database
SQLModel.metadata.create_all(engine)


# 4. Fill the tables with data
def create_data():
    with Session(engine) as session:
        team_z = Team(name="Z-Force", headquarters="Galaxy Tower")
        hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
        hero_2 = Hero(name="Spider-Boy", secret_name="Pedro Parqueador", age=18)

        session.add(team_z)
        session.add(hero_1)
        session.add(hero_2)
        session.commit()


# 5. Pretty-print all tables
def print_all_tables():

    with Session(engine) as session:
        for table_name, table_obj in SQLModel.metadata.tables.items():
            print(f"\n--- TABLE: {table_name.upper()} ---")

            # 1. Use .mappings() to ensure results are returned as dictionary-like objects
            statement = select(table_obj)
            results = session.execute(statement).mappings().all()

            if not results:
                print("No data available.")
                continue

            # 2. Convert the mapping objects to plain dictionaries for tabulate
            data = [dict(row) for row in results]

            print(tabulate(data, headers="keys", tablefmt="grid"))


if __name__ == "__main__":
    create_data()
    print_all_tables()
