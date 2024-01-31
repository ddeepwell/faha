"""Weight of each stat category."""
from typing import Callable, TypedDict

from faha.league import League

Weights = TypedDict(
    "Weights",
    {
        "Goals": float,
        "Assists": float,
        "Plus/Minus": float,
        "Powerplay Points": float,
        "Shots on Goal": float,
        "Faceoffs Won": float,
        "Hits": float,
        "Blocks": float,
        "Wins": float,
        "Saves": float,
        "Save Percentage": Callable[[float], float],
        "Shutouts": float,
    },
)


def all_manager_team_stats(league: League) -> dict:
    """Extract the stats of all teams."""
    manager_ids = [str(mngr) for mngr in range(1, league.num_managers + 1)]
    raw_stats = league.team_stats(manager_ids)
    return {
        category: [
            _convert(team_stats[category], category)
            for team_stats in raw_stats.values()
        ]
        for category in league.stat_categories().values()
    }


def _convert(value: str, category: str) -> float | int:
    """Convert a string to the correct type."""
    if category == "Save Percentage":
        return float(value)
    return int(value)


def stat_weights(all_stats: dict) -> Weights:
    """Return the stat weights."""
    stat_sums = {category: sum(values) for category, values in all_stats.items()}
    weights = {
        category: stat_sums["Goals"] / value for category, value in stat_sums.items()
    }
    # explicitly set the weights for difficult stat categories
    weights["Plus/Minus"] = 1 / 3
    # use a function that maps [0.890, 0.940] save percentage range to to [0, 3]
    weights["Save Percentage"] = lambda x: 60 * (x - 0.89)
    weights["Shutouts"] /= 3
    return weights  # type: ignore
