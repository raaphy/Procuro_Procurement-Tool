import base64
import streamlit as st


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
        if st.button("👁️ Show Preview" if not st.session_state[preview_key] else "🙈 Hide Preview",
                     key=f"{key_prefix}_toggle_{filename}"):
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