"""Player methods."""
from datetime import timedelta
from typing import TypedDict

GoalieSeasonStats = TypedDict(
    "GoalieSeasonStats",
    {
        "Minutes": timedelta,
        "Wins": int,
        "Saves": int,
        "Save Percentage": float,
        "Shutouts": int,
    },
)


OffenseSeasonStats = TypedDict(
    "OffenseSeasonStats",
    {
        "Time on Ice": timedelta,
        "Goals": int,
        "Assists": int,
        "Plus/Minus": int,
        "Powerplay Points": int,
        "Shots on Goal": int,
        "Faceoffs Won": int,
        "Hits": int,
        "Blocks": int,
    },
)


Player = TypedDict(
    "Player",
    {
        "Player ID": str,
        "Name": str,
        "NHL Team": str,
        "Positions": list[str],
        "Position Type": str,
    },
)


OffensiveStats = TypedDict("OffensiveStats", {"Season Stats": OffenseSeasonStats})
GoalieStats = TypedDict("GoalieStats", {"Season Stats": GoalieSeasonStats})


class OffensePlayer(Player, OffensiveStats):  # pylint: disable=E0239,E0241
    """Offensive player class."""


class GoaliePlayer(Player, GoalieStats):  # pylint: disable=E0239,E0241
    """Goalie player class."""
