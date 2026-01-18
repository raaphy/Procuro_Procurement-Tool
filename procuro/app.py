import streamlit as st
import base64
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
from models import ProcurementRequest, OrderLine, StatusHistory, RequestStatus
from commodity_groups import COMMODITY_GROUPS, get_commodity_group_display
from extraction import extract_offer_data_from_pdf, classify_commodity_group

# Initialize database
init_db()

st.set_page_config(page_title="Procuro", page_icon="📋", layout="wide")


def get_db():
    return SessionLocal()


def show_pdf_preview(pdf_data: bytes, filename: str = "document.pdf", key_prefix: str = "pdf"):
    """Display PDF with download button and optional embedded preview"""
    st.markdown(f"**📄 {filename}**")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        st.download_button(
            label="⬇️ Download PDF",
            data=pdf_data,
            file_name=filename,
            mime="application/pdf",
            key=f"{key_prefix}_download_{filename}"
        )
    
    preview_key = f"{key_prefix}_show_preview_{filename}"
    if preview_key not in st.session_state:
        st.session_state[preview_key] = False
    
    with col2:
        if st.button("👁️ Show Preview" if not st.session_state[preview_key] else "🙈 Hide Preview", key=f"{key_prefix}_toggle_{filename}"):
            st.session_state[preview_key] = not st.session_state[preview_key]
            st.rerun()
    
    if st.session_state[preview_key]:
        # TODO: maybe make pdf cachable
        base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
        pdf_display = f'''
            <iframe 
                src="data:application/pdf;base64,{base64_pdf}" 
                width="100%" 
                height="500px" 
                type="application/pdf"
                style="border: 1px solid #ccc; border-radius: 4px;">
            </iframe>
        '''
        st.markdown(pdf_display, unsafe_allow_html=True)


def navigate_to_overview(preserve_filters: bool = True):
    """Navigate back to overview page"""
    st.session_state.edit_mode = False
    st.session_state.edit_request_id = None
    st.session_state.pdf_data = None
    st.session_state.pdf_filename = None
    st.session_state.form_data = {
        "requestor_name": "",
        "title": "",
        "vendor_name": "",
        "vat_id": "",
        "department": "",
        "currency": "EUR",
        "status": RequestStatus.OPEN.value,
        "order_lines": [{"description": "", "unit_price": 0.0, "quantity": 1.0, "unit": "pieces", "stated_total_price": None}],
        "stated_total_cost": None,
        "commodity_group_id": None,
        "classification_result": None
    }
    if not preserve_filters:
        st.session_state.overview_status_filter = "All"
        st.session_state.overview_search = ""
    st.session_state.navigate_to_overview = True


def load_request_for_edit(request_id: int):
    """Load a request into session state for editing"""
    db = get_db()
    try:
        req = db.query(ProcurementRequest).filter(ProcurementRequest.id == request_id).first()
        if req:
            st.session_state.edit_mode = True
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


def main():
    st.title("📋 Procuro")
    st.caption("Procurement Request Management System")

    edit_mode = st.session_state.get("edit_mode", False)
    edit_request_id = st.session_state.get("edit_request_id")
    
    # Build navigation options dynamically
    if edit_mode:
        nav_options = ["📝 New Request", "📊 Request Overview", f"✏️ Edit Request #{edit_request_id}"]
        default_index = 2  # Select Edit page
    elif st.session_state.get("navigate_to_overview"):
        nav_options = ["📝 New Request", "📊 Request Overview"]
        default_index = 1  # Select Overview page
    else:
        nav_options = ["📝 New Request", "📊 Request Overview"]
        default_index = 0
    
    page = st.sidebar.radio(
        "Navigation",
        nav_options,
        label_visibility="collapsed",
        index=default_index
    )

    # Handle navigation
    if page.startswith("✏️ Edit"):
        show_edit_request_page()
    elif page == "📝 New Request":
        # If switching to New Request while in edit mode, clear edit state
        if edit_mode:
            st.session_state.edit_mode = False
            st.session_state.edit_request_id = None
            st.session_state.pdf_data = None
            st.session_state.pdf_filename = None
            st.session_state.form_data = {
                "requestor_name": "",
                "title": "",
                "vendor_name": "",
                "vat_id": "",
                "department": "",
                "currency": "EUR",
                "status": RequestStatus.OPEN.value,
                "order_lines": [{"description": "", "unit_price": 0.0, "quantity": 1.0, "unit": "pieces", "stated_total_price": None}],
                "stated_total_cost": None,
                "commodity_group_id": None,
                "classification_result": None
            }
            st.rerun()
        show_new_request_page()
    elif page == "📊 Request Overview":
        # Check if navigating from edit mode via Cancel/Update (preserve_filters flag)
        if st.session_state.get("navigate_to_overview"):
            st.session_state.navigate_to_overview = False
        elif edit_mode:
            # User clicked on Overview in sidebar while in edit mode - reset filters
            st.session_state.overview_status_filter = "All"
            st.session_state.overview_search = ""
            st.session_state.edit_mode = False
            st.session_state.edit_request_id = None
        show_overview_page()


def show_edit_request_page():
    """Page for editing an existing request"""
    edit_request_id = st.session_state.get("edit_request_id")
    
    col1, col2 = st.columns([6, 1])
    with col1:
        st.header(f"Edit Procurement Request #{edit_request_id}")
    with col2:
        if st.button("❌ Cancel"):
            navigate_to_overview(preserve_filters=True)
            st.rerun()
    
    show_request_form(edit_mode=True, edit_request_id=edit_request_id)


def show_new_request_page():
    """Page for creating a new request"""
    st.header("Create New Procurement Request")
    show_request_form(edit_mode=False, edit_request_id=None)


def show_request_form(edit_mode: bool, edit_request_id: int | None):

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
            "requestor_name": "",
            "title": "",
            "vendor_name": "",
            "vat_id": "",
            "department": "",
            "currency": "EUR",
            "status": RequestStatus.OPEN.value,
            "order_lines": [{"description": "", "unit_price": 0.0, "quantity": 1.0, "unit": "pieces", "stated_total_price": None}],
            "stated_total_cost": None,
            "commodity_group_id": None,
            "classification_result": None
        }
    
    if "extraction_counter" not in st.session_state:
        st.session_state.extraction_counter = 0

    # Track uploaded file to avoid re-extraction on every rerun
    if "last_uploaded_file" not in st.session_state:
        st.session_state.last_uploaded_file = None

    # Auto-extract when a new file is uploaded
    if uploaded_file is not None:
        file_id = (uploaded_file.name, uploaded_file.size)
        if st.session_state.last_uploaded_file != file_id:
            st.session_state.last_uploaded_file = file_id
            pdf_bytes = uploaded_file.read()
            # Store PDF for preview and saving
            st.session_state.pdf_data = pdf_bytes
            st.session_state.pdf_filename = uploaded_file.name
            
            with st.spinner("Extracting data from PDF..."):
                try:
                    extracted = extract_offer_data_from_pdf(pdf_bytes)
                    
                    if extracted:
                        st.session_state.form_data["requestor_name"] = extracted.get("requestor_name", "") or ""
                        st.session_state.form_data["title"] = extracted.get("title", "") or ""
                        st.session_state.form_data["vendor_name"] = extracted.get("vendor_name", "") or ""
                        st.session_state.form_data["vat_id"] = extracted.get("vat_id", "") or ""
                        st.session_state.form_data["department"] = extracted.get("department", "") or ""
                        st.session_state.form_data["currency"] = extracted.get("currency", "EUR") or "EUR"
                        st.session_state.form_data["stated_total_cost"] = extracted.get("stated_total_cost")
                        
                        if extracted.get("order_lines"):
                            st.session_state.extraction_counter += 1
                            
                            st.session_state.form_data["order_lines"] = [
                                {
                                    "description": line.get("description", ""),
                                    "unit_price": float(line.get("unit_price", 0) or 0),
                                    "quantity": float(line.get("quantity", 1) or 1),
                                    "unit": line.get("unit", "pieces") or "pieces",
                                    "stated_total_price": line.get("stated_total_price")
                                }
                                for line in extracted["order_lines"]
                            ]
                        
                        # Auto-classify commodity group
                        if st.session_state.form_data["title"] or any(line["description"] for line in st.session_state.form_data["order_lines"]):
                            result = classify_commodity_group(
                                title=st.session_state.form_data["title"],
                                order_lines=st.session_state.form_data["order_lines"],
                                vendor_name=st.session_state.form_data["vendor_name"],
                                department=st.session_state.form_data["department"]
                            )
                            st.session_state.form_data["commodity_group_id"] = result.get("commodity_group_id")
                            st.session_state.form_data["classification_result"] = result
                        
                        st.success("✅ Data extracted and classified successfully!")
                        st.rerun()
                    else:
                        st.error("Could not extract data from the document")
                except Exception as e:
                    st.error(f"Error extracting data: {str(e)}")

    # Show PDF preview if available
    if st.session_state.get("pdf_data"):
        show_pdf_preview(st.session_state.pdf_data, st.session_state.get("pdf_filename", "document.pdf"), key_prefix="form")
        if st.button("🗑️ Remove PDF", key="form_remove_pdf"):
            st.session_state.pdf_data = None
            st.session_state.pdf_filename = None
            st.session_state.last_uploaded_file = None
            st.rerun()

    st.divider()

    # Form
    st.subheader("Request Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        requestor_name = st.text_input(
            "Requestor Name *",
            value=st.session_state.form_data["requestor_name"],
            placeholder="Max Mustermann"
        )
        vendor_name = st.text_input(
            "Vendor Name *",
            value=st.session_state.form_data["vendor_name"],
            placeholder="Company XYZ"
        )
        department = st.text_input(
            "Department *",
            value=st.session_state.form_data["department"],
            placeholder="Department X"
        )
    
    with col2:
        title = st.text_input(
            "Title / Short Description *",
            value=st.session_state.form_data["title"],
            placeholder="Product Name"
        )
        vat_id = st.text_input(
            "VAT ID (USt-IdNr.) *",
            value=st.session_state.form_data["vat_id"],
            placeholder="DEXXXXXXXXX"
        )
        col2a, col2b = st.columns(2)
        with col2a:
            currency = st.selectbox(
                "Currency",
                options=["EUR", "USD", "GBP", "CHF"],
                index=["EUR", "USD", "GBP", "CHF"].index(st.session_state.form_data.get("currency", "EUR"))
            )
            st.session_state.form_data["currency"] = currency
        with col2b:
            status_options = [RequestStatus.OPEN.value, RequestStatus.IN_PROGRESS.value, RequestStatus.CLOSED.value]
            if edit_mode:
                current_status = st.session_state.form_data.get("status", RequestStatus.OPEN.value)
                status = st.selectbox(
                    "Status",
                    options=status_options,
                    index=status_options.index(current_status)
                )
                st.session_state.form_data["status"] = status
            else:
                st.selectbox(
                    "Status",
                    options=[RequestStatus.OPEN.value],
                    index=0,
                    disabled=True,
                    help="New requests are always created with status 'Open'"
                )

    st.divider()

    # Order Lines
    st.subheader("Order Lines")
    
    order_lines = st.session_state.form_data["order_lines"]
    
    currency_symbol = {"EUR": "€", "USD": "$", "GBP": "£", "CHF": "CHF"}.get(currency, "€")
    ec = st.session_state.extraction_counter  # Use counter for unique keys after extraction
    
    for i, line in enumerate(order_lines):
        col1, col2, col3, col4, col5, col6, col7 = st.columns([2.5, 1.2, 0.8, 1, 1.2, 1.2, 0.4])
        
        with col1:
            order_lines[i]["description"] = st.text_input(
                "Description",
                value=line["description"],
                key=f"desc_{ec}_{i}",
                placeholder="Some Product description"
            )
        with col2:
            order_lines[i]["unit_price"] = st.number_input(
                f"Unit Price ({currency_symbol})",
                value=float(line["unit_price"]),
                min_value=0.0,
                step=0.01,
                key=f"price_{ec}_{i}"
            )
        with col3:
            order_lines[i]["quantity"] = st.number_input(
                "Qty",
                value=float(line["quantity"]),
                min_value=0.01,
                step=0.01,
                key=f"qty_{ec}_{i}"
            )
        with col4:
            order_lines[i]["unit"] = st.text_input(
                "Unit",
                value=line["unit"],
                key=f"unit_{ec}_{i}",
                placeholder="piece, kg, ect."
            )
        
        # Calculate line total
        calculated_line_total = line["unit_price"] * line["quantity"]
        stated_line_total = line.get("stated_total_price")
        
        with col5:
            order_lines[i]["stated_total_price"] = st.number_input(
                "Stated Total",
                value=float(stated_line_total) if stated_line_total is not None else calculated_line_total,
                min_value=0.0,
                step=0.01,
                key=f"stated_{ec}_{i}"
            )
        
        with col6:
            st.write("Calculated")
            line_mismatch = stated_line_total is not None and abs(stated_line_total - calculated_line_total) > 0.01
            if line_mismatch:
                st.markdown(f"<span style='color: orange; font-weight: bold;'>⚠️ {currency_symbol} {calculated_line_total:,.2f}</span>", unsafe_allow_html=True)
            else:
                st.write(f"{currency_symbol} {calculated_line_total:,.2f}")
        
        with col7:
            st.write("")
            st.write("")
            if len(order_lines) > 1:
                if st.button("🗑️", key=f"del_{ec}_{i}"):
                    order_lines.pop(i)
                    st.rerun()

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("➕ Add Line"):
            order_lines.append({"description": "", "unit_price": 0.0, "quantity": 1.0, "unit": "pieces", "stated_total_price": None})
            st.rerun()

    st.divider()

    # Total Cost Comparison
    calculated_total = sum(line["unit_price"] * line["quantity"] for line in order_lines)
    stated_total = st.session_state.form_data.get("stated_total_cost")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        new_stated_total = st.number_input(
            f"Stated Total Cost ({currency_symbol})",
            value=float(stated_total) if stated_total is not None else calculated_total,
            min_value=0.0,
            step=0.01
        )
        st.session_state.form_data["stated_total_cost"] = new_stated_total
    
    with col2:
        total_mismatch = stated_total is not None and abs(stated_total - calculated_total) > 0.01
        if total_mismatch:
            diff = calculated_total - stated_total
            st.markdown(f"**Calculated Total**")
            st.markdown(f"<span style='font-size: 1.5em; font-weight: bold;'>{currency_symbol} {calculated_total:,.2f}</span> <span style='color: orange; font-weight: bold;'>({diff:+,.2f}) ⚠️</span>", unsafe_allow_html=True)
        else:
            st.metric("Calculated Total", f"{currency_symbol} {calculated_total:,.2f}")

    st.divider()

    # Commodity Group Classification
    st.subheader("Commodity Group")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if st.button("🤖 Re-classify"):
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
    
    # Show current commodity group (from classification or existing data)
    if commodity_group_id:
        if classification_result:
            st.success(f"**Suggested:** {get_commodity_group_display(commodity_group_id)}")
            st.caption(f"Confidence: {classification_result.get('confidence', 0):.0%} - {classification_result.get('rationale', '')}")
        else:
            st.info(f"**Current:** {get_commodity_group_display(commodity_group_id)}")

    # Manual override option
    group_options = {f"{g['id']} - {g['category']} - {g['name']}": g["id"] for g in COMMODITY_GROUPS}
    reverse_options = {v: k for k, v in group_options.items()}
    
    # Find current index for selectbox
    current_display = reverse_options.get(commodity_group_id, "")
    options_list = [""] + list(group_options.keys())
    current_index = options_list.index(current_display) if current_display in options_list else 0
    
    with st.expander("Override commodity group manually"):
        selected = st.selectbox(
            "Select commodity group",
            options=options_list,
            index=current_index
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

    button_label = "💾 Update Request" if edit_mode else "✅ Submit Request"
    
    if st.button(button_label, type="primary", disabled=bool(errors)):
        db = get_db()
        try:
            if edit_mode:
                # Update existing request
                request = db.query(ProcurementRequest).filter(ProcurementRequest.id == edit_request_id).first()
                old_status = request.status
                new_status = st.session_state.form_data.get("status", old_status)
                
                request.requestor_name = requestor_name
                request.title = title
                request.vendor_name = vendor_name
                request.vat_id = vat_id
                request.department = department
                request.commodity_group_id = commodity_group_id
                request.currency = currency
                request.stated_total_cost = st.session_state.form_data.get("stated_total_cost")
                request.pdf_data = st.session_state.get("pdf_data")
                request.pdf_filename = st.session_state.get("pdf_filename")
                request.status = new_status
                
                # Add status history if status changed
                if old_status != new_status:
                    history = StatusHistory(
                        request_id=request.id,
                        from_status=old_status,
                        to_status=new_status,
                        changed_by="user"
                    )
                    db.add(history)
                
                # Delete existing order lines and add new ones
                for line in request.order_lines:
                    db.delete(line)
                
                for line in order_lines:
                    if line["description"] and line["unit_price"] > 0:
                        order_line = OrderLine(
                            request_id=request.id,
                            description=line["description"],
                            unit_price=line["unit_price"],
                            quantity=line["quantity"],
                            unit=line["unit"],
                            stated_total_price=line.get("stated_total_price")
                        )
                        db.add(order_line)
                
                db.commit()
                st.success(f"✅ Request #{request.id} updated successfully!")
                navigate_to_overview(preserve_filters=True)
                st.rerun()
            else:
                # Create new request
                request = ProcurementRequest(
                    requestor_name=requestor_name,
                    title=title,
                    vendor_name=vendor_name,
                    vat_id=vat_id,
                    department=department,
                    commodity_group_id=commodity_group_id,
                    currency=currency,
                    stated_total_cost=st.session_state.form_data.get("stated_total_cost"),
                    status=RequestStatus.OPEN.value,
                    pdf_data=st.session_state.get("pdf_data"),
                    pdf_filename=st.session_state.get("pdf_filename")
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
                            unit=line["unit"],
                            stated_total_price=line.get("stated_total_price")
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
                st.success(f"✅ Request #{request.id} submitted successfully!")
                st.balloons()
            
            # Reset form and edit state
            st.session_state.form_data = {
                "requestor_name": "",
                "title": "",
                "vendor_name": "",
                "vat_id": "",
                "department": "",
                "currency": "EUR",
                "order_lines": [{"description": "", "unit_price": 0.0, "quantity": 1.0, "unit": "pieces", "stated_total_price": None}],
                "stated_total_cost": None,
                "commodity_group_id": None,
                "classification_result": None
            }
            st.session_state.edit_mode = False
            st.session_state.edit_request_id = None
            st.session_state.pdf_data = None
            st.session_state.pdf_filename = None
            st.session_state.last_uploaded_file = None
            
        except Exception as e:
            db.rollback()
            st.error(f"Error saving request: {str(e)}")
        finally:
            db.close()


def show_overview_page():
    st.header("Procurement Requests Overview")
    
    db = get_db()
    
    # Initialize filter state if not exists
    if "overview_status_filter" not in st.session_state:
        st.session_state.overview_status_filter = "All"
    if "overview_search" not in st.session_state:
        st.session_state.overview_search = ""
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_options = ["All", RequestStatus.OPEN.value, RequestStatus.IN_PROGRESS.value, RequestStatus.CLOSED.value]
        status_filter = st.selectbox(
            "Filter by Status",
            status_options,
            index=status_options.index(st.session_state.overview_status_filter)
        )
        st.session_state.overview_status_filter = status_filter
    with col2:
        search = st.text_input("Search (vendor/title)", value=st.session_state.overview_search, placeholder="Search...")
        st.session_state.overview_search = search
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
                    st.markdown(f"<span style='color: orange;'>**Calculated Total:** {currency_symbol} {req.calculated_total_cost:,.2f} ⚠️</span>", unsafe_allow_html=True)
                else:
                    st.write(f"**Total Cost:** {currency_symbol} {req.calculated_total_cost:,.2f}")

            # Order lines
            st.write("**Order Lines:**")
            for line in req.order_lines:
                line_text = f"  - {line.description}: {line.quantity} {line.unit} × {currency_symbol}{line.unit_price:.2f}"
                if line.has_price_mismatch:
                    st.markdown(f"{line_text} = <span style='color: orange;'>Stated: {currency_symbol}{line.stated_total_price:.2f} | Calc: {currency_symbol}{line.calculated_total_price:.2f} ⚠️</span>", unsafe_allow_html=True)
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
            
            with col3:
                if st.button("✏️ Edit", key=f"edit_{req.id}"):
                    db.close()
                    load_request_for_edit(req.id)
                    st.rerun()

            # Status history
            with st.expander("📜 Status History"):
                for h in req.status_history:
                    from_str = h.from_status or "Created"
                    st.write(f"{h.changed_at.strftime('%Y-%m-%d %H:%M')} - {from_str} → {h.to_status} (by {h.changed_by})")

    db.close()


if __name__ == "__main__":
    main()
