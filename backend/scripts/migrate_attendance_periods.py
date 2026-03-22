"""
Re-seed attendance with correct period numbers (Section B only).
Creates one record per student per period per working day.
"""
import sys, os, random
from datetime import date, timedelta, datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import text
from app.database import SessionLocal
from app.timetable_config import TIMETABLE_B, WEEKDAY_TO_DAY, SHORT_TO_CODE

db = SessionLocal()

# Get all students
students = db.execute(text("SELECT id FROM students ORDER BY id")).fetchall()
student_ids = [r[0] for r in students]
print(f"Students: {len(student_ids)}")

# Get subjects with codes
subjects_rows = db.execute(text("SELECT id, code, name FROM subjects")).fetchall()
code_to_id = {r[1]: r[0] for r in subjects_rows}
print(f"Subjects: {len(subjects_rows)}")
for r in subjects_rows:
    print(f"  {r[1]} -> ID {r[0]} ({r[2]})")

# Assign a random attendance rate per student (60%-95%)
random.seed(42)
student_att_rates = {}
for sid in student_ids:
    student_att_rates[sid] = random.uniform(0.60, 0.95)

# Date range: semester start to yesterday (March 21, 2026)
SEMESTER_START = date(2026, 1, 1)
SIMULATION_DATE = date(2026, 3, 21)

# Festival holidays
HOLIDAYS = {
    "2026-01-01", "2026-01-26", "2026-03-14", "2026-03-30",
    "2026-04-14", "2026-08-15", "2026-08-19", "2026-09-18",
    "2026-10-02", "2026-10-20", "2026-11-10", "2026-11-12", "2026-12-25"
}

# Build working days list
working_days = []
current = SEMESTER_START
while current <= SIMULATION_DATE:
    day_str = str(current)
    weekday = current.weekday()
    day_name = WEEKDAY_TO_DAY.get(weekday)
    
    # Skip Sunday (weekday 6), Friday (training, weekday 4), holidays
    if weekday == 6 or weekday == 4 or day_str in HOLIDAYS:
        current += timedelta(days=1)
        continue
    
    if day_name and TIMETABLE_B.get(day_name):
        working_days.append((current, day_name))
    
    current += timedelta(days=1)

print(f"Working days: {len(working_days)} ({SEMESTER_START} to {SIMULATION_DATE})")

# Generate attendance records
total_inserted = 0
batch = []
BATCH_SIZE = 5000

for di, (day_date, day_name) in enumerate(working_days):
    periods_list = TIMETABLE_B[day_name]  # list of 7 period slots
    date_str = str(day_date)
    
    for period_idx, short_code in enumerate(periods_list):
        if not short_code or short_code == "TRAINING":
            continue
        
        subject_code = SHORT_TO_CODE.get(short_code)
        if not subject_code or subject_code not in code_to_id:
            continue
        
        subject_id = code_to_id[subject_code]
        period_num = period_idx + 1  # 1-indexed
        
        for sid in student_ids:
            att_rate = student_att_rates[sid]
            present = 1 if random.random() < att_rate else 0
            batch.append(f"({sid}, {subject_id}, '{date_str}', {present}, {period_num})")
            total_inserted += 1
        
        # Flush batch
        if len(batch) >= BATCH_SIZE:
            values = ", ".join(batch)
            db.execute(text(f"INSERT INTO attendance (student_id, subject_id, date, status, period) VALUES {values}"))
            db.commit()
            batch = []
    
    if (di + 1) % 10 == 0:
        print(f"  Day {di+1}/{len(working_days)}: {day_date} ({day_name}) — {total_inserted} records so far")

# Final batch
if batch:
    values = ", ".join(batch)
    db.execute(text(f"INSERT INTO attendance (student_id, subject_id, date, status, period) VALUES {values}"))
    db.commit()

final_count = db.execute(text("SELECT COUNT(*) FROM attendance")).scalar()
print(f"\nDone!")
print(f"  Total records inserted: {total_inserted}")
print(f"  DB count: {final_count}")
print(f"  Working days: {len(working_days)}")
print(f"  Students: {len(student_ids)}")

db.close()
