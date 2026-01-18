import streamlit as st

st.set_page_config(page_title="Request Overview - Procuro", page_icon="📋", layout="wide")

from database.database import init_db
from state import init_session_state, AppPage
from views.overview import show_overview_page
from views.edit_request import show_edit_request_page

init_db()
init_session_state()

# Track page navigation
st.session_state.last_page = AppPage.OVERVIEW.value
st.session_state.current_page = AppPage.OVERVIEW.value

st.title("Procuro")
st.caption("Procurement Request Management System")

# Edit mode is shown on this page when edit_request_id is set
if st.session_state.get("current_page") == AppPage.EDIT_REQUEST.value and st.session_state.get("edit_request_id"):
    show_edit_request_page()
else:
    show_overview_page()
