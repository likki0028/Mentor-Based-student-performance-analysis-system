"""
Post-process synthetic_students.json to enforce exact CGPA targets.
Also adds backlog counts.

Target distribution (195 students):
  - Below 5.0: ~12 students (High risk)
  - 5.0-6.0: ~12 students  
  - 6.0-7.0: ~30 students
  - 7.0-8.0: ~55 students   (bulk)
  - 8.0-9.0: ~60 students   (bulk)
  - 9.0-9.3: ~14 students
  - 9.3-9.7: ~12 students   (toppers)
  Total: 195
"""
import json
import random
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)
sys.path.insert(0, backend_dir)

random.seed(99)
json_path = os.path.join(script_dir, "synthetic_students.json")

with open(json_path, "r", encoding="utf-8") as f:
    students = json.load(f)

# Sort by current CGPA so we can map them to target bands
students.sort(key=lambda s: s["cgpa"])

# Define target CGPA ranges for each student index band
# 65 students total (Section B only)
# Targets set slightly lower than desired because grade-point rounding pushes CGPAs up
TARGETS = [
    # (count, cgpa_min, cgpa_max)
    (4,  4.2, 4.99),     # struggling
    (5,  5.0, 5.99),     # below average
    (8,  6.0, 6.99),     # average
    (18, 7.0, 7.99),     # good (bulk)
    (20, 8.0, 8.70),     # very good (bulk) — cap at 8.7 to avoid rounding to 9+
    (5,  8.71, 8.99),    # high very good
    (5,  9.0, 9.29),     # excellent (reduced from 9)
]

# Assign target CGPA to each student
target_cgpas = []
for count, cmin, cmax in TARGETS:
    for i in range(count):
        target = round(random.uniform(cmin, cmax), 2)
        target_cgpas.append(target)
target_cgpas.sort()

# Sanity check
assert len(target_cgpas) == len(students), f"Target count {len(target_cgpas)} != student count {len(students)}"

# Now scale each student's marks to hit the target CGPA
from scripts.generate_synthetic_data import CURRICULUM, total_to_grade

def scale_student(student, target_cgpa):
    """Scale all marks proportionally to hit target CGPA."""
    # Current CGPA and target
    current_cgpa = student["cgpa"]
    if current_cgpa == 0:
        current_cgpa = 0.1  # avoid divide by zero
    
    # Calculate scale factor
    # CGPA is grade_point * credits / total_credits
    # grade_point = total_percentage / 10
    # So to change CGPA, we need to scale total_percentage
    # target_pct = target_cgpa * 10 (approximately)
    target_pct = target_cgpa * 10  # e.g., 8.5 CGPA → ~85%
    
    # Calculate current average percentage
    all_scores = []
    for sem in student["semesters"]:
        for subj in sem["subjects"]:
            m = subj["marks"]
            if subj["type"] == "Theory":
                total = m.get("total", 0)
                if total > 0:
                    all_scores.append(total)  # total out of 100
            elif subj["type"] == "Lab":
                total = m.get("total", 0)
                if total > 0:
                    all_scores.append(total)
    
    current_avg = sum(all_scores) / len(all_scores) if all_scores else 50
    if current_avg == 0:
        current_avg = 1
    
    scale = target_pct / current_avg
    
    backlogs = 0
    total_credit_points = 0
    total_credits = 0
    
    for sem in student["semesters"]:
        sem_credits = 0
        sem_grade_points = 0
        
        for subj in sem["subjects"]:
            m = subj["marks"]
            sem_num = sem["semester"]
            subj_info = None
            if sem_num in CURRICULUM:
                for s in CURRICULUM[sem_num]["subjects"]:
                    if s["code"] == subj["code"]:
                        subj_info = s
                        break
            credits = subj_info["credits"] if subj_info else subj.get("credits", 3)
            
            if subj["type"] == "Theory":
                # Scale mid marks
                m["mid1_mcq"] = int(round(max(0, min(10, m["mid1_mcq"] * scale))))
                m["mid1_subjective"] = int(round(max(0, min(20, m["mid1_subjective"] * scale))))
                m["mid1_total"] = m["mid1_mcq"] + m["mid1_subjective"]
                
                m["mid2_mcq"] = int(round(max(0, min(10, m["mid2_mcq"] * scale))))
                m["mid2_subjective"] = int(round(max(0, min(20, m["mid2_subjective"] * scale))))
                m["mid2_total"] = m["mid2_mcq"] + m["mid2_subjective"]
                
                m["mid_avg"] = round((m["mid1_total"] + m["mid2_total"]) / 2)
                
                m["internal_assignments"] = int(round(max(0, min(5, m["internal_assignments"] * scale))))
                m["internal_attendance"] = int(round(max(0, min(5, m["internal_attendance"] * scale))))
                m["internal_total"] = max(0, min(40, m["mid_avg"] + m["internal_assignments"] + m["internal_attendance"]))
                
                m["external"] = int(round(max(0, min(59, m["external"] * scale))))
                m["total"] = m["internal_total"] + m["external"]
                m["total"] = max(0, min(100, m["total"]))
                
                m["is_pass"] = (m["internal_total"] >= 14) and (m["external"] >= 21) and (m["total"] >= 40)
                if m["is_pass"]:
                    gp, grade = total_to_grade(m["total"])
                else:
                    gp, grade = 0, "F"
                    backlogs += 1
                m["grade_point"] = gp
                m["grade"] = grade
                
                if credits > 0:
                    sem_credits += credits
                    sem_grade_points += gp * credits
                    total_credits += credits
                    total_credit_points += gp * credits
                    
            elif subj["type"] == "Lab":
                m["internal_total"] = int(round(max(0, min(40, m["internal_total"] * scale))))
                m["external"] = int(round(max(0, min(59, m["external"] * scale))))
                m["total"] = m["internal_total"] + m["external"]
                m["total"] = max(0, min(100, m["total"]))
                
                m["is_pass"] = (m["internal_total"] >= 14) and (m["external"] >= 21) and (m["total"] >= 40)
                if m["is_pass"]:
                    gp, grade = total_to_grade(m["total"])
                else:
                    gp, grade = 0, "F"
                    backlogs += 1
                m["grade_point"] = gp
                m["grade"] = grade
                
                if credits > 0:
                    sem_credits += credits
                    sem_grade_points += gp * credits
                    total_credits += credits
                    total_credit_points += gp * credits
                    
            else:  # Non-Credit
                m["mid1"] = int(round(max(0, min(40, m["mid1"] * scale))))
                m["mid2"] = int(round(max(0, min(40, m["mid2"] * scale))))
                m["average"] = round((m["mid1"] + m["mid2"]) / 2)
                m["is_pass"] = m["average"] >= 16
                if not m["is_pass"]:
                    backlogs += 1
        
        sem["sgpa"] = round(sem_grade_points / sem_credits, 2) if sem_credits > 0 else 0
    
    student["cgpa"] = round(total_credit_points / total_credits, 2) if total_credits > 0 else 0
    student["backlogs"] = backlogs
    
    # Update risk profile based on new CGPA
    if target_cgpa < 5.5:
        student["risk_profile"] = "High"
    elif target_cgpa < 7.0:
        student["risk_profile"] = "Medium"
    else:
        student["risk_profile"] = "Low"
    
    # Adjust attendance rate to match risk profile
    if student["risk_profile"] == "High":
        student["overall_attendance_rate"] = round(random.uniform(0.40, 0.65), 2)
    elif student["risk_profile"] == "Medium":
        student["overall_attendance_rate"] = round(random.uniform(0.70, 0.82), 2)
    else:
        student["overall_attendance_rate"] = round(random.uniform(0.83, 0.98), 2)

# Apply scaling
for i, student in enumerate(students):
    scale_student(student, target_cgpas[i])

# Re-sort by student_id for consistency
students.sort(key=lambda s: s["student_id"])

# Save
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(students, f, indent=2, ensure_ascii=False)

# Print distribution
cgpas = sorted([s["cgpa"] for s in students])
backlogs_list = [s.get("backlogs", 0) for s in students]
print("=== CGPA DISTRIBUTION ===")
print(f"Min: {cgpas[0]}, Max: {cgpas[-1]}")
print(f"Below 5.0: {sum(1 for c in cgpas if c < 5)}")
print(f"5.0-6.0:   {sum(1 for c in cgpas if 5 <= c < 6)}")
print(f"6.0-7.0:   {sum(1 for c in cgpas if 6 <= c < 7)}")
print(f"7.0-8.0:   {sum(1 for c in cgpas if 7 <= c < 8)}")
print(f"8.0-9.0:   {sum(1 for c in cgpas if 8 <= c < 9)}")
print(f"9.0-9.3:   {sum(1 for c in cgpas if 9 <= c < 9.3)}")
print(f"9.3-9.7:   {sum(1 for c in cgpas if 9.3 <= c <= 9.7)}")
print(f"Above 9.7: {sum(1 for c in cgpas if c > 9.7)}")
print(f"\nTop 5 CGPAs: {cgpas[-5:]}")
print(f"Bottom 5 CGPAs: {cgpas[:5]}")
print(f"\n=== BACKLOGS ===")
print(f"Students with backlogs: {sum(1 for b in backlogs_list if b > 0)}")
print(f"Max backlogs: {max(backlogs_list)}")
print(f"Backlog distribution: 0={sum(1 for b in backlogs_list if b==0)}, 1-3={sum(1 for b in backlogs_list if 1<=b<=3)}, 4+={sum(1 for b in backlogs_list if b>=4)}")
print(f"\n=== RISK PROFILES ===")
print(f"High: {sum(1 for s in students if s['risk_profile'] == 'High')}")
print(f"Medium: {sum(1 for s in students if s['risk_profile'] == 'Medium')}")
print(f"Low: {sum(1 for s in students if s['risk_profile'] == 'Low')}")
print("\nDone! synthetic_students.json updated.")
