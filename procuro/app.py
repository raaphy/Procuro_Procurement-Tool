import streamlit as st
from database import init_db
from state import AppPage, init_session_state, navigate
from views.new_request import show_new_request_page
from views.overview import show_overview_page
from views.edit_request import show_edit_request_page

st.set_page_config(page_title="procuro", page_icon="📋", layout="wide")

# Initialize database
init_db()


def main():
    init_session_state()
    
    st.title("📋 Procuro")
    st.caption("Procurement Request Management System")

    current_page = st.session_state.current_page
    edit_request_id = st.session_state.edit_request_id
    
    # Build navigation options dynamically
    if current_page == AppPage.EDIT_REQUEST.value:
        nav_options = ["📝 New Request", "📊 Request Overview", f"✏️ Edit Request #{edit_request_id}"]
        default_index = 2
    elif current_page == AppPage.OVERVIEW.value:
        nav_options = ["📝 New Request", "📊 Request Overview"]
        default_index = 1
    else:
        nav_options = ["📝 New Request", "📊 Request Overview"]
        default_index = 0
    
    page = st.sidebar.radio(
        "Navigation",
        nav_options,
        label_visibility="collapsed",
        index=default_index
    )

    # Handle sidebar navigation
    if page == "📝 New Request" and current_page != AppPage.NEW_REQUEST.value:
        navigate(AppPage.NEW_REQUEST)
    elif page == "📊 Request Overview" and current_page != AppPage.OVERVIEW.value:
        navigate(AppPage.OVERVIEW, preserve_filters=False)
    elif page.startswith("✏️ Edit"):
        show_edit_request_page()
    elif current_page == AppPage.NEW_REQUEST.value:
        show_new_request_page()
    elif current_page == AppPage.OVERVIEW.value:
        show_overview_page()
    elif current_page == AppPage.EDIT_REQUEST.value:
        show_edit_request_page()








if __name__ == "__main__":
    main()
