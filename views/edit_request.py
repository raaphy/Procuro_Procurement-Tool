import streamlit as st
from state import AppPage, navigate, get_db
from database.models import ProcurementRequest
from views.new_request import show_request_form

def load_request_for_edit(request_id: int):
    """Load a request into session state for editing"""
    db = get_db()
    try:
        req = db.query(ProcurementRequest).filter(ProcurementRequest.id == request_id).first()
        if req:
            st.session_state.current_page = AppPage.EDIT_REQUEST.value
            st.session_state.edit_request_id = request_id
            st.session_state.form_data = {
                "requestor_name": req.requestor_name,
                "title": req.title,
                "vendor_name": req.vendor_name,
                "vat_id": req.vat_id,
                "department": req.department,
                "currency": req.currency or "EUR",
                "status": req.status,
                "order_lines": [
                    {
                        "description": line.description,
                        "unit_price": float(line.unit_price),
                        "quantity": float(line.quantity),
                        "unit": line.unit,
                        "stated_total_price": line.stated_total_price
                    }
                    for line in req.order_lines
                ],
                "stated_total_cost": req.stated_total_cost,
                "commodity_group_id": req.commodity_group_id,
                "classification_result": None
            }
            if req.pdf_data:
                st.session_state.pdf_data = req.pdf_data
                st.session_state.pdf_filename = req.pdf_filename
            else:
                st.session_state.pdf_data = None
                st.session_state.pdf_filename = None
            return True
    finally:
        db.close()
    return False


def show_edit_request_page():
    """Page for editing an existing request"""
    edit_request_id = st.session_state.edit_request_id

    col1, col2 = st.columns([6, 1])
    with col1:
        st.header(f"Edit Procurement Request #{edit_request_id}")
    with col2:
        if st.button("❌ Cancel"):
            navigate(AppPage.OVERVIEW, preserve_filters=True)

    show_request_form(edit_mode=True, edit_request_id=edit_request_id)
    st.info("Form will be loaded from views.new_request")