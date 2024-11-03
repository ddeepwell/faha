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


def offense_player_stat_values(
    stats: OffenseSeasonStats, weights: Weights, sort: bool = False
) -> dict[str, float]:
    """Calculate offensive player value."""
    games_played = stats["Games Played"]
    if games_played == 0:
        return dict({name: 0 for name in stats.keys() if name != "Games Played"})
    normalized_stats = {
        name: value / games_played  # type: ignore
        for name, value in stats.items()
        if name != "Games Played"
    }
    values = [
        (stat_name, value * weights[stat_name])  # type: ignore
        for stat_name, value in normalized_stats.items()
    ]
    if sort:
        return dict(sorted(values, key=lambda x: x[1], reverse=True))
    return dict(values)


def offense_player_value(stats: OffenseSeasonStats, weights: Weights) -> float:
    """Calculate offensive player value."""
    return sum(offense_player_stat_values(stats, weights).values())


def goalie_player_stat_values(
    stats: GoalieSeasonStats, weights: Weights, sort: bool = False
) -> dict[str, float]:
    """Calculate goalie player value."""
    games_started = stats["Games Started"]
    normalized_stats = {
        name: value / games_started  # type: ignore
        for name, value in stats.items()
        if name not in ["Games Started", "Save Percentage"]
    }
    save_percentage_value = weights["Save Percentage"](stats["Save Percentage"])
    values = [("Save Percentage", save_percentage_value)] + [
        (stat_name, value * weights[stat_name])  # type: ignore
        for stat_name, value in normalized_stats.items()
    ]
    if sort:
        return dict(sorted(values, key=lambda x: x[1], reverse=True))
    return dict(values)


def goalie_player_value(stats: GoalieSeasonStats, weights: Weights) -> float:
    """Calculate goalie player value."""
    return sum(goalie_player_stat_values(stats, weights).values())


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
