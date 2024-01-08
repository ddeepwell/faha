"""Make request to Yahoo."""
from yahoo_oauth import OAuth2  # type: ignore


def request(oauth: OAuth2, url: str) -> dict:
    """Make a generic request to Yahoo."""
    return oauth.session.get(url, params={"format": "json"}).json()
