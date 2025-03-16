import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from src.utils import COMPONENT

st.set_page_config(
    page_title="Tacto Landing Page",
    layout="centered",
    initial_sidebar_state="collapsed",
)

col1, col2, col3 = st.columns([1, 6, 1])
with col2:
    st.image("app/assets/tacto_logo_full.png", use_container_width=True)
    st.write("")
    st.write("")

st.info(
    f"Our agents identified a high potential for the component {COMPONENT}.",
    icon="💡",
)

with st.form(key="search_form", border=False, enter_to_submit=False):
    search_col, button_col = st.columns([5, 1])

    with search_col:
        search_query = st.text_input(
            "Component Search",
            "",
            key="search_input",
            label_visibility="collapsed",
        )

    with button_col:
        submit_button = st.form_submit_button("Start")

if submit_button:
    switch_page("market_agent")
