"""Value a player."""
from faha.players import GoalieSeasonStats, OffenseSeasonStats
from faha.weights import Weights


def offense_player_value(stats: OffenseSeasonStats, weights: dict[str, float]) -> float:
    """Calculate offensive player value."""
    games_played = stats["Games Played"]
    normalized_stats = {
        name: value / games_played  # type: ignore
        for name, value in stats.items()
        if name != "Games Played"
    }
    return sum(
        value * weights[stat_name] for stat_name, value in normalized_stats.items()
    )


def goalie_player_value(stats: GoalieSeasonStats, weights: Weights) -> float:
    """Calculate goalie player value."""
    games_started = stats["Games Started"]
    normalized_stats = {
        name: value / games_started  # type: ignore
        for name, value in stats.items()
        if name not in ["Games Started", "Save Percentage"]
    }
    save_percentage_value = weights["Save Percentage"](stats["Save Percentage"])
    return save_percentage_value + sum(  # type: ignore
        value * weights[stat_name]  # type: ignore
        for stat_name, value in normalized_stats.items()
    )
