"""Make request to Yahoo."""
from yahoo_oauth import OAuth2  # type: ignore

YAHOO_ENDPOINT = "https://fantasysports.yahooapis.com/fantasy/v2"


class Yahoo:
    """Yahoo APIs builder and requester class."""

    def __init__(self, oauth: OAuth2) -> None:
        """Initialize class."""
        self.oauth = oauth

    def request(self, uri: str) -> dict:
        """Make a generic request to Yahoo."""
        url = f"{YAHOO_ENDPOINT}/{uri}"
        response = self.oauth.session.get(url, params={"format": "json"})
        if response.status_code != 200:
            raise RuntimeError(response.content)
        return response.json()

    def get_team_info(self, team_keys: list[str]) -> dict:
        """Get team info."""
        teams = ",".join(team_keys)
        uri = f"teams;team_keys={teams}"
        return self.request(uri)

    def get_team_stats(self, team_keys: list[str]) -> dict:
        """Get the season stats for a team or teams."""
        teams = ",".join(team_keys)
        uri = f"teams;team_keys={teams}/stats;type=season"
        return self.request(uri)

    def get_team_roster(self, team_keys: list[str]) -> dict:
        """Get the team roster."""
        teams = ",".join(team_keys)
        uri = f"teams;team_keys={teams}/roster/players"
        return self.request(uri)

    def get_player_stats(self, player_ids: list[str]) -> dict:
        """Get season stats for players from player ids."""
        players = ",".join(player_ids)
        uri = f"players;player_keys={players}/stats;type=season"
        return self.request(uri)

    def get_league_info(self) -> dict:
        """Get league information."""
        uri = "game/nhl"
        return self.request(uri)

    def get_league_settings(self, league_key: str) -> dict:
        """Get league settings."""
        uri = f"league/{league_key}/settings"
        return self.request(uri)
