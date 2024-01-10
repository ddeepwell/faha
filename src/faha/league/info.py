"""Extract league info."""
from dataclasses import dataclass
from pathlib import Path

from yahoo_oauth import OAuth2  # type: ignore

from faha.oauth.client import get_client
from faha.request import request
from faha.utils import json_io


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
        return league_info["game_key"]

    @property
    def league_id(self) -> str:
        """Return the league ID."""
        file = league_ids_file()
        return json_io.read(file)[str(self.season)]

    @property
    def url(self) -> str:
        """Return the URL of the league."""
        return (
            f"https://fantasysports.yahooapis.com/fantasy/v2/league/{self.league_key}"
        )

    @property
    def _raw_settings(self) -> dict:
        """Return the raw league settings."""
        return json_io.read(settings_file())


def extract_league_info(oauth: OAuth2) -> dict:
    """Extract the league info from Yahoo.

    Note: this returns the current season only!
    """
    url = "https://fantasysports.yahooapis.com/fantasy/v2/game/nhl"
    return request(oauth, url)["fantasy_content"]["game"][0]


def extract_league_settings(oauth: OAuth2, season_info: SeasonInfo) -> dict:
    """Extract the league settings from Yahoo.

    Note: this returns the current season only!
    """
    url = f"{season_info.url}/settings"
    all_settings = request(oauth, url)["fantasy_content"]["league"]
    num_teams = all_settings[0]["num_teams"]
    settings = all_settings[1]
    settings["settings"].append({"num_teams": num_teams})
    return settings


def extract_and_save_league_info() -> None:
    """Extract the league info from Yahoo and save to disk."""
    oauth = get_client()
    league_info = extract_league_info(oauth)
    json_io.write(info_file(), league_info)
    season = int(league_info["season"])
    season_info = SeasonInfo(season)
    league_settings = extract_league_settings(oauth, season_info)
    json_io.write(settings_file(), league_settings)


def input_league_id() -> None:
    """Input the league ID into the ID file."""
    league_id = input("What is the league ID? ")
    season = int(input("What year did the season start? "))
    file = league_ids_file()
    if file.exists():
        content = json_io.read(file)
        content[season] = league_id
    else:
        content = {season: league_id}
    json_io.write(file, content)


def info_file() -> Path:
    """Return the path of the league info file."""
    return info_dir() / "info.json"


def league_ids_file() -> Path:
    """Return the path of the league id file."""
    return info_dir() / "league_ids.json"


def settings_file() -> Path:
    """Return the path of the league settings file."""
    return info_dir() / "settings.json"


def info_dir() -> Path:
    """Return the directory storing the info files."""
    return Path(__file__).parent.resolve() / "data"
