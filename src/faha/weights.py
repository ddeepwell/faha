"""Weight of each stat category."""

from faha._types import Weights
from faha.league import League
from faha.oauth.client import get_client
from faha.yahoo import Yahoo


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


def stat_weights(all_stats: dict) -> Weights:
    """Return the stat weights."""
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


def stat_weights_for_season(season: int) -> Weights:
    """Return the weights for a given season."""
    oauth = get_client()
    yahoo_agent = Yahoo(oauth)
    lg = League(season, yahoo_agent)
    all_stats = all_manager_team_stats(lg)
    return stat_weights(all_stats)
