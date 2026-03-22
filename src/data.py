"""
Defines dataclasses used to record games, matches and events results
"""

from __future__ import annotations
import weakref
from dataclasses import dataclass, field
from typing import Optional
from mashumaro.mixins.json import DataClassJSONMixin


@dataclass
class Game(DataClassJSONMixin):
    """
    A single game in a Match.
    """

    play: bool
    win: bool
    parent_match_ref: Optional[weakref.ReferenceType[Match]] = field(
        default=None,
        repr=False,
        init=False,
        metadata={"serialize": "omit", "deserialize": "omit"},
    )

    @property
    def parent_match(self) -> Optional[Match]:
        """docstring"""
        return self.parent_match_ref() if self.parent_match_ref else None


@dataclass
class Match(DataClassJSONMixin):
    """
    A Match, a collection of Games and additional info (e.g. archetype, date).
    """

    archetype: str
    date: str
    is_match_loss: bool = False
    games: list[Game] = field(default_factory=list)

    @classmethod
    def __post_deserialize__(cls, obj: Match) -> Match:
        """
        Mashumaro calls this after the object is created from JSON.
        We use it to stitch the parent back into the children.
        """
        for game in obj.games:
            game.parent_match_ref = weakref.ref(obj)
        return obj

    def add_game(self, game: Game) -> None:
        """Programmatic way to create and link a child."""
        # Manually set the weak reference
        game.parent_match_ref = weakref.ref(self)
        self.games.append(game)

    def is_win(self) -> bool:
        """Check if the match was won"""
        if self.is_match_loss:
            return False
        total = 0
        for game in self.games:
            if game.win:
                total += 1
            else:
                total -= 1

        return total > 0


class MatchUp:
    """
    A class to represent a match up and compute win rates. Rather than storing each individual match
    the class tallies the total matches played and how many where won
    """

    def __init__(self, archetype):
        self.archetype = archetype
        self.total = 0.0
        self.win = 0.0

    def win_rate(self) -> float:
        """
        Compute the win rate for a given MatchUp
        """

        return self.win / self.total

    def update(self, new_match: Match) -> None:
        """
        Update the MatchUp with the resul from a new Match
        """

        assert self.archetype == new_match.archetype
        self.total += 1.0
        self.win += new_match.is_win()
