"""League info."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from glom import (  # type: ignore
    SKIP,
    M,
    Or,
    T,
    glom,
)

from faha._types import Weights
from faha.oauth.client import get_client
from faha.players import (
    GoaliePlayer,
    GoalieSeasonStats,
    OffensePlayer,
    OffenseSeasonStats,
)
from faha.utils import json_io
from faha.value import calculate_player_values, sort_players
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
    taken_players_cache: dict = field(default_factory=dict)
    available_players_cache: dict = field(default_factory=dict)

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

    @property
    def all_manager_ids(self) -> list[str]:
        """Return the list of all manager IDs."""
        return [str(mngr) for mngr in range(1, self.num_managers + 1)]

    @property
    def team_names(self) -> dict[str, str]:
        """Return the team names."""
        team_keys = self._team_keys(self.all_manager_ids)
        res = self.yahoo_agent.get_team_info(team_keys)
        raw_data = res["fantasy_content"]["teams"]
        raw_data.pop("count")
        return {
            _get_team_info(team_info, "name")[0]: _get_team_info(team_info, "team_id")[
                0
            ]
            for team_info in raw_data.values()
        }

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

    def team_roster(self, manager_ids: list[str] | str) -> dict:
        """Return the roster of a manager's team."""
        if isinstance(manager_ids, str):
            team_keys = self._team_keys([manager_ids])
        else:
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

    def team_player_stats(self, manager_id: str) -> dict:
        """Find players on a team and return their stats and info."""
        roster = self.team_roster(manager_id)
        team_name = list(roster.keys())[0]
        players = list(roster[team_name].keys())
        return self.players(players)

    def team_offense_player_values(
        self, manager_id: str, weights: Weights
    ) -> list[tuple[str, float]]:
        """Return the skater player values for a manager."""
        return self._team_player_values(manager_id, weights, "P")

    def team_goalie_player_values(
        self, manager_id: str, weights: Weights
    ) -> list[tuple[str, float]]:
        """Return the goalie player values for a manager."""
        return self._team_player_values(manager_id, weights, "G")

    def _team_player_values(
        self, manager_id: str, weights: Weights, position: str
    ) -> list[tuple[str, float]]:
        player_stats = self.team_player_stats(manager_id)
        players_to_remove = [
            player_name
            for player_name, player_info in player_stats.items()
            if player_info["Position Type"] != position
        ]
        for player_name in players_to_remove:
            player_stats.pop(player_name)
        valued_stats = calculate_player_values(player_stats, weights)
        return sort_players(valued_stats, condensed=True)  # type: ignore

    def team_values(self, weights: Weights) -> list[tuple[str, float]]:
        """Return the list of teams and their values.

        This method can be greatly improved, likely by combining the many API calls
        that currently exist within the for loop.
        Might want to find a way to account for the variance in player slots between
        offensive (11 slots) and goalie (2 slots) players
        """
        team_list = []
        for manager, manager_id in self.team_names.items():
            offense_values = self.team_offense_player_values(manager_id, weights)
            goalie_values = self.team_goalie_player_values(manager_id, weights)
            team_value = (
                sum(value for _, value in offense_values) * 8 / 12
                + sum(value for _, value in goalie_values) * 4 / 12
            )  # goalies only account for 4/12th of the stats
            team_list.append((manager, team_value))
        return sorted(team_list, key=lambda x: x[1], reverse=True)

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

    def _player_keys(self, player_ids: list[str]) -> list[str]:
        """Return the list of team keys."""
        return [f"{self.game_key}.p.{player_id}" for player_id in player_ids]

    def players(self, player_ids: list[str]) -> dict:
        """Return stats for players matching the player ids."""
        player_keys = self._player_keys(player_ids)
        res = self.yahoo_agent.get_player_stats(player_keys)
        raw_data = res["fantasy_content"]["players"]
        raw_data.pop("count")
        player_info = {
            player_info["player"][0][2]["name"]["full"]: self._extract_player_data(
                player_info
            )
            for player_info in raw_data.values()
        }
        return player_info

    def _extract_player_data(self, player_info: dict) -> OffensePlayer | GoaliePlayer:
        """Extract the player from raw data."""
        player_id = _get_player_id(player_info)
        name = _get_player_name(player_info)
        nhl_team = _get_nhl_team(player_info)
        positions = _get_positions(player_info)
        position_type = _get_position_type(player_info)
        if position_type == "P":
            oplayer: OffensePlayer = {
                "Player ID": player_id,
                "Name": name,
                "NHL Team": nhl_team,
                "Positions": positions,
                "Position Type": position_type,
                "Season Stats": self._get_offensive_stats(player_info),
            }
            return oplayer
        if position_type == "G":
            gplayer: GoaliePlayer = {
                "Player ID": player_id,
                "Name": name,
                "NHL Team": nhl_team,
                "Positions": positions,
                "Position Type": position_type,
                "Season Stats": self._get_goalie_stats(player_info),
            }
            return gplayer
        raise ValueError(f"Unknown position type, {position_type}")

    def _get_offensive_stats(self, player_info: dict) -> OffenseSeasonStats:
        """Return an offensive player's stats."""
        games_played = convert(self._extract_stat(player_info, "Games Played"), int)
        goals = convert(self._extract_stat(player_info, "Goals"), int)
        assists = convert(self._extract_stat(player_info, "Assists"), int)
        plus_minus = convert(self._extract_stat(player_info, "Plus/Minus"), int)
        powerplay_points = convert(
            self._extract_stat(player_info, "Powerplay Points"), int
        )
        shots_on_goal = convert(self._extract_stat(player_info, "Shots on Goal"), int)
        faceoffs_won = convert(self._extract_stat(player_info, "Faceoffs Won"), int)
        hits = convert(self._extract_stat(player_info, "Hits"), int)
        blocks = convert(self._extract_stat(player_info, "Blocks"), int)
        stats: OffenseSeasonStats = {
            "Games Played": games_played,
            "Goals": goals,
            "Assists": assists,
            "Plus/Minus": plus_minus,
            "Powerplay Points": powerplay_points,
            "Shots on Goal": shots_on_goal,
            "Faceoffs Won": faceoffs_won,
            "Hits": hits,
            "Blocks": blocks,
        }
        return stats

    def _get_goalie_stats(self, player_info: dict) -> GoalieSeasonStats:
        """Return an goalie player's stats."""
        games_started = convert(self._extract_stat(player_info, "Games Started"), int)
        wins = convert(self._extract_stat(player_info, "Wins"), int)
        saves = convert(self._extract_stat(player_info, "Saves"), int)
        save_percentage = convert(
            self._extract_stat(player_info, "Save Percentage"), float
        )
        shutouts = convert(self._extract_stat(player_info, "Shutouts"), int)
        stats: GoalieSeasonStats = {
            "Games Started": games_started,
            "Wins": wins,
            "Saves": saves,
            "Save Percentage": save_percentage,
            "Shutouts": shutouts,
        }
        return stats

    def _extract_stat(self, player_info: dict, stat_name: str) -> str:
        """Extract a stat."""
        return glom(player_info, self._stat_spec(stat_name))[0]

    def _stat_spec(self, stat_name: str) -> tuple:
        """Return the glom stat spec."""
        stat_id = self._stat_id(stat_name)
        return (
            "player",
            T[1],
            "player_stats.stats",
            [T["stat"]],
            [Or((M(T["stat_id"]) == stat_id, "value"), default=SKIP)],
        )

    def _stat_id(self, stat_name: str) -> str:
        """Return the stat ID for a stat name."""
        if stat_name in self.stat_categories().values():
            return next(
                (k for k, v in self.stat_categories().items() if v == stat_name)
            )
        if stat_name == "Games Played":
            return "29"
        if stat_name == "Games Started":
            return "18"
        raise ValueError(f"Unknown stat: {stat_name}")

    def taken_players(self, position: Optional[str] = None) -> dict:
        """Return the players taken by teams."""
        if not self.taken_players_cache:
            self.taken_players_cache = self._fetch_players("T", position)
        return self.taken_players_cache

    def available_players(self, position: Optional[str] = None) -> dict:
        """Return the available players."""
        if not self.available_players_cache:
            self.available_players_cache = self._fetch_players("A", position)
        return self.available_players_cache

    def _fetch_players(self, status: str, position: Optional[str] = None) -> dict:
        """Fetch players from Yahoo.

        Args:
            status (str): Indicates what type of players to get.  Available
            options are: 'FA' for free agents, 'W' waivers only, 'T' all taken
            players, 'K' keepers, 'A' all available players (FA + WA).
        """
        # The Yahoo! API we use doles out players 25 per page.  We need to make
        # successive calls to gather all of the players.  We stop when we fetch
        # less then 25.
        player_keys = self._fetch_players_ids(status, position)
        player_key_chunks = [
            player_keys[ii : ii + 25]  # noqa: E203
            for ii in range(0, len(player_keys), 25)
        ]
        players: dict = {}
        for players_in_chunk in player_key_chunks:
            potential_players = self.players(players_in_chunk)
            players |= {
                k: v
                for k, v in potential_players.items()
                if not (
                    (
                        "Games Started" in v["Season Stats"]
                        and v["Season Stats"]["Games Started"] == 0
                    )
                    or (
                        "Games Played" in v["Season Stats"]
                        and v["Season Stats"]["Games Played"] == 0
                    )
                )
            }
        return players

    def _fetch_players_ids(
        self,
        status: str,
        position: Optional[str] = None,
    ) -> list[str]:
        """Fetch player ids from Yahoo with a status.

        Args:
            status (str): Indicates what type of players to get.  Available
            options are: 'FA' for free agents, 'W' waivers only, 'T' all taken
            players, 'K' keepers, 'A' all available players (FA + WA).
        """
        # The Yahoo! API we use doles out players 25 per page.  We need to make
        # successive calls to gather all of the players.  We stop when we fetch
        # less then 25.
        players_per_page = 25
        player_ids = []
        player_index = 0
        while player_index % players_per_page == 0:
            res = self.yahoo_agent.get_player_category_stats(
                self.league_key, player_index, status, position
            )
            raw_data = res["fantasy_content"]["league"][1]["players"]
            num_paginated_players = raw_data["count"]
            if num_paginated_players == 0:
                break
            raw_data.pop("count")
            player_index += num_paginated_players
            player_ids += [
                _get_player_id(player_info) for player_info in raw_data.values()
            ]
        return player_ids


def convert(quantity: str, new_type: type) -> int:
    """Convert a string to int."""
    return new_type(quantity) if quantity != "-" else 0


def _get_player_id(player_info: dict) -> str:
    return glom(
        player_info,
        ("player", T[0], ([Or((M(T["player_id"]), "player_id"), default=SKIP)])),
    )[0]


def _get_player_name(player_info: dict) -> str:
    return glom(
        player_info,
        ("player", T[0], ([Or((M(T["name"]), "name.full"), default=SKIP)])),
    )[0]


def _get_nhl_team(player_info: dict) -> str:
    return glom(
        player_info,
        (
            "player",
            T[0],
            ([Or((M(T["editorial_team_abbr"]), "editorial_team_abbr"), default=SKIP)]),
        ),
    )[0]


def _get_positions(player_info: dict) -> list[str]:
    return glom(
        player_info,
        (
            "player",
            T[0],
            (
                [
                    Or(
                        (
                            M(T["eligible_positions"]),
                            "eligible_positions",
                            ["position"],
                        ),
                        default=SKIP,
                    )
                ]
            ),
        ),
    )[0]


def _get_position_type(player_info: dict) -> str:
    return glom(
        player_info,
        (
            "player",
            T[0],
            ([Or((M(T["position_type"]), "position_type"), default=SKIP)]),
        ),
    )[0]


def _get_team_info(team_info: dict, category) -> str:
    return glom(
        team_info, ("team", T[0], ([Or((M(T[category]), category), default=SKIP)]))
    )


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
