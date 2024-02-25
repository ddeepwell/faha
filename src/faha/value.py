"""Value a player."""

from copy import deepcopy
from typing import Optional

from faha._types import Weights
from faha.players import (
    GoaliePlayer,
    GoalieSeasonStats,
    OffensePlayer,
    OffenseSeasonStats,
    ValuedGoaliePlayer,
    ValuedOffensePlayer,
)


def offense_player_value(stats: OffenseSeasonStats, weights: Weights) -> float:
    """Calculate offensive player value."""
    games_played = stats["Games Played"]
    normalized_stats = {
        name: value / games_played  # type: ignore
        for name, value in stats.items()
        if name != "Games Played"
    }
    return sum(
        value * weights[stat_name]  # type: ignore
        for stat_name, value in normalized_stats.items()
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


def calculate_player_values(
    players: dict[str, OffensePlayer | GoaliePlayer], weights: Weights
) -> dict[str, ValuedOffensePlayer | ValuedGoaliePlayer]:
    """Add the player's values."""
    players_copy = deepcopy(players)
    for player in players_copy.values():
        position = player["Position Type"]
        if position == "P":
            player["Value"] = (  # type: ignore
                offense_player_value(player["Season Stats"], weights)  # type: ignore
            )
        else:
            player["Value"] = (  # type: ignore
                goalie_player_value(player["Season Stats"], weights)  # type: ignore
            )
    return players_copy  # type: ignore


def sort_players(
    players: dict[str, ValuedOffensePlayer | ValuedGoaliePlayer],
    condensed: Optional[bool] = False,
) -> (
    list[tuple[str, ValuedOffensePlayer | ValuedGoaliePlayer]] | list[tuple[str, float]]
):
    """Sort the players by their value."""
    sorted_players = sorted(
        players.items(), key=lambda x: x[1]["Value"], reverse=True  # type: ignore
    )
    if not condensed:
        return sorted_players
    return [(name, info["Value"]) for name, info in sorted_players]
