"""League info."""
from dataclasses import dataclass
from pathlib import Path

from yahoo_oauth import OAuth2  # type: ignore

from faha.oauth.client import get_client
from faha.request import request
from faha.utils import json_io


@dataclass
class League:
    """League class of a season.

    Note: only use this class with the current season
    because the game key is fixed to that season
    """

    season: int
    oauth: OAuth2

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
    def _raw_settings(self) -> dict:
        """Return the raw league settings."""
        return json_io.read(settings_file())

    @property
    def num_managers(self) -> int:
        """Return number of managers."""
        return self._raw_settings["settings"][2]["num_teams"]

    def stat_categories(self, flatten: bool = True) -> dict:
        """Return the stat categories."""
        raw_category_info = self._raw_settings["settings"][0]["stat_categories"]
        utilized_stats = [
            item
            for item in raw_category_info["stats"]
            if "is_only_display_stat" not in item["stat"]
            or item["stat"]["is_only_display_stat"] == "0"
        ]
        raw_goalie_stats = [
            item["stat"]
            for item in utilized_stats
            if item["stat"]["group"] == "goaltending"
        ]
        raw_offense_stats = [
            item["stat"]
            for item in utilized_stats
            if item["stat"]["group"] == "offense"
        ]
        goalie_stats = {stat["stat_id"]: stat["name"] for stat in raw_goalie_stats}
        offense_stats = {stat["stat_id"]: stat["name"] for stat in raw_offense_stats}
        stats = {"goaltending": goalie_stats, "offense": offense_stats}
        if flatten:
            return {
                str(id): name
                for category_vals in stats.values()
                for id, name in category_vals.items()
            }
        return stats

    def team_stats(self, manager_id: str) -> dict:
        """Return the category stats for a manager."""
        team_key = f"{self.league_key}.t.{manager_id}"
        uri = f"team/{team_key}/stats;type=season"
        res = request(self.oauth, uri)
        raw_stats = res["fantasy_content"]["team"][1]["team_stats"]["stats"]
        stats = {
            raw_stats[ind]["stat"]["stat_id"]: raw_stats[ind]["stat"]["value"]
            for ind in range(len(raw_stats))
        }
        stat_categories = self.stat_categories(flatten=True)
        return {
            stat_categories[id]: value
            for id, value in stats.items()
            if id in stat_categories
        }

    def team_roster(self, manager_id: str) -> dict:
        """Return the roster of a manager's team."""
        team_key = f"{self.league_key}.t.{manager_id}"
        uri = f"team/{team_key}/roster/players"
        res = request(self.oauth, uri)
        players = res["fantasy_content"]["team"][1]["roster"]["0"]["players"]
        players.pop("count")
        return {
            search_player_item(player["player"][0], "player_id"): search_player_item(
                player["player"][0], "name"
            )
            for player in players.values()
        }


def search_player_item(info: dict, selection: str) -> str | list[str]:
    """General search for information about a player."""
    for item in info:
        if selection in item:
            if selection == "name":
                return item[selection]["full"]
            if selection == "eligible_positions":
                return [
                    position["position"]
                    for position in item[selection]
                    if position["position"] != "Util"
                ]
            return item[selection]
    raise KeyError(f"Player {selection} was not found.")


def extract_league_info(oauth: OAuth2) -> dict:
    """Extract the league info from Yahoo.

    Note: this returns the current season only!
    """
    uri = "game/nhl"
    return request(oauth, uri)["fantasy_content"]["game"][0]


def extract_league_settings(oauth: OAuth2, league: League) -> dict:
    """Extract the league settings from Yahoo."""
    uri = f"league/{league.league_key}/settings"
    all_settings = request(oauth, uri)["fantasy_content"]["league"]
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
    league = League(season, oauth)
    league_settings = extract_league_settings(oauth, league)
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
