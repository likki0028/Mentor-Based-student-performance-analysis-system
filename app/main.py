import streamlit as st
from utils.auth import authenticate


# ---------------------------------
# PAGE CONFIG
# ---------------------------------
st.set_page_config(
    page_title="Mentor-Based Student Performance System",
    layout="wide"
)

# ---------------------------------
# SESSION INIT
# ---------------------------------
if "user" not in st.session_state:
    st.session_state.user = None

if "active_role" not in st.session_state:
    st.session_state.active_role = None

# ---------------------------------
# LOGIN PAGE
# ---------------------------------
def login_page():
    st.title("🔐 Login")
    st.caption("Mentor-Based Student Performance Analysis System")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = authenticate(username.strip(), password.strip())

        if user:
            st.session_state.user = user
            st.session_state.active_role = None
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid username or password")

# ---------------------------------
# SIDEBAR (ROLE SWITCH + LOGOUT)
# ---------------------------------
def sidebar_controls():
    user = st.session_state.user
    role = user["role"]

    with st.sidebar:
        st.markdown("### 👤 Logged in as")
        st.write(user["username"])

        # Role switcher only for dual-role users
        if role == "both":
            selected = st.radio(
                "Switch Role",
                ["Mentor", "Lecturer"],
                index=0 if st.session_state.active_role != "Lecturer" else 1
            )
            st.session_state.active_role = selected

        st.divider()

        if st.button("🚪 Logout"):
            logout()

# ---------------------------------
# DASHBOARDS
# ---------------------------------
def mentor_dashboard():
    user = st.session_state.user

    st.title("👨‍🏫 Mentor Dashboard")
    st.write(f"**Section:** {user['section_id']}")
    st.info("Mentor analytics will appear here")

def lecturer_dashboard():
    user = st.session_state.user

    st.title("🧑‍🏫 Lecturer Dashboard")
    st.write(f"**Faculty ID:** {user['faculty_id']}")
    st.info("Lecturer data entry features will appear here")

# ---------------------------------
# LOGOUT
# ---------------------------------
def logout():
    st.session_state.user = None
    st.session_state.active_role = None
    st.rerun()

# ---------------------------------
# MAIN FLOW
# ---------------------------------
if st.session_state.user is None:
    login_page()

else:
    sidebar_controls()

    user_role = st.session_state.user["role"]

    # Single-role users
    if user_role == "mentor":
        mentor_dashboard()

    elif user_role == "lecturer":
        lecturer_dashboard()

    # Dual-role users
    elif user_role == "both":
        if st.session_state.active_role is None:
            st.title("Select Role")
            role = st.radio("Login as:", ["Mentor", "Lecturer"])

            if st.button("Continue"):
                st.session_state.active_role = role
                st.rerun()
        else:
            if st.session_state.active_role == "Mentor":
                mentor_dashboard()
            else:
                lecturer_dashboard()
