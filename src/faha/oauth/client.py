"""Get OAuth Tokens."""
from pathlib import Path

from yahoo_oauth import OAuth2  # type: ignore

from faha.utils import json_io


def get_client() -> OAuth2:
    """Authenticate to get OAuth tokens."""
    oauth = OAuth2(None, None, from_file=token_file())
    if not oauth.token_is_valid():
        oauth.refresh_access_token()
    return oauth


def token_file() -> Path:
    """Return the token file."""
    oauth_dir = Path(__file__).resolve().parent
    return oauth_dir / "tokens.json"


def initialize_keys() -> None:
    """Initialize the client keys."""
    consumer_key = input("What is the Client ID (Consumer Key)? ")
    consumer_secret = input("What is the Client Secret (Consumer Secret)? ")
    tokens = {
        "consumer_key": consumer_key,
        "consumer_secret": consumer_secret,
    }
    json_io.write(token_file(), tokens)
    get_client()
