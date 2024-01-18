"""League info."""
from dataclasses import dataclass, field
from pathlib import Path

from faha.oauth.client import get_client
from faha.utils import json_io
from faha.yahoo import Yahoo


@dataclass
class League:
    """League class of a season.

    Note: only use this class with the current season
    because the game key is fixed to that season
    """

    season: int
    yahoo_agent: Yahoo
    team_stats_cache: dict = field(default_factory=dict)
    team_rosters_cache: dict = field(default_factory=dict)

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

    def team_stats(self, manager_ids: list[str]) -> dict:
        """Return the category stats for a manager."""
        team_keys = self._team_keys(manager_ids)
        res = self.yahoo_agent.get_team_stats(team_keys)
        raw_data = res["fantasy_content"]["teams"]
        raw_data.pop("count")
        team_stats = {
            team_info["team"][0][2]["name"]: self._extract_single_team_stats(team_info)
            for team_info in raw_data.values()
        }
        for team, stats in team_stats.items():
            self.team_stats_cache[team] = stats
        return team_stats

    def _extract_single_team_stats(self, team_info: dict) -> dict:
        raw_stats = team_info["team"][1]["team_stats"]["stats"]
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

    def team_roster(self, manager_ids: list[str]) -> dict:
        """Return the roster of a manager's team."""
        team_keys = self._team_keys(manager_ids)
        res = self.yahoo_agent.get_team_roster(team_keys)
        raw_data = res["fantasy_content"]["teams"]
        raw_data.pop("count")
        team_rosters = {
            team_info["team"][0][2]["name"]: self._extract_single_team_roster(team_info)
            for team_info in raw_data.values()
        }
        for team, roster in team_rosters.items():
            self.team_rosters_cache[team] = roster
        return team_rosters

    def _extract_single_team_roster(self, team_info: dict) -> dict:
        raw_players = team_info["team"][1]["roster"]["0"]["players"]
        raw_players.pop("count")
        return {
            search_player_item(player["player"][0], "player_id"): search_player_item(
                player["player"][0], "name"
            )
            for player in raw_players.values()
        }

    def _team_keys(self, manager_ids: list[str]) -> list[str]:
        """Return the list of team keys."""
        return [f"{self.league_key}.t.{manager_id}" for manager_id in manager_ids]


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


def extract_league_info(yahoo_agent: Yahoo) -> dict:
    """Extract the league info from Yahoo.

    Note: this returns the current season only!
    """
    return yahoo_agent.get_league_info()["fantasy_content"]["game"][0]


def extract_league_settings(yahoo_agent: Yahoo, league: League) -> dict:
    """Extract the league settings from Yahoo."""
    all_settings = yahoo_agent.get_league_settings(league.league_key)
    sub_settings = all_settings["fantasy_content"]["league"]
    num_teams = sub_settings[0]["num_teams"]
    settings = sub_settings[1]
    settings["settings"].append({"num_teams": num_teams})
    return settings


def extract_and_save_league_info() -> None:
    """Extract the league info from Yahoo and save to disk."""
    oauth = get_client()
    yahoo_agent = Yahoo(oauth)
    league_info = extract_league_info(yahoo_agent)
    json_io.write(info_file(), league_info)
    season = int(league_info["season"])
    league = League(season, yahoo_agent)
    league_settings = extract_league_settings(yahoo_agent, league)
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
