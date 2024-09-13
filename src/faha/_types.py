"""Types."""

from typing import Callable, TypedDict

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
