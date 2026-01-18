import streamlit as st

st.set_page_config(page_title="New Request - Procuro", page_icon="📋", layout="wide")

from database.database import init_db
from state import init_session_state, reset_form, AppPage
from views.new_request import show_new_request_page

init_db()
init_session_state()

# Reset form when navigating to this page from another page
last_page = st.session_state.get("last_page")
if last_page is not None and last_page != AppPage.NEW_REQUEST.value:
    reset_form()

st.session_state.last_page = AppPage.NEW_REQUEST.value
st.session_state.current_page = AppPage.NEW_REQUEST.value

st.title("Procuro")
st.caption("Procurement Request Management System")

show_new_request_page()
