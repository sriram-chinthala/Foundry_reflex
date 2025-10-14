# utils/ui_components.py
import streamlit as st
import yaml
from pathlib import Path

@st.cache_data
def _load_glossary():
    """Loads the glossary YAML file."""
    glossary_path = Path("glossary.yaml")
    if glossary_path.exists():
        with open(glossary_path, 'r') as file:
            return yaml.safe_load(file)
    return {}

def show_term_tooltip(term_key: str):
    """
    Displays a small info icon with a popover showing a term's definition.

    Args:
        term_key (str): The key of the term in glossary.yaml (e.g., 'sharpe_ratio').
    """
    glossary = _load_glossary()
    term_data = glossary.get(term_key)

    if term_data:
        with st.popover(f"ℹ️ {term_data.get('term', term_key)}"):
            st.markdown(f"**{term_data.get('term', term_key)}**")
            st.markdown(f"*{term_data.get('definition', 'No definition available.')}*")
            if 'calculation' in term_data:
                st.code(f"Calculation: {term_data.get('calculation')}", language="text")

def configure_glossary_tooltips(grid_builder, glossary: dict):
    """
    Reads a glossary and configures the header tooltips for an AgGrid GridOptionsBuilder.

    Args:
        grid_builder (GridOptionsBuilder): The builder instance to configure.
        glossary (dict): The loaded glossary data.
    """
    for key, value in glossary.items():
        field = key  # The field name in the dataframe
        header_name = value.get("term", key)
        tooltip_text = value.get("definition", "No definition available.")
        
        # Configure the specific column with its pretty name and tooltip
        grid_builder.configure_column(
            field=field, 
            headerName=header_name, 
            headerTooltip=tooltip_text
        )
    
    # Manually configure the non-glossary columns
    grid_builder.configure_column("symbol", headerName="Symbol", headerTooltip="The stock ticker symbol.")
    grid_builder.configure_column("strategy_name", headerName="Strategy", headerTooltip="The name of the strategy preset used.")