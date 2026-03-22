
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
import csv
import io

from ..database import get_db
from ..models import user as user_model, student as student_model
from ..models import marks as marks_model, attendance as att_model
from ..models.mark_finalization import MarkFinalization
from ..dependencies import get_current_active_user

router = APIRouter()


@router.get("/marks/subject/{subject_id}/section/{section_id}")
async def export_marks_csv(
    subject_id: int,
    section_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    students = db.query(student_model.Student).filter(
        student_model.Student.section_id == section_id
    ).all()

    # Get all marks for these students in this subject
    student_ids = [s.id for s in students]
    all_marks = db.query(marks_model.Marks).filter(
        marks_model.Marks.student_id.in_(student_ids),
        marks_model.Marks.subject_id == subject_id
    ).all()

    # Organize by student
    marks_by_student = {}
    for m in all_marks:
        if m.student_id not in marks_by_student:
            marks_by_student[m.student_id] = {}
        marks_by_student[m.student_id][m.assessment_type.value] = m.score

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["#", "Name", "Enrollment", "Mid 1 (/30)", "Mid 2 (/30)", "Assignment (/5)", "Daily Assessment (/5)", "Internal Total (/40)"])

    for idx, s in enumerate(students, 1):
        name = s.user.username if s.user else "Unknown"
        enrollment = s.enrollment_number or ""
        sm = marks_by_student.get(s.id, {})
        mid1 = sm.get("mid_1", "")
        mid2 = sm.get("mid_2", "")
        assgn = sm.get("assignment", "")
        daily = sm.get("daily_assessment", "")

        # Calculate internal total
        mid_avg = ""
        if mid1 != "" and mid2 != "":
            mid_avg = round((int(mid1) + int(mid2)) / 2)
        internal = ""
        if mid_avg != "" and assgn != "" and daily != "":
            internal = int(mid_avg) + int(assgn) + int(daily)

        writer.writerow([idx, name, enrollment, mid1, mid2, assgn, daily, internal])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=marks_export_{subject_id}.csv"}
    )


@router.get("/attendance/subject/{subject_id}/section/{section_id}")
async def export_attendance_csv(
    subject_id: int,
    section_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    students = db.query(student_model.Student).filter(
        student_model.Student.section_id == section_id
    ).all()

    student_ids = [s.id for s in students]
    all_att = db.query(att_model.Attendance).filter(
        att_model.Attendance.student_id.in_(student_ids),
        att_model.Attendance.subject_id == subject_id
    ).order_by(att_model.Attendance.date).all()

    # Get unique dates
    dates = sorted(set(a.date for a in all_att))

    # Organize: { student_id: { date: status } }
    att_map = {}
    for a in all_att:
        if a.student_id not in att_map:
            att_map[a.student_id] = {}
        att_map[a.student_id][a.date] = a.status

    output = io.StringIO()
    writer = csv.writer(output)
    header = ["#", "Name", "Enrollment"] + [d.strftime("%d-%b") for d in dates] + ["Total Present", "Total Classes", "Percentage"]
    writer.writerow(header)

    for idx, s in enumerate(students, 1):
        name = s.user.username if s.user else "Unknown"
        enrollment = s.enrollment_number or ""
        student_att = att_map.get(s.id, {})
        row = [idx, name, enrollment]
        present = 0
        for d in dates:
            status = student_att.get(d)
            if status is True:
                row.append("P")
                present += 1
            elif status is False:
                row.append("A")
            else:
                row.append("-")
        total = len(dates)
        pct = round((present / total) * 100) if total > 0 else 0
        row.extend([present, total, f"{pct}%"])
        writer.writerow(row)

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=attendance_export_{subject_id}.csv"}
    )


# --- Mark Finalization ---

@router.get("/finalization/subject/{subject_id}/section/{section_id}")
async def get_finalization_status(
    subject_id: int,
    section_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    fin = db.query(MarkFinalization).filter(
        MarkFinalization.subject_id == subject_id,
        MarkFinalization.section_id == section_id
    ).first()
    if not fin:
        return {"is_finalized": False, "finalized_at": None}
    return {
        "is_finalized": fin.is_finalized,
        "finalized_at": fin.finalized_at.isoformat() if fin.finalized_at else None
    }


@router.post("/finalization/subject/{subject_id}/section/{section_id}")
async def finalize_marks(
    subject_id: int,
    section_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    fin = db.query(MarkFinalization).filter(
        MarkFinalization.subject_id == subject_id,
        MarkFinalization.section_id == section_id
    ).first()

    if fin and fin.is_finalized:
        raise HTTPException(status_code=400, detail="Marks already finalized")

    if not fin:
        fin = MarkFinalization(
            subject_id=subject_id,
            section_id=section_id,
            is_finalized=True,
            finalized_by=current_user.id,
            finalized_at=datetime.utcnow()
        )
        db.add(fin)
    else:
        fin.is_finalized = True
        fin.finalized_by = current_user.id
        fin.finalized_at = datetime.utcnow()

    db.commit()
    return {"message": "Marks finalized successfully", "finalized_at": fin.finalized_at.isoformat()}
