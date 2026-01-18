import streamlit as st
from database.database import init_db
from state import init_session_state

st.set_page_config(page_title="Procuro", page_icon="📋", layout="wide")

# Initialize database
init_db()
init_session_state()

st.title("📋 Procuro")
st.caption("Procurement Request Management System")

st.markdown("""
## Welcome to Procuro

Use the sidebar to navigate:
- **New Request** - Create a new procurement request
- **Request Overview** - View and manage existing requests
""")
