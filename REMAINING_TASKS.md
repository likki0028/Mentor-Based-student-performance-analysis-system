# Remaining Tasks for Mentor-Based Student Performance Analysis System

This document outlines the detailed steps required to complete the project. The current state suggests a skeletal structure is in place, but core functionality, data integration, and logic are missing.

---

## 1. Backend Development (FastAPI)

### 1.1. Core Infrastructure & Database
- [ ] **Database Migration/Initialization**:
    - Verify `models/` definitions match the requirements.
    - Create a startup script (`init_db.py`) to initialize tables using `Base.metadata.create_all(bind=engine)`.
    - **Minor:** Ensure `database.py` correctly reads `DATABASE_URL` from `.env`.
- [ ] **Seed Data Script**:
    - Create `scripts/seed_data.py` to populate the database with initial testing data:
        - 1 Admin User.
        - 5-10 Faculty members (Lecturers/Mentors).
        - 50+ Students with varied performance data.
        - Courses, Sections, and mappings between Faculty-Courses-Students.

### 1.2. Authentication Module (`/auth`)
- [ ] **Login Endpoint**:
    - Implement `POST /auth/login` to verify credentials and return JWT access token.
    - **Minor:** Validate hashed passwords using `passlib`.
- [ ] **Current User Dependency**:
    - Implement `get_current_user` in `dependencies.py` to decode JWT and fetch user context.
    - **Minor:** Handle `ExpiredSignatureError` and `JWTClaimsError`.
- [ ] **Registration (Admin Only)**:
    - Implement `POST /auth/register` to create new users (Student/Faculty) with role assignment.

### 1.3. API Routers Implementation
*Currently, routers contain placeholder TODOs. Each must be fully implemented.*

#### **Students Router (`routers/students.py`)**
- [ ] `GET /students/me`: Return profile of the currently logged-in student.
- [ ] `GET /students/{id}`: Return detailed student profile (protected: Admin/Mentor/Faculty).
- [ ] `GET /students/{id}/attendance`: Fetch attendance records for specific student.
- [ ] `GET /students/{id}/marks`: Fetch marks/grades for specific student.

#### **Faculty/Mentor Router (`routers/faculty.py`)**
- [ ] `GET /faculty/dashboard`: Return overview data (total students, classes, pending tasks).
- [ ] `GET /faculty/my-students`: List students assigned to the logged-in mentor.
- [ ] `POST /faculty/remarks`: Add a remark/note to a specific student's profile.

#### **Academic Data Routers (`attendance.py`, `assignments.py`, `quizzes.py`)**
- [ ] **Attendance**: Implement `POST /attendance/mark` (bulk update) and `GET /attendance/report`.
- [ ] **Assignments**: Implement `POST /assignments/create`, `POST /assignments/submit`, `GET /assignments/pending`.
- [ ] **Quizzes**: Implement CRUD for Quizzes and `POST /quizzes/attempt` for student submissions.

### 1.4. ML & Analytics Service (`services/ml_service.py`)
- [ ] **Data Preprocessing**:
    - Write functions to fetch raw student data (attendance %, past grades, assignment completion) and format it for the model.
- [ ] **Model Implementation**:
    - Select a model (e.g., Random Forest or Logistic Regression for "At-Risk" classification).
    - Train the model using the seed data or external dataset.
    - Save the model using `joblib` or `pickle`.
- [ ] **Prediction Endpoint**:
    - Implement `predict_performance(student_id)` method in `MLService`.
    - Integrate this into `routers/analytics.py` to expose `GET /analytics/predict/{student_id}`.

### 1.5. Scheduler & Alerts (`services/alert_service.py`)
- [ ] **Low Attendance Alert**:
    - Create a periodic task (APScheduler) that checks for students with <75% attendance.
    - Generate an `Alert` record in the database for these students.
- [ ] **Performance Alert**:
    - Check for failing grades (<40%) in recent tests and trigger alerts to Mentors.

---

## 2. Frontend Development (React + Vite)

### 2.1. API Layer Refactoring
- [ ] **Create Service Files**:
    - Split `api.js` logic into specialized services in `src/services/`:
        - `auth.service.js`: Login, register, change password.
        - `student.service.js`: Fetch profile, attendance, marks.
        - `faculty.service.js`: Fetch mentee list, post remarks.
        - `analytics.service.js`: Fetch predictions and reports.
- [ ] **Axios Interceptors**:
    - Ensure `api.js` automatically attaches the generic `Authorization: Bearer <token>` header to every request.
    - Global error handler (e.g., redirect to login on 401).

### 2.2. Component Implementation & Data Binding

#### **Authentication**
- [ ] **Login Page**:
    - Wire up the form to `auth.service.login`.
    - Store JWT in `localStorage` and User Object in `AuthContext`.
    - Redirect based on Role (Student -> `/student`, Mentor -> `/mentor`).

#### **Student Dashboard (`StudentDashboard.jsx`)**
- [ ] **Header Section**: Fetch and display actual Student Name and Semester.
- [ ] **Stats Cards**:
    - Replace hardcoded "85%" Attendance with data from `student.service.getAttendanceSummary`.
    - Replace "3.8 CGPA" with calculated CGPA from `student.service.getMarks`.
- [ ] **Recent Alerts**:
    - Fetch real alerts from `GET /alerts/my-alerts`.
- [ ] **Subjects Grid**:
    - Map over actual enrolled courses fetched from API.

#### **Mentor/Lecturer Dashboard**
- [ ] **Student List Table**:
    - create a data table listing all assigned mentees.
    - Columns: Name, Roll No, Attendance %, Avg Marks, Risk Status (from ML).
- [ ] **Detail View**:
    - clicking a student should navigate to `/student/detail` with their ID.
    - **Student Detail Page**: Needs to show deep analytics for that specific student (Graphs/Charts).

#### **Admin Dashboard**
- [ ] **User Management**:
    - UI to Add/Delete Faculty and Students.
    - UI to Assign Mentors to Students.

### 2.3. UI/UX Improvements
- [ ] **Loading States**: Add Skeleton loaders (shimmer effect) while API data is fetching.
- [ ] **Toast Notifications**: Add `react-hot-toast` or similar for success/error messages (e.g., "Login Successful", "Failed to submit assignment").
- [ ] **Charts**: Use `recharts` or `chart.js` to visualize:
    - Attendance trends over time.
    - Marks distribution per subject.

---

## 3. Integration & Testing Implementation

### 3.1. Integration
- [ ] **CORS Configuration**: Ensure Backend `main.py` allows requests from Frontend URL (likely `http://localhost:5173`).
- [ ] **Environment Variables**:
    - Frontend: `.env.local` with `VITE_API_URL`.
    - Backend: `.env` with `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`.

### 3.2. Verification
- [ ] **End-to-End Flow Test**:
    1. Admin creates a Student and a Mentor.
    2. Admin maps Student to Mentor.
    3. Student logs in, sees empty dashboard.
    4. Faculty logs in, adds marks/attendance for Student.
    5. Student refreshes, sees updated stats.
    6. System runs analysis, flags Student as "At Risk" if marks are low.
    7. Mentor sees "At Risk" flag on their dashboard.
