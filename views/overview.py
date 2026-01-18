import streamlit as st
from state import get_db
from database.models import ProcurementRequest, StatusHistory, RequestStatus
from views.pdf_helper import show_pdf_preview
from database.commodity_groups import get_commodity_group_display
from views.edit_request import load_request_for_edit


def show_overview_page():
    st.header("Procurement Requests Overview")

    db = get_db()

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_options = ["All", RequestStatus.OPEN.value, RequestStatus.IN_PROGRESS.value, RequestStatus.CLOSED.value]
        status_filter = st.selectbox(
            "Filter by Status",
            status_options,
            key="overview_status_filter"
        )
    with col2:
        search = st.text_input("Search (vendor/title)", placeholder="Search...", key="overview_search")
    with col3:
        st.write("")
        if st.button("🔄 Refresh"):
            st.rerun()

    # Query requests
    query = db.query(ProcurementRequest)

    if st.session_state.overview_status_filter != "All":
        query = query.filter(ProcurementRequest.status == st.session_state.overview_status_filter)

    if st.session_state.overview_search:
        search_term = st.session_state.overview_search
        query = query.filter(
            (ProcurementRequest.vendor_name.ilike(f"%{search_term}%")) |
            (ProcurementRequest.title.ilike(f"%{search_term}%"))
        )

    requests = query.order_by(ProcurementRequest.created_at.desc()).all()

    if not requests:
        st.info("No requests found")
        db.close()
        return

    # Display requests
    for req in requests:
        currency_symbol = {"EUR": "€", "USD": "$", "GBP": "£", "CHF": "CHF"}.get(req.currency, "€")

        with st.expander(f"#{req.id} - {req.title} ({req.status})", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Requestor:** {req.requestor_name}")
                st.write(f"**Vendor:** {req.vendor_name}")
                st.write(f"**VAT ID:** {req.vat_id}")
                st.write(f"**Department:** {req.department}")

            with col2:
                st.write(f"**Commodity Group:** {get_commodity_group_display(req.commodity_group_id)}")
                st.write(f"**Currency:** {req.currency}")
                st.write(f"**Created:** {req.created_at.strftime('%Y-%m-%d %H:%M')}")

                # Show totals with mismatch warning
                if req.has_total_mismatch:
                    st.markdown(f"**Stated Total:** {currency_symbol} {req.stated_total_cost:,.2f}")
                    st.markdown(
                        f"<span style='color: orange;'>**Calculated Total:** {currency_symbol} {req.calculated_total_cost:,.2f} ⚠️</span>",
                        unsafe_allow_html=True)
                else:
                    st.write(f"**Total Cost:** {currency_symbol} {req.calculated_total_cost:,.2f}")

            # Order lines
            st.write("**Order Lines:**")
            for line in req.order_lines:
                line_text = f"  - {line.description}: {line.quantity} {line.unit} × {currency_symbol}{line.unit_price:.2f}"
                if line.has_price_mismatch:
                    st.markdown(
                        f"{line_text} = <span style='color: orange;'>Stated: {currency_symbol}{line.stated_total_price:.2f} | Calc: {currency_symbol}{line.calculated_total_price:.2f} ⚠️</span>",
                        unsafe_allow_html=True)
                else:
                    st.write(f"{line_text} = {currency_symbol}{line.calculated_total_price:.2f}")

            # PDF Preview
            if req.pdf_data:
                show_pdf_preview(req.pdf_data, req.pdf_filename or "document.pdf", key_prefix=f"req_{req.id}")

            st.divider()

            # Status update and Edit
            col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
            with col1:
                new_status = st.selectbox(
                    "Update Status",
                    [RequestStatus.OPEN.value, RequestStatus.IN_PROGRESS.value, RequestStatus.CLOSED.value],
                    index=[RequestStatus.OPEN.value, RequestStatus.IN_PROGRESS.value, RequestStatus.CLOSED.value].index(
                        req.status),
                    key=f"status_{req.id}"
                )
            with col2:
                if st.button("Update", key=f"update_{req.id}"):
                    if new_status != req.status:
                        old_status = req.status
                        req.status = new_status

                        history = StatusHistory(
                            request_id=req.id,
                            from_status=old_status,
                            to_status=new_status,
                            changed_by="user"
                        )
                        db.add(history)
                        db.commit()
                        st.success(f"Status updated to {new_status}")
                        st.rerun()

            with col3:
                if st.button("✏️ Edit", key=f"edit_{req.id}"):
                    db.close()
                    load_request_for_edit(req.id)
                    st.rerun()

            # Status history
            with st.expander("📜 Status History"):
                for h in req.status_history:
                    from_str = h.from_status or "Created"
                    st.write(
                        f"{h.changed_at.strftime('%Y-%m-%d %H:%M')} - {from_str} → {h.to_status} (by {h.changed_by})")

    db.close()
