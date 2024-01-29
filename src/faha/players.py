"""Player methods."""
from datetime import timedelta
from typing import TypedDict


class GoalieSeasonStats(TypedDict):
    """Season stats class for goalies."""

    minutes: timedelta
    wins: int
    saves: int
    save_percentage: float
    shutouts: int


class OffenseSeasonStats(TypedDict):
    """Season stats class for goalies."""

    time_on_ice: timedelta
    goals: int
    assists: int
    plus_minus: int
    powerplay_points: int
    shots_on_goal: int
    faceoffs_won: int
    hits: int
    blocks: int


class Player(TypedDict):
    """Player class."""

    player_id: str
    name: str
    nhl_team: str
    positions: list[str]
    position_type: str
    # primary_position: str


class OffensePlayer(Player):
    """Offensive player class."""

    season_stats: OffenseSeasonStats


class GoaliePlayer(Player):
    """Goalie player class."""

    season_stats: GoalieSeasonStats
