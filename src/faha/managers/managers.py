"""Manager Information."""
from dataclasses import dataclass

from yahoo_oauth import OAuth2  # type: ignore

from faha.league.info import SeasonInfo
from faha.request import request


@dataclass
class Managers:
    """Team manager class."""

    oauth: OAuth2
    season_info: SeasonInfo

    def __post_init__(self) -> None:
        """Request team information."""
        url = f"{self.season_info.url}/teams"
        self._raw_data = request(self.oauth, url)["fantasy_content"]["league"]
        self._league_info = self._raw_data[0]
        self._managers = self._raw_data[1]["teams"]

    @property
    def num_managers(self) -> int:
        """Return number of managers."""
        return self.season_info.num_managers

    def manager_info(self, manager_id: str) -> dict:
        """Return a manager's information."""
        return self._managers[manager_id]

    def team_stats(self, manager_id: str) -> dict:
        """Return the category stats for a manager."""
        team_key = f"{self.season_info.league_key}.t.{manager_id}"
        url = (
            "https://fantasysports.yahooapis.com/fantasy/v2"
            f"/team/{team_key}/stats;type=season"
        )
        res = request(self.oauth, url)
        raw_stats = res["fantasy_content"]["team"][1]["team_stats"]["stats"]
        stats = {
            raw_stats[ind]["stat"]["stat_id"]: raw_stats[ind]["stat"]["value"]
            for ind in range(len(raw_stats))
        }
        stat_categories = self.season_info.stat_categories(flatten=True)
        return {
            stat_categories[id]: value
            for id, value in stats.items()
            if id in stat_categories
        }
