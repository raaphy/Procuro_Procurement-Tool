from enum import Enum
import streamlit as st
from database.database import SessionLocal
from database.models import RequestStatus

class AppPage(Enum):
    NEW_REQUEST = "new"
    OVERVIEW = "overview"
    EDIT_REQUEST = "edit"


def init_session_state():
    """Initialize all session state variables"""
    if "current_page" not in st.session_state:
        st.session_state.current_page = None
    if "last_page" not in st.session_state:
        st.session_state.last_page = None
    if "edit_request_id" not in st.session_state:
        st.session_state.edit_request_id = None
    if "preserve_filters" not in st.session_state:
        st.session_state.preserve_filters = False
    if "form_data" not in st.session_state:
        st.session_state.form_data = get_empty_form_data()
    if "pdf_data" not in st.session_state:
        st.session_state.pdf_data = None
    if "pdf_filename" not in st.session_state:
        st.session_state.pdf_filename = None
    if "overview_status_filter" not in st.session_state:
        st.session_state.overview_status_filter = "All"
    if "overview_search" not in st.session_state:
        st.session_state.overview_search = ""


def get_empty_form_data():
    """Return empty form data structure"""
    return {
        "requestor_name": "",
        "title": "",
        "vendor_name": "",
        "vat_id": "",
        "department": "",
        "currency": "EUR",
        "status": RequestStatus.OPEN.value,
        "order_lines": [
            {"description": "", "unit_price": 0.0, "quantity": 1.0, "unit": "pieces", "stated_total_price": None}],
        "stated_total_cost": None,
        "commodity_group_id": None,
        "classification_result": None
    }


def navigate(page: AppPage, request_id: int = None, preserve_filters: bool = False):
    """Central navigation function"""
    st.session_state.current_page = page.value
    st.session_state.edit_request_id = request_id
    st.session_state.preserve_filters = preserve_filters

    if page == AppPage.NEW_REQUEST:
        st.session_state.form_data = get_empty_form_data()
        st.session_state.pdf_data = None
        st.session_state.pdf_filename = None
        st.session_state.last_uploaded_file = None
    elif page == AppPage.OVERVIEW and not preserve_filters:
        st.session_state.overview_status_filter = "All"
        st.session_state.overview_search = ""

    st.rerun()


def reset_form():
    """Reset form data to empty state - increments form_key to force widget reset"""
    st.session_state.form_data = get_empty_form_data()
    st.session_state.pdf_data = None
    st.session_state.pdf_filename = None
    st.session_state.last_uploaded_file = None
    # Increment form_key to force all widgets to reset
    if "form_key" not in st.session_state:
        st.session_state.form_key = 0
    st.session_state.form_key += 1


def get_db():
    return SessionLocal()
