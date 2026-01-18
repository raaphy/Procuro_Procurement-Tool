import streamlit as st
from state import AppPage, navigate, get_db, reset_form
from database.models import ProcurementRequest, OrderLine, StatusHistory, RequestStatus
from views.pdf_helper import show_pdf_preview
from database.commodity_groups import COMMODITY_GROUPS, get_commodity_group_display
from extraction import extract_offer_data_from_pdf, classify_commodity_group

def show_new_request_page():
    """Page for creating a new request"""
    st.header("Create New Procurement Request")
    show_request_form(edit_mode=False, edit_request_id=None)


def show_request_form(edit_mode: bool, edit_request_id: int | None):
    # Form key for resetting all widgets
    if "form_key" not in st.session_state:
        st.session_state.form_key = 0
    fk = st.session_state.form_key
    
    # File upload section
    st.subheader("📄 Upload Vendor Offer (Optional)")
    
    col_upload, col_extract = st.columns([3, 1])
    
    with col_upload:
        uploaded_file = st.file_uploader(
            "Upload a PDF",
            type=["pdf"],
            help="Upload a vendor offer document",
            key=f"pdf_uploader_{fk}"
        )

    # Store PDF when uploaded (without extraction)
    if uploaded_file is not None:
        file_id = (uploaded_file.name, uploaded_file.size)
        if st.session_state.get("last_uploaded_file") != file_id:
            st.session_state.last_uploaded_file = file_id
            pdf_bytes = uploaded_file.read()
            st.session_state.pdf_data = pdf_bytes
            st.session_state.pdf_filename = uploaded_file.name
            st.session_state.extraction_done = False
            st.rerun()

    with col_extract:
        st.write("")  # Spacing
        extract_disabled = st.session_state.get("pdf_data") is None
        if st.button("🔍 Extract Info", disabled=extract_disabled, type="primary"):
            with st.spinner("Extracting data from PDF..."):
                try:
                    extracted = extract_offer_data_from_pdf(st.session_state.pdf_data)

                    if extracted:
                        st.session_state.form_key += 1
                        st.session_state.form_data["requestor_name"] = extracted.get("requestor_name", "") or ""
                        st.session_state.form_data["title"] = extracted.get("title", "") or ""
                        st.session_state.form_data["vendor_name"] = extracted.get("vendor_name", "") or ""
                        st.session_state.form_data["vat_id"] = extracted.get("vat_id", "") or ""
                        st.session_state.form_data["department"] = extracted.get("department", "") or ""
                        st.session_state.form_data["currency"] = extracted.get("currency", "EUR") or "EUR"
                        st.session_state.form_data["stated_total_cost"] = extracted.get("stated_total_cost")

                        if extracted.get("order_lines"):

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
                        if st.session_state.form_data["title"] or any(
                                line["description"] for line in st.session_state.form_data["order_lines"]):
                            result = classify_commodity_group(
                                title=st.session_state.form_data["title"],
                                order_lines=st.session_state.form_data["order_lines"],
                                vendor_name=st.session_state.form_data["vendor_name"],
                                department=st.session_state.form_data["department"]
                            )
                            st.session_state.form_data["commodity_group_id"] = result.get("commodity_group_id")
                            st.session_state.form_data["classification_result"] = result

                        st.session_state.extraction_done = True
                        st.success("✅ Data extracted and classified successfully!")
                        st.rerun()
                    else:
                        st.error("Could not extract data from the document")
                except Exception as e:
                    st.error(f"Error extracting data: {str(e)}")

    # Show PDF preview if available
    if st.session_state.get("pdf_data"):
        show_pdf_preview(st.session_state.pdf_data, st.session_state.get("pdf_filename", "document.pdf"),
                         key_prefix="form")

    st.divider()

    # Form
    st.subheader("Request Details")

    col1, col2 = st.columns(2)

    with col1:
        requestor_name = st.text_input(
            "Requestor Name *",
            value=st.session_state.form_data["requestor_name"],
            placeholder="Max Mustermann",
            key=f"requestor_{fk}"
        )
        vendor_name = st.text_input(
            "Vendor Name *",
            value=st.session_state.form_data["vendor_name"],
            placeholder="Company XYZ",
            key=f"vendor_{fk}"
        )
        department = st.text_input(
            "Department *",
            value=st.session_state.form_data["department"],
            placeholder="Department X",
            key=f"department_{fk}"
        )

    with col2:
        title = st.text_input(
            "Title / Short Description *",
            value=st.session_state.form_data["title"],
            placeholder="Product Name",
            key=f"title_{fk}"
        )
        vat_id = st.text_input(
            "VAT ID (USt-IdNr.) *",
            value=st.session_state.form_data["vat_id"],
            placeholder="DEXXXXXXXXX",
            key=f"vat_id_{fk}"
        )
        col2a, col2b = st.columns(2)
        with col2a:
            currency = st.selectbox(
                "Currency",
                options=["EUR", "USD", "GBP", "CHF"],
                index=["EUR", "USD", "GBP", "CHF"].index(st.session_state.form_data.get("currency", "EUR")),
                key=f"currency_{fk}"
            )
            st.session_state.form_data["currency"] = currency
        with col2b:
            status_options = [RequestStatus.OPEN.value, RequestStatus.IN_PROGRESS.value, RequestStatus.CLOSED.value]
            if edit_mode:
                current_status = st.session_state.form_data.get("status", RequestStatus.OPEN.value)
                status = st.selectbox(
                    "Status",
                    options=status_options,
                    index=status_options.index(current_status),
                    key=f"status_{fk}"
                )
                st.session_state.form_data["status"] = status
            else:
                st.selectbox(
                    "Status",
                    options=[RequestStatus.OPEN.value],
                    index=0,
                    disabled=True,
                    help="New requests are always created with status 'Open'",
                    key=f"status_{fk}"
                )

    st.divider()

    # Order Lines
    st.subheader("Order Lines")

    order_lines = st.session_state.form_data["order_lines"]

    currency_symbol = {"EUR": "€", "USD": "$", "GBP": "£", "CHF": "CHF"}.get(currency, "€")

    for i, line in enumerate(order_lines):
        col1, col2, col3, col4, col5, col6, col7 = st.columns([2.5, 1.2, 0.8, 1, 1.2, 1.2, 0.4])

        with col1:
            order_lines[i]["description"] = st.text_input(
                "Description",
                value=line["description"],
                key=f"desc_{fk}_{i}",
                placeholder="Some Product description"
            )
        with col2:
            order_lines[i]["unit_price"] = st.number_input(
                f"Unit Price ({currency_symbol})",
                value=float(line["unit_price"]),
                step=0.01,
                key=f"price_{fk}_{i}"
            )
        with col3:
            order_lines[i]["quantity"] = st.number_input(
                "Qty",
                value=float(line["quantity"]),
                min_value=0.01,
                step=0.01,
                key=f"qty_{fk}_{i}"
            )
        with col4:
            order_lines[i]["unit"] = st.text_input(
                "Unit",
                value=line["unit"],
                key=f"unit_{fk}_{i}",
                placeholder="piece, kg, ect."
            )

        # Calculate line total
        calculated_line_total = line["unit_price"] * line["quantity"]
        stated_line_total = line.get("stated_total_price")

        with col5:
            order_lines[i]["stated_total_price"] = st.number_input(
                "Stated Total",
                value=float(stated_line_total) if stated_line_total is not None else calculated_line_total,
                step=0.01,
                key=f"stated_{fk}_{i}"
            )

        with col6:
            st.write("Calculated")
            line_mismatch = stated_line_total is not None and abs(stated_line_total - calculated_line_total) > 0.01
            if line_mismatch:
                st.markdown(
                    f"<span style='color: orange; font-weight: bold;'>⚠️ {currency_symbol} {calculated_line_total:,.2f}</span>",
                    unsafe_allow_html=True)
            else:
                st.write(f"{currency_symbol} {calculated_line_total:,.2f}")

        with col7:
            st.write("")
            st.write("")
            if len(order_lines) > 1:
                if st.button("🗑️", key=f"del_{fk}_{i}"):
                    order_lines.pop(i)
                    st.rerun()

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("➕ Add Line"):
            order_lines.append(
                {"description": "", "unit_price": 0.0, "quantity": 1.0, "unit": "pieces", "stated_total_price": None})
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
            step=0.01,
            key=f"stated_total_{fk}"
        )
        st.session_state.form_data["stated_total_cost"] = new_stated_total

    with col2:
        total_mismatch = stated_total is not None and abs(stated_total - calculated_total) > 0.01
        if total_mismatch:
            diff = calculated_total - stated_total
            st.markdown(f"**Calculated Total**")
            st.markdown(
                f"<span style='font-size: 1.5em; font-weight: bold;'>{currency_symbol} {calculated_total:,.2f}</span> <span style='color: orange; font-weight: bold;'>({diff:+,.2f}) ⚠️</span>",
                unsafe_allow_html=True)
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
            st.caption(
                f"Confidence: {classification_result.get('confidence', 0):.0%} - {classification_result.get('rationale', '')}")
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
            index=current_index,
            key=f"commodity_{fk}"
        )
        if selected:
            st.session_state.form_data["commodity_group_id"] = group_options[selected]
            commodity_group_id = group_options[selected]

    st.divider()

    # Validation and Submit
    errors = validate_request_form(requestor_name, title, vendor_name, vat_id, department, order_lines,
                                   commodity_group_id)
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
                navigate(AppPage.OVERVIEW, preserve_filters=True)
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
                reset_form()
                st.rerun()

        except Exception as e:
            db.rollback()
            st.error(f"Error saving request: {str(e)}")
        finally:
            db.close()

def validate_request_form(requestor_name, title, vendor_name, vat_id, department, order_lines, commodity_group_id):
    """Validate form fields and return list of errors"""
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
    return errors
