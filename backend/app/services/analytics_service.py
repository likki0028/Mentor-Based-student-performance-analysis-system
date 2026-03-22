
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer
from datetime import date, datetime

from ..models import attendance as attendance_model
from ..models import marks as marks_model
from ..models import student as student_model
from ..models import subject as subject_model
from ..models import alert as alert_model
from ..models import assignment as assignment_model
from ..models import submission as submission_model

class AnalyticsService:
    @staticmethod
    def get_student_analytics(db: Session, student_id: int):
        """Get comprehensive analytics for a student grouped by semester."""
        student = db.query(student_model.Student).filter(
            student_model.Student.id == student_id
        ).first()
        if not student:
            return None

        # --- Base Data Fetching (batch queries) ---
        total_classes = db.query(func.count(attendance_model.Attendance.id)).filter(
            attendance_model.Attendance.student_id == student_id
        ).scalar() or 0

        present_count = db.query(func.sum(
            func.cast(attendance_model.Attendance.status, Integer)
        )).filter(
            attendance_model.Attendance.student_id == student_id
        ).scalar() or 0

        attendance_pct = (present_count / total_classes * 100) if total_classes > 0 else 0

        marks_records = db.query(marks_model.Marks).filter(
            marks_model.Marks.student_id == student_id
        ).all()

        assignments_all = db.query(assignment_model.Assignment).all()
        submissions_all = db.query(submission_model.Submission).filter(
            submission_model.Submission.student_id == student_id
        ).all()

        current_sem = student.current_semester or 6
        subjects = db.query(subject_model.Subject).all()

        # --- BATCH attendance per subject (single query replaces N+1) ---
        att_stats = db.query(
            attendance_model.Attendance.subject_id,
            func.count(attendance_model.Attendance.id),
            func.sum(func.cast(attendance_model.Attendance.status, Integer))
        ).filter(
            attendance_model.Attendance.student_id == student_id
        ).group_by(attendance_model.Attendance.subject_id).all()

        att_map = {row[0]: (row[1] or 0, int(row[2] or 0)) for row in att_stats}

        # Data Structures
        semester_stats = {}  # For Sem 1-5
        current_semester_details = {
            "semester": current_sem,
            "subjects": []
        }

        # Overall running totals (across ALL semesters including current)
        total_completed_credits = 0
        total_grade_points = 0
        cum_att_total = 0
        cum_att_present = 0

        # Current date for assignment logic
        today = date.today()

        for sub in subjects:
            is_completed_sem = sub.semester < current_sem
            sem_num = sub.semester

            # Use pre-fetched attendance (no DB query per subject!)
            sub_att_total, sub_att_present = att_map.get(sub.id, (0, 0))
            sub_att_pct = (sub_att_present / sub_att_total * 100) if sub_att_total > 0 else 0
            sub_marks = [m for m in marks_records if m.subject_id == sub.id]


            # --- COMPLETED SEMESTER LOGIC ---
            if is_completed_sem:
                # Calculate simple percentage to GP
                total_scored = sum(m.score for m in sub_marks)
                total_max = sum(m.total for m in sub_marks)
                
                # Default Grade Point is 0
                grade_point = 0
                if total_max > 0:
                    percentage = (total_scored / total_max) * 100
                    # 10 point scale mapping (Integers for grade points per user request)
                    grade_point = int(round(min(10.0, percentage / 10)))

                if sub_att_total > 0 or sub_marks:
                    if sem_num not in semester_stats:
                        semester_stats[sem_num] = {
                            "semester": sem_num,
                            "subject_stats": [],
                            "attendance_percentage": 0,
                            "sgpa": 0,
                            "total_credits": 0,
                            "earned_points": 0
                        }
                    
                    # Accumulate SGPA/CGPA inputs
                    points = grade_point * sub.credits
                    semester_stats[sem_num]["total_credits"] += sub.credits
                    semester_stats[sem_num]["earned_points"] += points
                    
                    total_completed_credits += sub.credits
                    total_grade_points += points
                    
                    cum_att_total += sub_att_total
                    cum_att_present += sub_att_present

                    semester_stats[sem_num]["subject_stats"].append({
                        "subject_id": sub.id,
                        "subject_name": sub.name,
                        "subject_code": sub.code,
                        "subject_type": sub.subject_type,
                        "credits": sub.credits,
                        "attendance_percentage": round(sub_att_pct, 1),
                        "grade_point": grade_point,
                        "total_classes": sub_att_total,
                        "classes_attended": sub_att_present
                    })

            # --- CURRENT INCOMPLETE SEMESTER LOGIC ---
            elif sem_num == current_sem:
                # Determine assessment_type value regardless of whether SQLAlchemy
                # returns a str enum like "MID_TERM" or an Enum object with .value="mid_term"
                def get_type_val(m):
                    if hasattr(m, 'assessment_type') and m.assessment_type:
                        if hasattr(m.assessment_type, 'value'):
                            return m.assessment_type.value.lower()
                        return str(m.assessment_type).lower().split('.')[-1]
                    return ""

                mid_marks = [m for m in sub_marks if get_type_val(m) in ('mid_term', 'mid_1', 'mid_2')]

                # Calculate sessional marks (average of mid-terms)
                if mid_marks:
                    avg_mid_score = round(sum(m.score for m in mid_marks) / len(mid_marks))
                    # Use the total from the first mark record (usually 30 for theory, 50 for non-credit)
                    sessional_marks = f"{avg_mid_score}/{mid_marks[0].total}"
                else:
                    sessional_marks = "Not Yet Conducted"

                # Process Assignments for this subject
                sub_assignments = [a for a in assignments_all if a.subject_id == sub.id and (a.section_id is None or a.section_id == student.section_id)]
                assignment_progress = []
                submitted_count = 0
                for a in sub_assignments:
                    subm = next((s for s in submissions_all if s.assignment_id == a.id), None)
                    status = "Pending"
                    if subm:
                        status = "Submitted"
                        submitted_count += 1
                    elif a.due_date:
                        try:
                            # Handle string due_date in YYYY-MM-DD format
                            due_dt = datetime.strptime(a.due_date.split(' ')[0], "%Y-%m-%d").date()
                            if today > due_dt:
                                status = "Missing"
                        except:
                            pass
                    assignment_progress.append({
                        "id": a.id,
                        "title": a.title,
                        "due_date": str(a.due_date),
                        "status": status
                    })

                # Override sessional display based on subject type
                subject_type_lower = sub.subject_type.lower() if sub.subject_type else ""
                if subject_type_lower == "lab":
                    internal_lab = next((m for m in sub_marks if get_type_val(m) in ('lab_internal', 'internal')), None)
                    if internal_lab:
                        sessional_marks = f"{internal_lab.score}/{internal_lab.total}"
                    else:
                        sessional_marks = "Internal Exam Not Yet Conducted"
                elif subject_type_lower == "nptel":
                    sessional_marks = "NPTEL - External Exam Only"

                # Calculate overall marks percentage for this subject (from ALL marks)
                sub_total_scored = sum(m.score for m in sub_marks)
                sub_total_max = sum(m.total for m in sub_marks)
                overall_marks_pct = round((sub_total_scored / sub_total_max) * 100, 1) if sub_total_max > 0 else 0

                # Extract individual assessment marks
                mid1_mark = next((m for m in sub_marks if get_type_val(m) in ('mid_1', 'mid_term')), None)
                mid2_mark = next((m for m in sub_marks if get_type_val(m) == 'mid_2'), None)
                lab_internal_mark = next((m for m in sub_marks if get_type_val(m) in ('lab_internal', 'internal')), None)

                # Append to current semester details (including non-credit/0-credit subjects)
                current_semester_details["subjects"].append({
                    "subject_id": sub.id,
                    "subject_name": sub.name,
                    "subject_code": sub.code,
                    "subject_type": sub.subject_type,
                    "credits": sub.credits,
                    "attendance_percentage": round(sub_att_pct, 1),
                    "total_classes": sub_att_total,
                    "classes_attended": sub_att_present,
                    "sessional_marks": sessional_marks,
                    "overall_marks_percentage": overall_marks_pct,
                    "mid_1": f"{mid1_mark.score}/{mid1_mark.total}" if mid1_mark else None,
                    "mid_2": f"{mid2_mark.score}/{mid2_mark.total}" if mid2_mark else None,
                    "lab_internal": f"{lab_internal_mark.score}/{lab_internal_mark.total}" if lab_internal_mark else None,
                    "assignment_count": len(sub_assignments),
                    "assignments_submitted": submitted_count,
                    "assignment_details": assignment_progress
                })


                # Also include current semester in cumulative stats
                cum_att_total += sub_att_total
                cum_att_present += sub_att_present
                if sub_marks and sub.credits > 0:
                    total_scored = sum(m.score for m in sub_marks)
                    total_max = sum(m.total for m in sub_marks)
                    if total_max > 0:
                        percentage = (total_scored / total_max) * 100
                        grade_point = int(round(min(10.0, percentage / 10)))
                    else:
                        grade_point = 0
                    total_completed_credits += sub.credits
                    total_grade_points += grade_point * sub.credits

        # Finalize semester stats (calculate SGPA/Attendance per sem)
        for sem_num, data in semester_stats.items():
            total_sub_att = sum(s["attendance_percentage"] for s in data["subject_stats"])
            data["attendance_percentage"] = round(total_sub_att / len(data["subject_stats"]), 1) if data["subject_stats"] else 0
            
            data["sgpa"] = round(data["earned_points"] / data["total_credits"], 2) if data["total_credits"] > 0 else 0

        # CGPA calculation (only completed semesters)
        cgpa = round(total_grade_points / total_completed_credits, 2) if total_completed_credits > 0 else 0

        # Overall average marks (used for display and fallback risk classification)
        avg_marks_overall = 0
        if marks_records:
            total_pct = sum((m.score / m.total * 100) if m.total > 0 else 0 for m in marks_records)
            avg_marks_overall = total_pct / len(marks_records)

        # Use ML-based risk classification (XGBoost with rule-based fallback)
        try:
            from .ml_service import MLService
            ml_prediction = MLService.predict_risk(db, student_id)
            risk_status = ml_prediction.get("risk_status", AnalyticsService.classify_risk(attendance_pct, avg_marks_overall))
        except Exception:
            risk_status = AnalyticsService.classify_risk(attendance_pct, avg_marks_overall)

        # Recent alerts
        alerts = db.query(alert_model.Alert).filter(
            alert_model.Alert.student_id == student_id
        ).order_by(alert_model.Alert.created_at.desc()).limit(5).all()

        return {
            "student_id": student_id,
            "name": student.user.username if student.user else "Unknown",
            "enrollment_number": student.enrollment_number,
            "current_semester": student.current_semester,
            "attendance_percentage": round(attendance_pct, 1),
            "historical_attendance_percentage": round(cum_att_present / cum_att_total * 100, 1) if cum_att_total > 0 else 0,
            "average_marks": round(avg_marks_overall, 1),
            "total_assessments": len(marks_records),
            "total_classes": total_classes,
            "classes_attended": present_count,
            "risk_status": risk_status,
            "cgpa": cgpa,
            "semester_stats": sorted(list(semester_stats.values()), key=lambda x: x["semester"]),
            "subject_stats": current_semester_details["subjects"],
            "current_semester_details": current_semester_details,
            "recent_alerts": [
                {"id": a.id, "message": a.message, "type": a.type, "is_read": a.is_read, "created_at": str(a.created_at)}
                for a in alerts
            ]
        }

    @staticmethod
    def calculate_average_marks(db: Session, student_id: int) -> float:
        """Calculate simple overall average marks for a student."""
        marks_records = db.query(marks_model.Marks).filter(
            marks_model.Marks.student_id == student_id
        ).all()
        if not marks_records:
            return 0.0
        total_pct = sum((m.score / m.total * 100) if m.total > 0 else 0 for m in marks_records)
        return round(total_pct / len(marks_records), 1)

    @staticmethod
    def classify_risk(attendance_pct: float, avg_marks: float) -> str:
        """Rule-based risk classification."""
        if attendance_pct < 75 or avg_marks < 40:
            return "At Risk"
        elif attendance_pct < 85 or avg_marks < 60:
            return "Warning"
        return "Safe"
