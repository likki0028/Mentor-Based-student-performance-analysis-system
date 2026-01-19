import streamlit as st
import pandas as pd

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(
    page_title="Dataset Overview",
    layout="wide"
)

st.title("📊 Dataset Overview")
st.caption("Mentor-Based Student Performance Analysis System")
st.divider()

# -------------------------------
# LOAD DATA
# -------------------------------
students = pd.read_csv("data/students.csv")
sections = pd.read_csv("data/sections.csv")
subjects = pd.read_csv("data/subjects.csv")
faculty = pd.read_csv("data/faculty.csv")
faculty_map = pd.read_csv("data/faculty_subject_mapping.csv")
users = pd.read_csv("data/users.csv")
attendance = pd.read_csv("data/attendance.csv")
marks = pd.read_csv("data/marks.csv")
previous = pd.read_csv("data/previous_performance.csv")

# ==================================================
# 1️⃣ ACADEMIC STRUCTURE
# ==================================================
st.subheader("🎓 Academic Structure")

st.markdown(
    """
    These tables define the **core academic structure** of the system:
    students, sections, and subjects.
    """
)

col1, col2 = st.columns(2)

with col1:
    st.markdown("**👨‍🎓 Students per Section**")
    st.dataframe(
        students.groupby("section_id")
        .size()
        .reset_index(name="Number of Students"),
        use_container_width=True,
        hide_index=True
    )

with col2:
    with st.expander("📄 Sample Students"):
        st.dataframe(
            students.rename(columns={
                "student_id": "Student ID",
                "name": "Student Name",
                "section_id": "Section"
            }).head(6),
            use_container_width=True,
            hide_index=True
        )

with st.expander("🏫 Sections (Mentor Mapping)"):
    st.dataframe(
        sections.rename(columns={
            "section_id": "Section ID",
            "section_name": "Section Name",
            "mentor_id": "Mentor Faculty ID"
        }),
        use_container_width=True,
        hide_index=True
    )

with st.expander("📚 Subjects Offered"):
    st.dataframe(
        subjects.rename(columns={
            "subject_id": "Subject Code",
            "subject_name": "Subject Name",
            "subject_type": "Type"
        }),
        use_container_width=True,
        hide_index=True
    )

st.divider()

# ==================================================
# 2️⃣ FACULTY & ROLE MANAGEMENT
# ==================================================
st.subheader("👨‍🏫 Faculty & Role Management")

st.markdown(
    """
    These tables define **faculty details**, **login roles**, and
    **which faculty teaches which subject to which section**.
    """
)

col3, col4 = st.columns(2)

with col3:
    st.markdown("**👤 Faculty Details**")
    st.dataframe(
        faculty.rename(columns={
            "faculty_id": "Faculty ID",
            "faculty_name": "Faculty Name",
            "role": "Faculty Role"
        }),
        use_container_width=True,
        hide_index=True
    )

with col4:
    st.markdown("**🔐 System Users & Roles**")
    st.dataframe(
        users.rename(columns={
            "user_id": "User ID",
            "username": "Username",
            "role": "System Role",
            "faculty_id": "Faculty ID",
            "section_id": "Mentor Section"
        }),
        use_container_width=True,
        hide_index=True
    )

with st.expander("📌 Faculty – Subject – Section Mapping"):
    st.dataframe(
        faculty_map.rename(columns={
            "faculty_id": "Faculty ID",
            "subject_id": "Subject Code",
            "section_id": "Section"
        }),
        use_container_width=True,
        hide_index=True
    )

st.divider()

# ==================================================
# 3️⃣ ACADEMIC RECORDS
# ==================================================
st.subheader("📝 Academic Records")

st.markdown(
    """
    These datasets store **student academic performance**.
    Data is entered by lecturers and monitored by mentors.
    """
)

col5, col6 = st.columns(2)

with col5:
    st.markdown("**📅 Attendance Summary (Subject-wise Average)**")
    st.dataframe(
        attendance.groupby("subject_id")["attendance_percentage"]
        .mean()
        .round(2)
        .reset_index(name="Average Attendance (%)"),
        use_container_width=True,
        hide_index=True
    )

with col6:
    st.markdown("**📈 Previous CGPA Statistics**")
    st.dataframe(
        previous["previous_cgpa"]
        .describe()
        .round(2)
        .reset_index()
        .rename(columns={
            "index": "Metric",
            "previous_cgpa": "CGPA"
        }),
        use_container_width=True,
        hide_index=True
    )

with st.expander("📝 Sample Marks Records"):
    st.dataframe(
        marks.head(6),
        use_container_width=True,
        hide_index=True
    )

with st.expander("📄 Sample Attendance Records"):
    st.dataframe(
        attendance.head(6),
        use_container_width=True,
        hide_index=True
    )

with st.expander("📄 Sample Previous Performance Records"):
    st.dataframe(
        previous.head(6),
        use_container_width=True,
        hide_index=True
    )

st.divider()

# ==================================================
# FINAL SUMMARY
# ==================================================
st.success(
    """
    ✅ **Complete Dataset Explanation**
    
    - 9 fully linked datasets  
    - Clear student–section–mentor relationship  
    - Faculty act as lecturers and mentors  
    - Subject-wise academic tracking  
    - Realistic, noise-added student data  
    """
)
