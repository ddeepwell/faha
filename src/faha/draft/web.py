"""The web UI used to guide drafting.

Execute with:
$ streamlit run path/to/web.py [YEAR]
"""

import argparse
import pickle
from enum import StrEnum
from pathlib import Path

import pandas as pd
import streamlit as st

from faha.league import League
from faha.oauth.client import get_client
from faha.value import calculate_player_values
from faha.weights import stat_weights_from_yahoo
from faha.yahoo import Yahoo


class Positions(StrEnum):
    """Enumeration of player positions."""

    CENTER = "C"
    WINGER = "W"
    DEFENSEMAN = "D"
    GOALIE = "G"


Data = dict[Positions, pd.DataFrame]


def configure_page() -> None:
    """Streamlit page configuration."""
    st.set_page_config(page_title="FaHA", layout="wide")


def configure_header() -> None:
    """Create web UI page header."""
    st.title("Fantasy Hockey draft player rankings")


def get_keepers(year: int) -> list[str]:
    """Load keepers."""
    file_name = Path(f"src/faha/data/keepers_{year}.txt")
    with open(file_name, "r", encoding="utf-8") as file:
        return [name.rstrip() for name in file.readlines()]


def get_saved_data(data_file: Path) -> Data:
    """Load saved data."""
    with open(data_file, "rb") as file:
        return pickle.load(file)


def save_data(data: Data, data_file: Path) -> None:
    """Save data to disk."""
    with open(data_file, "wb") as file:
        pickle.dump(data, file)


def get_data_from_yahoo(year: int) -> Data:
    """Create data from a year."""
    oauth = get_client()
    yahoo_agent = Yahoo(oauth)
    lg = League(year, yahoo_agent)
    taken = lg.taken_players()
    weights = stat_weights_from_yahoo(year)
    taken_val = calculate_player_values(taken, weights)
    data_in_frame = pd.DataFrame(taken_val).transpose()
    return {
        pos: data_in_frame[is_position(pos.value, data_in_frame)].sort_values(
            by="Value", ascending=False
        )
        for pos in Positions
    }


def is_position(position: str, dataframe: pd.DataFrame) -> list[bool]:
    """List booleans matching a particular position."""
    if position == "W":
        return [
            "LW" in positions or "RW" in positions
            for positions in dataframe["Positions"]
        ]
    return dataframe["Positions"].tolist()


def initialize_state(data: Data) -> None:
    """Initialize the streamlit state."""
    if Positions.CENTER not in st.session_state:
        for position in Positions:
            st.session_state[position] = data[position]

    if "deleted_players" not in st.session_state:
        st.session_state.deleted_players = []

    if "player_to_delete" not in st.session_state:
        st.session_state.player_to_delete = ""

    if "player_to_value" not in st.session_state:
        st.session_state.player_to_value = ""

    if "keepers_are_deleted" not in st.session_state:
        st.session_state.keepers_are_deleted = False


def delete_player_in_all_tables(player: pd.Series) -> None:
    """Delete a player in all relevant tables."""
    st.session_state.deleted_players.append(player)
    for position in Positions:
        if _player_plays_position(position.value, player["Positions"]):
            _delete_player_in_table(position, player["Name"])
    st.toast(f"Deleted {player['Name']}", icon=":material/check:")


def _player_plays_position(position: str, positions: list[str]) -> bool:
    if position == Positions.WINGER:
        return "LW" in positions or "RW" in positions
    return position in positions


def _delete_player_in_table(position: Positions, name: str) -> None:
    st.session_state[position] = st.session_state[position][
        st.session_state[position]["Name"] != name
    ]


def value_player_by_entry(name: str) -> None:
    """Print the value of a player."""
    name = name.strip()
    if name not in _all_names():
        _not_found_message(name)
        return
    for position in Positions:
        names = st.session_state[position]["Name"]
        if name in names.tolist():
            player = st.session_state[position].loc[name]
            player_value = player["Value"]
            st.toast(f"{player['Name']}: {player_value:2.2f}", icon=":material/check:")
            st.session_state.player_to_value = ""
            return


def delete_player_by_entry(name: str) -> None:
    """Delete a player by entering a name."""
    name = name.strip()
    if name not in _all_names():
        _not_found_message(name)
        return
    name_in_table = False
    iter_positions = iter(Positions)
    while not name_in_table:
        position = next(iter_positions)
        names = st.session_state[position]["Name"]
        name_in_table = name in names.tolist()
        if name_in_table:
            player = st.session_state[position].loc[name]
            delete_player_in_all_tables(player)
    st.session_state.player_to_delete = ""


def _not_found_message(name: str) -> None:
    st.toast(f"No player found with the name: {name}", icon=":material/cancel:")


def _all_names() -> set:
    names: set = set()
    for position in Positions:
        names = names.union(set(st.session_state[position]["Name"].tolist()))
    return names


def undo_delete() -> None:
    """Undo the deletion of a player."""
    if not st.session_state.deleted_players:
        return
    last_deleted = st.session_state.deleted_players.pop()
    undid_deletion = False
    for position in Positions:
        if _player_plays_position(position.value, last_deleted["Positions"]):
            st.session_state[position] = pd.concat(
                [st.session_state[position], pd.DataFrame([last_deleted])],
                ignore_index=True,
            )
            st.session_state[position] = st.session_state[position].sort_values(
                by="Value", ascending=False
            )
            undid_deletion = True
    if undid_deletion:
        st.toast(f"Undid deletion of {last_deleted['Name']}", icon=":material/check:")


def update_value_inputs() -> None:
    """Update the value text input state variables."""
    st.session_state.player_to_value = st.session_state.value_input
    st.session_state.value_input = ""


def update_delete_inputs() -> None:
    """Update the delete text input state variables."""
    st.session_state.player_to_delete = st.session_state.delete_input
    st.session_state.delete_input = ""


def print_position_tables() -> None:
    """Print the player position tables."""
    cols = st.columns([1, 1, 1, 1], gap="medium")
    for index, position in enumerate(Positions):
        print_table(
            cols[index],
            st.session_state[position],
            f"## {position.name.capitalize()}",  # type: ignore
        )


def print_table(cols, data, title: str) -> None:
    """Print a position table."""
    cols.write(title)
    with cols:
        for _, row in data.head(20).iterrows():
            st.text(
                f"{row["Name"]}\n"
                f"{', '.join(row['Positions']):<8} {row['Value']:2.2f}"
            )


def text_inputs_section() -> None:
    """Create the text input section."""
    value_column, delete_name_column, undo_delete_button_column = st.columns([2, 2, 1])
    create_value_text_input(value_column)
    create_delete_text_input(delete_name_column)
    check_pressed_enter()
    create_undo_button(undo_delete_button_column)


def create_value_text_input(value_column) -> None:
    """Fill player value text input column."""
    with value_column:
        st.text_input(
            "Enter a name to print their value:",
            key="value_input",
            on_change=update_value_inputs,
        )


def create_delete_text_input(delete_name_column) -> None:
    """Fill delete player text input column."""
    with delete_name_column:
        st.text_input(
            "Enter a name to delete:",
            key="delete_input",
            on_change=update_delete_inputs,
        )


def check_pressed_enter() -> None:
    """Check if enter was pressed during text input."""
    if st.session_state.player_to_delete:
        delete_player_by_entry(st.session_state.player_to_delete)
    if st.session_state.player_to_value:
        value_player_by_entry(st.session_state.player_to_value)


def create_undo_button(undo_delete_button_column) -> None:
    """Fill undo button column."""
    with undo_delete_button_column:
        st.button(
            "Undo Delete",
            on_click=undo_delete,
            disabled=len(st.session_state.deleted_players) == 0,
        )


def delete_keepers(year: int):
    """Delete keepers."""
    if not st.session_state.keepers_are_deleted:
        for keeper in get_keepers(year):
            delete_player_by_entry(keeper)
        st.session_state.keepers_are_deleted = True


def main() -> None:
    """Create the web UI."""
    parser = argparse.ArgumentParser(description="Create draft helper web UI")
    parser.add_argument("year", type=int)
    args = parser.parse_args()
    year = args.year
    data_file = Path(f"src/faha/data/{year}.pkl")
    if data_file.exists():
        data = get_saved_data(data_file)
    else:
        data = get_data_from_yahoo(year)
        save_data(data, data_file)
    configure_page()
    configure_header()
    initialize_state(data)
    delete_keepers(year)
    text_inputs_section()
    print_position_tables()


if __name__ == "__main__":
    main()
