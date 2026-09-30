import streamlit as st
from pathlib import Path
from config import BASE_DIR

DEFAULT_OUTPUT = str(BASE_DIR / "outputs")


def init_paths():
    if "output_dir" not in st.session_state:
        st.session_state["output_dir"] = DEFAULT_OUTPUT


def get_output_dir():
    init_paths()
    return Path(st.session_state["output_dir"])


def get_fig_dir():
    p = get_output_dir() / "figures"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_tab_dir():
    p = get_output_dir() / "tables"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_map_dir():
    p = get_output_dir() / "maps"
    p.mkdir(parents=True, exist_ok=True)
    return p


def set_output_dir(path_str):
    p = Path(path_str)
    p.mkdir(parents=True, exist_ok=True)
    st.session_state["output_dir"] = str(p)
    return p