"""Make request to Yahoo."""
from yahoo_oauth import OAuth2  # type: ignore

YAHOO_ENDPOINT = "https://fantasysports.yahooapis.com/fantasy/v2"


def request(oauth: OAuth2, uri: str) -> dict:
    """Make a generic request to Yahoo."""
    url = f"{YAHOO_ENDPOINT}/{uri}"
    return oauth.session.get(url, params={"format": "json"}).json()
