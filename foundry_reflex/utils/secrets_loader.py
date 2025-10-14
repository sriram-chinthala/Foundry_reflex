# utils/secrets_loader.py
import toml
from pathlib import Path
import streamlit as st

@st.cache_resource
def load_secrets(secrets_file="secrets.toml"):
    """
    Loads secrets from a TOML file in the project root.
    Caches the result so the file is only read once.
    """
    path = Path(secrets_file)
    if not path.is_file():
        st.error(f"Secrets file not found at: {path}. Please create it.")
        return None
    try:
        return toml.load(path)
    except Exception as e:
        st.error(f"Error loading secrets file: {e}")
        return None