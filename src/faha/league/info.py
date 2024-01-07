"""Extract league info."""
from dataclasses import dataclass
from pathlib import Path

from faha.oauth.client import get_client
from faha.utils import json_io, string_io


@dataclass
class SeasonInfo:
    """Information class for a season of a league.

    Note: only use this class with the current season
    because the game key is fixed to that season
    """

    season: int

    @property
    def league_key(self) -> str:
        """Return the league key."""
        return f"{self.game_key}.l.{self.league_id}"

    @property
    def game_key(self) -> str:
        """Return the league game key."""
        league_info = json_io.read(info_file())
        return league_info["fantasy_content"]["game"][0]["game_key"]

    @property
    def league_id(self) -> str:
        """Return the league ID."""
        file = league_id_file(self.season)
        return string_io.read_file(file)

    @property
    def url(self) -> str:
        """Return the URL of the league."""
        return (
            f"https://fantasysports.yahooapis.com/fantasy/v2/league/{self.league_key}"
        )


def extract_league_info() -> dict:
    """Extract the league info from Yahoo.

    Note: this returns the current season only!
    """
    oauth = get_client()
    url = "https://fantasysports.yahooapis.com/fantasy/v2/game/nhl"
    response = oauth.session.get(url, params={"format": "json"})
    return response.json()


def extract_and_save_league_info() -> None:
    """Extract the league info from Yahoo and save to disk."""
    league_info = extract_league_info()
    json_io.write(info_file(), league_info)


def input_league_id() -> None:
    """Input the league ID into the ID file."""
    league_id = input("What is the league ID? ")
    season = int(input("What year did the season start? "))
    file = league_id_file(season)
    string_io.write_file(file, league_id)


def info_file() -> Path:
    """Return the Path of the league info file."""
    return info_dir() / "info.json"


def league_id_file(season: int) -> Path:
    """Return the Path of the league id file."""
    return info_dir() / f"league_id_{season}.json"


def info_dir() -> Path:
    """Return the directory storing the info files."""
    return Path(__file__).parent.resolve()
