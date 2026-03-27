"""
Define the DB model
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class Event(SQLModel, table=True):
    """
    An event (e.g., a league, a challenge or an RCQ)
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    event_type: str  # Use your Enum here
    matches: List["Match"] = Relationship(back_populates="event")


class Match(SQLModel, table=True):
    """
    A match in an event
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    archetype: str
    date: str
    is_match_loss: bool
    # event_id: int = Field(foreign_key="event.id")
    event_id: Optional[int] = Field(default=None, foreign_key="event.id")
    event: Event = Relationship(back_populates="matches")
    games: List["Game"] = Relationship(back_populates="match")


class Game(SQLModel, table=True):
    """
    A game in a match
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    on_the_play: bool
    win: bool
    match_id: int = Field(foreign_key="match.id")
    match: Match = Relationship(back_populates="games")


class GameResult(Enum):
    """
    Enum for game state
    """

    WIN = 1
    LOSS = -1
    UNSET = 0


@dataclass
class GameStats:
    games_played: int
    games_won: int
    on_the_play_games_played: int
    on_the_play_games_won: int
    on_the_draw_games_played: int
    on_the_draw_games_won: int

    @property
    def otp_win_rate(self) -> str:
        return (
            f"{(self.on_the_play_games_won/self.on_the_play_games_played):.3f}"
            if self.on_the_play_games_played
            else "N/A"
        )

    @property
    def otd_win_rate(self) -> str:
        return (
            f"{(self.on_the_draw_games_won/self.on_the_draw_games_played):.3f}"
            if self.on_the_draw_games_played
            else "N/A"
        )
