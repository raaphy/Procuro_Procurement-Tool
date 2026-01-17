import streamlit as st
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
from models import ProcurementRequest, OrderLine, StatusHistory, RequestStatus
from commodity_groups import COMMODITY_GROUPS, get_commodity_group_display
from extraction import extract_text_from_pdf, extract_offer_data, classify_commodity_group

# Initialize database
init_db()

st.set_page_config(page_title="Procuro", page_icon="📋", layout="wide")


def get_db():
    return SessionLocal()


def main():
    st.title("📋 Procuro")
    st.caption("Procurement Request Management System")

    # Sidebar navigation
    page = st.sidebar.radio(
        "Navigation",
        ["📝 New Request", "📊 Request Overview"],
        label_visibility="collapsed"
    )

    if page == "📝 New Request":
        show_new_request_page()
    else:
        show_overview_page()


def show_new_request_page():
    st.header("Create New Procurement Request")

    # File upload section
    st.subheader("📄 Upload Vendor Offer (Optional)")
    uploaded_file = st.file_uploader(
        "Upload a PDF to auto-fill the form",
        type=["pdf"],
        help="The system will extract vendor information from the uploaded document"
    )

    # Initialize session state for form data
    if "form_data" not in st.session_state:
        st.session_state.form_data = {
            "vendor_name": "",
            "vat_id": "",
            "department": "",
            "order_lines": [{"description": "", "unit_price": 0.0, "quantity": 1, "unit": "pieces"}],
            "commodity_group_id": None,
            "classification_result": None
        }

    # Process uploaded file
    if uploaded_file is not None:
        if st.button("🔍 Extract Data from PDF"):
            with st.spinner("Extracting data..."):
                try:
                    text = extract_text_from_pdf(uploaded_file.read())
                    extracted = extract_offer_data(text)
                    
                    if extracted:
                        st.session_state.form_data["vendor_name"] = extracted.get("vendor_name", "") or ""
                        st.session_state.form_data["vat_id"] = extracted.get("vat_id", "") or ""
                        st.session_state.form_data["department"] = extracted.get("department", "") or ""
                        
                        if extracted.get("order_lines"):
                            st.session_state.form_data["order_lines"] = [
                                {
                                    "description": line.get("description", ""),
                                    "unit_price": float(line.get("unit_price", 0)),
                                    "quantity": int(line.get("quantity", 1)),
                                    "unit": line.get("unit", "pieces")
                                }
                                for line in extracted["order_lines"]
                            ]
                        
                        st.success("✅ Data extracted successfully!")
                        st.rerun()
                    else:
                        st.error("Could not extract data from the document")
                except Exception as e:
                    st.error(f"Error extracting data: {str(e)}")

    st.divider()

    # Form
    st.subheader("Request Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        requestor_name = st.text_input("Requestor Name *", placeholder="John Doe")
        vendor_name = st.text_input(
            "Vendor Name *",
            value=st.session_state.form_data["vendor_name"],
            placeholder="Adobe Systems"
        )
        department = st.text_input(
            "Department *",
            value=st.session_state.form_data["department"],
            placeholder="Marketing"
        )
    
    with col2:
        title = st.text_input("Title / Short Description *", placeholder="Adobe Creative Cloud Subscription")
        vat_id = st.text_input(
            "VAT ID (USt-IdNr.) *",
            value=st.session_state.form_data["vat_id"],
            placeholder="DE123456789"
        )

    st.divider()

    # Order Lines
    st.subheader("Order Lines")
    
    order_lines = st.session_state.form_data["order_lines"]
    
    for i, line in enumerate(order_lines):
        col1, col2, col3, col4, col5 = st.columns([3, 1.5, 1, 1.5, 0.5])
        
        with col1:
            order_lines[i]["description"] = st.text_input(
                "Description",
                value=line["description"],
                key=f"desc_{i}",
                placeholder="Adobe Photoshop License"
            )
        with col2:
            order_lines[i]["unit_price"] = st.number_input(
                "Unit Price (€)",
                value=float(line["unit_price"]),
                min_value=0.0,
                step=0.01,
                key=f"price_{i}"
            )
        with col3:
            order_lines[i]["quantity"] = st.number_input(
                "Quantity",
                value=int(line["quantity"]),
                min_value=1,
                key=f"qty_{i}"
            )
        with col4:
            order_lines[i]["unit"] = st.text_input(
                "Unit",
                value=line["unit"],
                key=f"unit_{i}",
                placeholder="licenses"
            )
        with col5:
            st.write("")
            st.write("")
            if len(order_lines) > 1:
                if st.button("🗑️", key=f"del_{i}"):
                    order_lines.pop(i)
                    st.rerun()

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("➕ Add Line"):
            order_lines.append({"description": "", "unit_price": 0.0, "quantity": 1, "unit": "pieces"})
            st.rerun()

    # Calculate total
    total_cost = sum(line["unit_price"] * line["quantity"] for line in order_lines)
    st.metric("Total Cost", f"€ {total_cost:,.2f}")

    st.divider()

    # Commodity Group Classification
    st.subheader("Commodity Group")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if st.button("🤖 Auto-classify"):
            if title and order_lines and any(line["description"] for line in order_lines):
                with st.spinner("Classifying..."):
                    result = classify_commodity_group(
                        title=title,
                        order_lines=order_lines,
                        vendor_name=vendor_name,
                        department=department
                    )
                    st.session_state.form_data["commodity_group_id"] = result.get("commodity_group_id")
                    st.session_state.form_data["classification_result"] = result
                    st.rerun()
            else:
                st.warning("Please fill in title and at least one order line description first")

    classification_result = st.session_state.form_data.get("classification_result")
    commodity_group_id = st.session_state.form_data.get("commodity_group_id")
    
    if classification_result:
        st.success(f"**Suggested:** {get_commodity_group_display(commodity_group_id)}")
        st.caption(f"Confidence: {classification_result.get('confidence', 0):.0%} - {classification_result.get('rationale', '')}")

    # Manual override option
    with st.expander("Override commodity group manually"):
        group_options = {f"{g['id']} - {g['category']} - {g['name']}": g["id"] for g in COMMODITY_GROUPS}
        selected = st.selectbox(
            "Select commodity group",
            options=[""] + list(group_options.keys()),
            index=0
        )
        if selected:
            st.session_state.form_data["commodity_group_id"] = group_options[selected]
            commodity_group_id = group_options[selected]

    st.divider()

    # Validation and Submit
    errors = []
    if not requestor_name:
        errors.append("Requestor name is required")
    if not title:
        errors.append("Title is required")
    if not vendor_name:
        errors.append("Vendor name is required")
    if not vat_id:
        errors.append("VAT ID is required")
    elif not (vat_id.startswith("DE") and len(vat_id) == 11 and vat_id[2:].isdigit()):
        errors.append("VAT ID must be in format DE followed by 9 digits (e.g., DE123456789)")
    if not department:
        errors.append("Department is required")
    if not any(line["description"] and line["unit_price"] > 0 for line in order_lines):
        errors.append("At least one complete order line is required")
    if not commodity_group_id:
        errors.append("Commodity group must be classified or selected")

    if errors:
        for error in errors:
            st.error(error)

    if st.button("✅ Submit Request", type="primary", disabled=bool(errors)):
        db = get_db()
        try:
            # Create request
            request = ProcurementRequest(
                requestor_name=requestor_name,
                title=title,
                vendor_name=vendor_name,
                vat_id=vat_id,
                department=department,
                commodity_group_id=commodity_group_id,
                status=RequestStatus.OPEN.value
            )
            db.add(request)
            db.flush()

            # Add order lines
            for line in order_lines:
                if line["description"] and line["unit_price"] > 0:
                    order_line = OrderLine(
                        request_id=request.id,
                        description=line["description"],
                        unit_price=line["unit_price"],
                        quantity=line["quantity"],
                        unit=line["unit"]
                    )
                    db.add(order_line)

            # Add initial status history
            history = StatusHistory(
                request_id=request.id,
                from_status=None,
                to_status=RequestStatus.OPEN.value,
                changed_by="system"
            )
            db.add(history)

            db.commit()
            
            # Reset form
            st.session_state.form_data = {
                "vendor_name": "",
                "vat_id": "",
                "department": "",
                "order_lines": [{"description": "", "unit_price": 0.0, "quantity": 1, "unit": "pieces"}],
                "commodity_group_id": None,
                "classification_result": None
            }
            
            st.success(f"✅ Request #{request.id} submitted successfully!")
            st.balloons()
            
        except Exception as e:
            db.rollback()
            st.error(f"Error submitting request: {str(e)}")
        finally:
            db.close()


def show_overview_page():
    st.header("Procurement Requests Overview")
    
    db = get_db()
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", RequestStatus.OPEN.value, RequestStatus.IN_PROGRESS.value, RequestStatus.CLOSED.value]
        )
    with col2:
        search = st.text_input("Search (vendor/title)", placeholder="Search...")
    with col3:
        st.write("")
        if st.button("🔄 Refresh"):
            st.rerun()

    # Query requests
    query = db.query(ProcurementRequest)
    
    if status_filter != "All":
        query = query.filter(ProcurementRequest.status == status_filter)
    
    if search:
        query = query.filter(
            (ProcurementRequest.vendor_name.ilike(f"%{search}%")) |
            (ProcurementRequest.title.ilike(f"%{search}%"))
        )
    
    requests = query.order_by(ProcurementRequest.created_at.desc()).all()
    
    if not requests:
        st.info("No requests found")
        db.close()
        return

    # Display requests
    for req in requests:
        with st.expander(f"#{req.id} - {req.title} ({req.status})", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Requestor:** {req.requestor_name}")
                st.write(f"**Vendor:** {req.vendor_name}")
                st.write(f"**VAT ID:** {req.vat_id}")
                st.write(f"**Department:** {req.department}")
            
            with col2:
                st.write(f"**Commodity Group:** {get_commodity_group_display(req.commodity_group_id)}")
                st.write(f"**Created:** {req.created_at.strftime('%Y-%m-%d %H:%M')}")
                st.write(f"**Total Cost:** € {req.total_cost:,.2f}")

            # Order lines
            st.write("**Order Lines:**")
            for line in req.order_lines:
                st.write(f"  - {line.description}: {line.quantity} {line.unit} × €{line.unit_price:.2f} = €{line.total_price:.2f}")

            st.divider()

            # Status update
            col1, col2, col3 = st.columns([2, 2, 2])
            with col1:
                new_status = st.selectbox(
                    "Update Status",
                    [RequestStatus.OPEN.value, RequestStatus.IN_PROGRESS.value, RequestStatus.CLOSED.value],
                    index=[RequestStatus.OPEN.value, RequestStatus.IN_PROGRESS.value, RequestStatus.CLOSED.value].index(req.status),
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

            # Status history
            with st.expander("📜 Status History"):
                for h in req.status_history:
                    from_str = h.from_status or "Created"
                    st.write(f"{h.changed_at.strftime('%Y-%m-%d %H:%M')} - {from_str} → {h.to_status} (by {h.changed_by})")

    db.close()


if __name__ == "__main__":
    main()
