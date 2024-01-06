"""OAuth tests."""
from pathlib import Path

from faha.oauth import client


def test_token_file():
    """Test token_file."""
    returned = client.token_file()
    expected = Path(__file__).parents[1].resolve() / "src/faha/oauth/tokens.json"
    assert returned == expected
