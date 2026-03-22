
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer as SqlInt

from ..database import get_db
from ..models import faculty as faculty_model
from ..models import student as student_model
from ..models import user as user_model
from ..models import remark as remark_model
from ..models import attendance as attendance_model
from ..models import alert as alert_model
from ..models import marks as marks_model
from ..models import subject as sub_model
from ..models import section as section_model
from ..schemas import faculty as faculty_schema
from ..dependencies import get_current_active_user
from ..services.ml_service import MLService
from ..services.analytics_service import AnalyticsService

router = APIRouter(
    responses={404: {"description": "Not found"}},
)


def _calc_attendance_pct(db: Session, student_id: int) -> float:
    """Calculate real attendance percentage for a student from the DB."""
    total = db.query(func.count(attendance_model.Attendance.id)).filter(
        attendance_model.Attendance.student_id == student_id
    ).scalar() or 0
    present = db.query(func.sum(
        func.cast(attendance_model.Attendance.status, SqlInt)
    )).filter(
        attendance_model.Attendance.student_id == student_id
    ).scalar() or 0
    return round((present / total * 100), 2) if total > 0 else 0.0


@router.get("/dashboard", response_model=faculty_schema.FacultyDashboard)
async def get_dashboard_stats(
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [user_model.UserRole.MENTOR, user_model.UserRole.LECTURER, user_model.UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get mentor's faculty profile to find assigned students
    fac = db.query(faculty_model.Faculty).filter(
        faculty_model.Faculty.user_id == current_user.id
    ).first()

    if fac:
        students = db.query(student_model.Student).filter(
            student_model.Student.mentor_id == fac.id
        ).all()
    else:
        # If no faculty profile (admin), show all students
        students = db.query(student_model.Student).all()

    total_students = len(students)

    # Count actual at-risk students using ML predictions
    at_risk_count = 0
    recent_alert_msgs = []
    for stu in students:
        prediction = MLService.predict_risk(db, stu.id)
        if prediction.get("risk_status") == "At Risk":
            at_risk_count += 1
            name = stu.user.username if stu.user else "Unknown"
            att = prediction.get("attendance_percentage", 0)
            recent_alert_msgs.append(f"{name} - Attendance: {att}%")

    # Get recent actual alerts (only for these students) - actual Alert objects
    student_ids = [s.id for s in students]
    alerts = db.query(alert_model.Alert).filter(
        alert_model.Alert.student_id.in_(student_ids)
    ).order_by(
        alert_model.Alert.created_at.desc()
    ).limit(8).all()
    
    # Combined alerts (we'll only show DB alerts now to maintain object structure, 
    # as ML alerts are ephemeral strings and don't fit the 'Alert' schema perfectly)
    # The user asked to remove 'Pending Tasks' and keep 'Recent Alerts'.
    
    # Derive section/year info from the mentor's students
    section_name = None
    cur_sem = None
    year = None
    if students:
        first_stu = students[0]
        cur_sem = first_stu.current_semester
        year = (cur_sem + 1) // 2  # sem 1-2 = year 1, 3-4 = year 2, etc.
        if first_stu.section_id:
            sec = db.query(section_model.Section).filter(
                section_model.Section.id == first_stu.section_id
            ).first()
            if sec:
                section_name = sec.name

    return {
        "total_students": total_students,
        "at_risk_count": at_risk_count,
        "recent_alerts": alerts,
        "section_name": section_name,
        "year": year,
        "current_semester": cur_sem
    }


@router.get("/class-performance")
async def get_class_performance(
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get average marks per subject for the mentor's students (current semester only)."""
    if current_user.role not in [user_model.UserRole.MENTOR, user_model.UserRole.LECTURER, user_model.UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")

    fac = db.query(faculty_model.Faculty).filter(
        faculty_model.Faculty.user_id == current_user.id
    ).first()

    if fac:
        students = db.query(student_model.Student).filter(
            student_model.Student.mentor_id == fac.id
        ).all()
    else:
        students = db.query(student_model.Student).all()

    student_ids = [s.id for s in students]
    if not student_ids:
        return []

    # Determine current semester from students
    current_sem = max((s.current_semester for s in students), default=6)

    # Get marks only for current semester subjects
    marks_with_subject = (
        db.query(
            sub_model.Subject.name,
            sub_model.Subject.code,
            sub_model.Subject.subject_type,
            sub_model.Subject.credits,
            func.avg(marks_model.Marks.score * 100.0 / marks_model.Marks.total).label("avg_pct")
        )
        .join(sub_model.Subject, marks_model.Marks.subject_id == sub_model.Subject.id)
        .filter(marks_model.Marks.student_id.in_(student_ids))
        .filter(marks_model.Marks.total > 0)
        .filter(sub_model.Subject.semester == current_sem)
        .group_by(sub_model.Subject.id, sub_model.Subject.name, sub_model.Subject.code, sub_model.Subject.subject_type, sub_model.Subject.credits)
        .all()
    )

    return [
        {
            "subject": f"{row.code}",
            "subject_name": row.name,
            "average": round(float(row.avg_pct), 1),
            "subject_type": str(row.subject_type.value) if hasattr(row.subject_type, 'value') else str(row.subject_type),
            "credits": row.credits
        }
        for row in marks_with_subject
    ]


@router.get("/my-subjects", response_model=List[faculty_schema.SubjectSectionOut])
async def get_my_subjects(
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get subjects and sections taught by the current faculty."""
    fac = db.query(faculty_model.Faculty).filter(faculty_model.Faculty.user_id == current_user.id).first()
    if not fac:
        return []

    from ..models.material import Material
    from ..models.assignment import Assignment
    from ..models.subject import Subject
    from ..models.section import Section
    from ..models.faculty import FacultyAssignment

    # 1. Get explicit assignments from the new table
    explicit_assignments = db.query(FacultyAssignment).filter(FacultyAssignment.faculty_id == fac.id).all()
    results_map = {} # Using a map to avoid duplicates (sub_id, sec_id)

    for record in explicit_assignments:
        key = (record.subject_id, record.section_id)
        if key not in results_map:
            sub = record.subject
            sec = record.section
            if sub and sec:
                results_map[key] = {
                    "subject_id": sub.id,
                    "subject_name": sub.name,
                    "subject_code": sub.code,
                    "section_id": sec.id,
                    "section_name": sec.name
                }

    # 2. Add unique subject-section pairs from Materials and Assignments (legacy/inferred)
    mat_pairs = db.query(Material.subject_id, Material.section_id).filter(Material.faculty_id == fac.id).distinct()
    ass_pairs = db.query(Assignment.subject_id, Assignment.section_id).filter(Assignment.faculty_id == fac.id).distinct()
    
    inferred_pairs = set(mat_pairs.all()) | set(ass_pairs.all())
    
    for sub_id, sec_id in inferred_pairs:
        if sub_id is None or sec_id is None: continue
        key = (sub_id, sec_id)
        if key not in results_map:
            sub = db.query(Subject).filter(Subject.id == sub_id).first()
            sec = db.query(Section).filter(Section.id == sec_id).first()
            if sub and sec:
                results_map[key] = {
                    "subject_id": sub.id,
                    "subject_name": sub.name,
                    "subject_code": sub.code,
                    "section_id": sec.id,
                    "section_name": sec.name
                }
    
    return list(results_map.values())


@router.get("/mentor-assignment-stats")
async def get_mentor_assignment_stats(
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get assignment submission stats for the mentor's students."""
    if current_user.role not in [user_model.UserRole.MENTOR, user_model.UserRole.LECTURER, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    from ..models import assignment as assignment_model
    from ..models import submission as submission_model

    fac = db.query(faculty_model.Faculty).filter(
        faculty_model.Faculty.user_id == current_user.id
    ).first()

    if fac:
        students = db.query(student_model.Student).filter(
            student_model.Student.mentor_id == fac.id
        ).all()
    else:
        students = db.query(student_model.Student).all()

    if not students:
        return []

    student_ids = [s.id for s in students]
    section_ids = list(set(s.section_id for s in students if s.section_id))

    # Get assignments for sections the mentor's students belong to
    assignments = db.query(assignment_model.Assignment).filter(
        assignment_model.Assignment.section_id.in_(section_ids)
    ).order_by(assignment_model.Assignment.id.desc()).all()

    # Get all submissions by the mentor's students for these assignments
    assignment_ids = [a.id for a in assignments]
    submissions = db.query(submission_model.Submission).filter(
        submission_model.Submission.assignment_id.in_(assignment_ids),
        submission_model.Submission.student_id.in_(student_ids)
    ).all() if assignment_ids else []

    # Build a set of (assignment_id, student_id) for quick lookup
    submitted_set = set((sub.assignment_id, sub.student_id) for sub in submissions)

    results = []
    for a in assignments:
        # Only students in this assignment's section
        section_students = [s for s in students if s.section_id == a.section_id]
        total = len(section_students)
        submitted = sum(1 for s in section_students if (a.id, s.id) in submitted_set)
        pending = total - submitted

        # Build list of students who haven't submitted
        not_submitted = []
        for s in section_students:
            if (a.id, s.id) not in submitted_set:
                not_submitted.append({
                    "student_id": s.id,
                    "name": s.user.username if s.user else "Unknown",
                    "enrollment_number": s.enrollment_number or ""
                })

        # Get subject name
        subject = db.query(sub_model.Subject).filter(sub_model.Subject.id == a.subject_id).first()
        section = db.query(section_model.Section).filter(section_model.Section.id == a.section_id).first()

        results.append({
            "id": a.id,
            "title": a.title,
            "subject_name": subject.name if subject else "Unknown",
            "subject_code": subject.code if subject else "",
            "section_name": section.name if section else "",
            "due_date": a.due_date,
            "total_students": total,
            "submitted_count": submitted,
            "pending_count": pending,
            "not_submitted": not_submitted
        })

    return results

@router.post("/assignments", response_model=faculty_schema.FacultyAssignmentOut, status_code=201)
async def create_faculty_assignment(
    assignment: faculty_schema.FacultyAssignmentCreate,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Admin-only: Create a mapping between faculty, subject, and section."""
    if current_user.role != user_model.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can create assignments")
    
    new_assignment = faculty_model.FacultyAssignment(**assignment.dict())
    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)
    return new_assignment


@router.get("/my-students", response_model=List[faculty_schema.StudentSummary])
async def get_my_students(
    section_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Get faculty profile
    fac = db.query(faculty_model.Faculty).filter(
        faculty_model.Faculty.user_id == current_user.id
    ).first()

    query = db.query(student_model.Student)

    if section_id:
        query = query.filter(student_model.Student.section_id == section_id)
    
    # If it's a mentor viewing their own mentees
    if not section_id and not subject_id and fac:
        query = query.filter(student_model.Student.mentor_id == fac.id)
    elif not fac and current_user.role != user_model.UserRole.ADMIN:
        # Fallback for unexpected cases
        return []

    students = query.all()

    results = []
    for stu in students:
        # Real attendance from DB
        att_pct = _calc_attendance_pct(db, stu.id)

        # Calculate average marks
        avg_marks = AnalyticsService.calculate_average_marks(db, stu.id)

        # Use ML-based risk classification (XGBoost)
        ml_prediction = MLService.predict_risk(db, stu.id)
        risk_status = ml_prediction.get("risk_status", AnalyticsService.classify_risk(att_pct, avg_marks))

        # Calculate CGPA from completed semesters
        current_sem = stu.current_semester or 6
        completed_subjects = db.query(sub_model.Subject).filter(
            sub_model.Subject.semester <= current_sem
        ).all()
        total_credits = 0
        total_grade_points = 0
        for subj in completed_subjects:
            sub_marks = db.query(marks_model.Marks).filter(
                marks_model.Marks.student_id == stu.id,
                marks_model.Marks.subject_id == subj.id
            ).all()
            if sub_marks:
                total_scored = sum(m.score for m in sub_marks)
                total_max = sum(m.total for m in sub_marks)
                if total_max > 0:
                    percentage = (total_scored / total_max) * 100
                    grade_point = int(round(min(10.0, percentage / 10)))
                else:
                    grade_point = 0
                total_credits += subj.credits
                total_grade_points += grade_point * subj.credits

        cgpa = round(total_grade_points / total_credits, 2) if total_credits > 0 else 0.0

        summary = faculty_schema.StudentSummary(
            id=stu.id,
            name=stu.user.username if stu.user else "Unknown",
            enrollment_number=stu.enrollment_number,
            current_semester=stu.current_semester or 1,
            attendance_percentage=att_pct,
            average_marks=avg_marks,
            risk_status=risk_status,
            cgpa=cgpa,
        )
        results.append(summary)

    return results



@router.post("/remarks", response_model=faculty_schema.RemarkOut, status_code=201)
async def add_remark(
    remark_data: faculty_schema.RemarkCreate,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add a remark/note to a student's profile."""
    if current_user.role not in [user_model.UserRole.MENTOR, user_model.UserRole.LECTURER, user_model.UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Verify student exists
    student = db.query(student_model.Student).filter(student_model.Student.id == remark_data.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Get faculty profile
    fac = db.query(faculty_model.Faculty).filter(faculty_model.Faculty.user_id == current_user.id).first()
    faculty_id = fac.id if fac else 0

    new_remark = remark_model.Remark(
        student_id=remark_data.student_id,
        faculty_id=faculty_id,
        message=remark_data.message
    )
    db.add(new_remark)
    db.commit()
    db.refresh(new_remark)
    return new_remark


@router.get("/remarks/{student_id}", response_model=List[faculty_schema.RemarkOut])
async def get_remarks(
    student_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all remarks for a student."""
    from ..models.remark import Remark
    remarks = db.query(Remark).filter(
        Remark.student_id == student_id
    ).order_by(Remark.created_at.desc()).all()
    return remarks

@router.get("/sections/{section_id}")
async def get_section_details(
    section_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    from ..models.section import Section
    sec = db.query(Section).filter(Section.id == section_id).first()
    if not sec:
        raise HTTPException(status_code=404, detail="Section not found")
    return sec
