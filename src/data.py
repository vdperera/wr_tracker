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
class ResultData:
    """
    Generic data class to store result whether it's a game, a match or else
    """

    played: int = 0
    won: int = 0

    @property
    def win_rate(self) -> str:
        """
        Compute the win rate
        """
        return f"{(self.won/self.played):.3f}" if self.played else "N/A"

    def __add__(self, other):
        if not isinstance(other, ResultData):
            return NotImplemented
        return ResultData(self.played + other.played, self.won + other.won)


@dataclass
class ArchetypeData:
    """
    Dataclass to store, in one object, all the stats we plan to show in the table
    """

    matches: ResultData = ResultData(0, 0)
    games: ResultData = ResultData(0, 0)
    otp_games: ResultData = ResultData(0, 0)
    otd_games: ResultData = ResultData(0, 0)

    def __add__(self, other):
        if not isinstance(other, ArchetypeData):
            return NotImplemented
        return ArchetypeData(
            self.matches + other.matches,
            self.games + other.games,
            self.otp_games + other.otp_games,
            self.otd_games + other.otd_games,
        )
