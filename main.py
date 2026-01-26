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
    import pandas as pd

    user = st.session_state.user
    section_id = user["section_id"]

    st.title("👨‍🏫 Mentor Dashboard")
    st.subheader(f"Section: {section_id}")

    # -------------------------------
    # LOAD DATA
    # -------------------------------
    students = pd.read_csv("data/students.csv")
    attendance = pd.read_csv("data/attendance.csv")
    marks = pd.read_csv("data/marks.csv")

    # -------------------------------
    # FILTER SECTION STUDENTS
    # -------------------------------
    section_students = students[students["section_id"] == section_id]

    # -------------------------------
    # AGGREGATE ATTENDANCE
    # -------------------------------
    avg_attendance = (
        attendance
        .groupby("student_id")["attendance_percentage"]
        .mean()
        .reset_index()
    )

    # -------------------------------
    # CALCULATE TOTAL MARKS
    # -------------------------------
    # -------------------------------
    # CALCULATE INTERNAL & TOTAL MARKS
    # -------------------------------

    # Average of mids (out of 30)
    marks["avg_mids"] = (marks["mid1"] + marks["mid2"]) / 2

    # Average of quizzes (out of 5)
    quiz_cols = ["q1", "q2", "q3", "q4", "q5"]
    marks["avg_quizzes"] = marks[quiz_cols].mean(axis=1)

    # Average of assignments (out of 5)
    ass_cols = ["ass1", "ass2", "ass3", "ass4", "ass5"]
    marks["avg_assignments"] = marks[ass_cols].mean(axis=1)

    # Internal marks (out of 40)
    marks["internal_marks"] = (
        marks["avg_mids"] +
        marks["avg_quizzes"] +
        marks["avg_assignments"]
    )

    # Total marks (out of 100)
    marks["total_marks"] = marks["internal_marks"] + marks["external_marks"]

    # -------------------------------
    # AGGREGATE PER STUDENT
    # -------------------------------
    avg_marks = (
        marks
        .groupby("student_id")["total_marks"]
        .mean()
        .reset_index()
    )


    # -------------------------------
    # MERGE DATA
    # -------------------------------
    report = section_students.merge(avg_attendance, on="student_id")
    report = report.merge(avg_marks, on="student_id")

    report.rename(columns={
        "name": "Student Name",
        "attendance_percentage": "Avg Attendance (%)",
        "total_marks": "Avg Total Marks"
    }, inplace=True)

    # -------------------------------
    # RISK CLASSIFICATION (RULE-BASED)
    # -------------------------------
    def classify(row):
        if row["Avg Attendance (%)"] >= 75 and row["Avg Total Marks"] >= 60:
            return "Good"
        elif row["Avg Attendance (%)"] >= 60 and row["Avg Total Marks"] >= 45:
            return "Average"
        else:
            return "At-Risk"

    report["Risk Level"] = report.apply(classify, axis=1)

    # -------------------------------
    # DISPLAY TABLE
    # -------------------------------
    st.subheader("📊 Student Performance Overview")

    st.dataframe(
        report[[
            "Student Name",
            "Avg Attendance (%)",
            "Avg Total Marks",
            "Risk Level"
        ]],
        use_container_width=True
    )

    # -------------------------------
    # QUICK INSIGHTS
    # -------------------------------
    st.subheader("📌 Risk Summary")

    col1, col2, col3 = st.columns(3)

    col1.metric("Good", (report["Risk Level"] == "Good").sum())
    col2.metric("Average", (report["Risk Level"] == "Average").sum())
    col3.metric("At-Risk", (report["Risk Level"] == "At-Risk").sum())


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
