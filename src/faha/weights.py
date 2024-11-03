"""Weight of each stat category."""

import typing
from pathlib import Path

import dill

from faha._types import Weights
from faha.league import League
from faha.oauth.client import get_client
from faha.yahoo import Yahoo

STAT_NAMES = {
    "Wins": "W",
    "Save Percentage": "SV%",
    "Saves": "SV",
    "Shutouts": "SHO",
    "Goals": "G",
    "Assists": "A",
    "Plus/Minus": "+/-",
    "Powerplay Points": "PPP",
    "Shots on Goal": "SOG",
    "Faceoffs Won": "FW",
    "Hits": "HIT",
    "Blocks": "BLK",
}


def all_manager_team_stats(league: League) -> dict:
    """Extract the stats of all teams."""
    raw_stats = league.team_stats(league.all_manager_ids)
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


def calculate_stat_weights(all_stats: dict) -> Weights:
    """Calculate the stat weights."""
    stat_sums = {
        category: sum(sorted(values)[-2:]) / 2 for category, values in all_stats.items()
    }
    weights = {
        category: stat_sums["Goals"] / value for category, value in stat_sums.items()
    }
    # explicitly set the weights for difficult stat categories
    weights["Plus/Minus"] = 1 / 3
    # use a function that maps [0.890, 0.940] save percentage range to to [0, 3]
    weights["Save Percentage"] = lambda x: 60 * (x - 0.89)
    weights["Shutouts"] /= 3
    return weights  # type: ignore


def stat_weights_from_yahoo(season: int) -> Weights:
    """Return the weights for a given season accessed from yahoo."""
    oauth = get_client()
    yahoo_agent = Yahoo(oauth)
    lg = League(season, yahoo_agent)
    all_stats = all_manager_team_stats(lg)
    return calculate_stat_weights(all_stats)


def weights_file(season: int) -> Path:
    """Return the weights file."""
    return Path(f"src/faha/data/weights_{season}.pkl")


def write_data(data: typing.Any, file_name: Path) -> None:
    """Write dictionary to disk."""
    with open(file_name, "wb") as file_handle:
        dill.dump(data, file_handle)


def write_weights(weights: Weights, season: int) -> None:
    """Write weights to disk."""
    write_data(weights, weights_file(season))


def stat_weights_from_disk(season: int) -> Weights:
    """Return the weights for a given season, accessed from a saved file on disk."""
    file_name = weights_file(season)
    with open(file_name, "rb") as file_handle:
        return dill.load(file_handle)
