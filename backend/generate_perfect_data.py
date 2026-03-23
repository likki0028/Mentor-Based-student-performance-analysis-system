"""
Perfect Synthetic Data Generator for Section B (65 students)
=============================================================
Uses a top-down approach:
1. Generate exactly 65 target CGPAs based on user requirements.
2. Generate marks for each subject to explicitly hit that CGPA.
3. Automatically apply backlogs only to students below 6.5 CGPA.
"""

import json
import random
import os

random.seed(123)

from scripts.generate_synthetic_data import (
    CURRICULUM, get_indian_name, GENDERS, total_to_grade
)

# --- Configuration ---
NUM_STUDENTS = 65
SECTION = "B"
MIN_CGPA = 4.0
MAX_CGPA = 9.7

# --- 1. Target CGPAs ---
# 15 from 4.0 to 5.5
# 15 from 9.0 to 9.7
# 35 from 5.5 to 9.0 (bulk between 7 and 8.5)
cgp_low = [round(random.uniform(4.0, 5.5), 2) for _ in range(15)]
cgp_high = [round(random.uniform(9.0, 9.7), 2) for _ in range(15)]

def get_risk(cgpa):
    if cgpa < 6.0: return "High"
    if cgpa < 7.5: return "Medium"
    return "Low"

def clamp(val, mn, mx):
    return max(mn, min(mx, val))

# --- Buckets ---
buckets = {
    "low": {"count": 15, "min": 4.0, "max": 5.49, "current": 0},
    "mid": {"count": 35, "min": 5.5, "max": 8.99, "current": 0},
    "high": {"count": 15, "min": 9.0, "max": 9.7, "current": 0}
}

generated_students = []

total_attempts = 0

while True:
    total_attempts += 1
    
    # Pick a random target to generate from
    target_cgpa = random.uniform(4.0, 9.7)
    
    sid = f"23241A67{len(generated_students)+1:02d}"
    gender = random.choice(GENDERS)
    name = get_indian_name(gender)
    risk = get_risk(target_cgpa)
    
    target_pct = target_cgpa * 10
    num_backlogs_target = 0
    if target_cgpa < 5.0:
        num_backlogs_target = random.randint(4, 9)
    elif target_cgpa < 6.0:
        num_backlogs_target = random.randint(1, 4)
    elif target_cgpa < 6.5:
        num_backlogs_target = random.choice([0, 1, 2])
        
    student = {
        "student_id": sid,
        "name": name,
        "section": SECTION,
        "gender": gender,
        "risk_profile": risk,
        "semesters": [],
        "target_cgpa": target_cgpa,
        "backlogs": 0
    }
    
    total_credit_pts, total_credits, actual_backlogs = 0, 0, 0
    all_subjects_count = sum(len(CURRICULUM[s]["subjects"]) for s in range(1, 7))
    backlog_subject_indices = set(random.sample(range(all_subjects_count), num_backlogs_target)) if num_backlogs_target > 0 else set()
    subject_global_idx = 0
    all_assignments, all_attendance = [], []
    
    for sem_num in range(1, 7):
        sem_info = CURRICULUM[sem_num]
        sem_data = {"semester": sem_num, "semester_name": sem_info["name"], "subjects": []}
        sem_credits, sem_grade_pts = 0, 0
        
        for subj in sem_info["subjects"]:
            subj_pct = clamp(target_pct + random.uniform(-6, 6), 0, 100)
            is_backlog = subject_global_idx in backlog_subject_indices
            if is_backlog: subj_pct = random.uniform(20, 38)
            else: subj_pct = clamp(subj_pct, 40, 99)
            
            subject_global_idx += 1
            subj_entry = {"name": subj["name"], "code": subj["code"], "credits": subj["credits"], "type": subj["type"]}
            m = {}
            
            if subj["type"] == "Theory":
                ext_raw, int_raw = subj_pct * 0.60, subj_pct * 0.40
                if target_cgpa > 9.3 and not is_backlog: ext_raw += 2; int_raw += 2
                m["external"] = int(round(clamp(ext_raw, 0, 59)))
                m["internal_total"] = int(round(clamp(int_raw, 0, 40)))
                
                if is_backlog:
                    if random.random() > 0.5: m["external"] = random.randint(5, 19)
                    else: m["internal_total"] = random.randint(5, 12); m["external"] = random.randint(5, 25)
                else:
                    m["external"] = max(21, m["external"]); m["internal_total"] = max(14, m["internal_total"])
                    
                m["total"] = m["external"] + m["internal_total"]
                available = m["internal_total"]
                att_asgn = max(0, min(10, available - random.randint(15, 20) if available > 20 else random.randint(2, 6)))
                if target_cgpa > 8.0: att_asgn = max(8, min(10, available))
                elif target_cgpa < 5.5: att_asgn = max(2, min(6, available))
                    
                m["internal_attendance"] = att_asgn // 2
                m["internal_assignments"] = att_asgn - m["internal_attendance"]
                m["mid_avg"] = available - att_asgn
                
                all_attendance.append(m["internal_attendance"] / 5.0)
                all_assignments.append(m["internal_assignments"] / 5.0)
                
                diff = random.randint(-3, 3)
                m["mid1_total"] = clamp(m["mid_avg"] + diff, 0, 30)
                m["mid2_total"] = clamp((m["mid_avg"] * 2) - m["mid1_total"], 0, 30)
                m["mid_avg"] = round((m["mid1_total"] + m["mid2_total"]) / 2)
                m["mid1_mcq"], m["mid2_mcq"] = int(round(m["mid1_total"] / 3)), int(round(m["mid2_total"] / 3))
                m["mid1_subjective"] = m["mid1_total"] - m["mid1_mcq"]
                m["mid2_subjective"] = m["mid2_total"] - m["mid2_mcq"]
                m["is_pass"] = (m["internal_total"] >= 14) and (m["external"] >= 21) and (m["total"] >= 40)
                
            elif subj["type"] == "Lab":
                ext_raw, int_raw = subj_pct * 0.60, subj_pct * 0.40
                m["external"] = int(round(clamp(ext_raw, 0, 59)))
                m["internal_total"] = int(round(clamp(int_raw, 0, 40)))
                
                if is_backlog: m["external"] = random.randint(5, 19)
                else: m["external"] = max(21, m["external"]); m["internal_total"] = max(14, m["internal_total"])
                    
                m["total"] = m["external"] + m["internal_total"]
                m["is_pass"] = (m["internal_total"] >= 14) and (m["external"] >= 21) and (m["total"] >= 40)
                
            else: # Non-Credit
                avg_raw = subj_pct * 0.40
                m["mid1"] = int(round(clamp(avg_raw + random.randint(-4, 4), 0, 40)))
                m["mid2"] = int(round(clamp(avg_raw * 2 - m["mid1"], 0, 40)))
                m["average"] = round((m["mid1"] + m["mid2"])/2)
                
                if is_backlog:
                    m["average"] = random.randint(5, 14)
                    m["mid1"] = m["mid2"] = m["average"]
                else:
                    m["average"] = max(16, m["average"])
                
                m["is_pass"] = m["average"] >= 16
                m["total"] = m["average"]
            
            if m["is_pass"]:
                gp, grade = total_to_grade(m["total"]) if subj["type"] != "Non-Credit" else (0, "P")
            else:
                gp, grade = 0, "F"
                actual_backlogs += 1
                
            m["grade_point"] = gp
            m["grade"] = grade
            subj_entry["marks"] = m
            sem_data["subjects"].append(subj_entry)
            
            if subj["credits"] > 0 and subj["type"] != "Non-Credit":
                sem_credits += subj["credits"]
                sem_grade_pts += gp * subj["credits"]
                total_credits += subj["credits"]
                total_credit_pts += gp * subj["credits"]
                
        sem_data["sgpa"] = round(sem_grade_pts / sem_credits, 2) if sem_credits > 0 else 0
        sem_data["total_credits"] = sem_credits
        student["semesters"].append(sem_data)
        
    actual_cgpa = round(total_credit_pts / total_credits, 2) if total_credits > 0 else 0
    
    # ----------------------------------------------------
    # BUCKET VALIDATION
    # ----------------------------------------------------
    # Reject out of global bounds
    if actual_cgpa < 4.0 or actual_cgpa > 9.7:
        continue
    
    # Reject rule: Backlogs ONLY for students < 6.5
    if actual_cgpa >= 6.5 and actual_backlogs > 0:
        continue
        
    bucket_found = None
    for bk, b_data in buckets.items():
        if b_data["min"] <= actual_cgpa <= b_data["max"]:
            bucket_found = bk
            break
            
    if not bucket_found:
        continue
        
    if buckets[bucket_found]["current"] < buckets[bucket_found]["count"]:
        # We need this student!
        student["cgpa"] = actual_cgpa
        student["backlogs"] = actual_backlogs
        student["overall_attendance_rate"] = round(sum(all_attendance) / len(all_attendance), 2) if all_attendance else 0.75
        student["overall_assignment_rate"] = round(sum(all_assignments) / len(all_assignments), 2) if all_assignments else 0.75
        
        # Reset ID cleanly
        student["student_id"] = f"23241A67{len(generated_students)+1:02d}"
        
        generated_students.append(student)
        buckets[bucket_found]["current"] += 1
    
    # Check if we are totally done
    if all(b["current"] == b["count"] for b in buckets.values()):
        break

students_data = generated_students

# Save
with open("scripts/synthetic_students.json", "w", encoding="utf-8") as f:
    json.dump(students_data, f, indent=2, ensure_ascii=False)

print("=== PERFECT DATA GENERATION RESULTS ===")
cgpas = sorted([s["cgpa"] for s in students_data])
backs = [s["backlogs"] for s in students_data]
print(f"Total students configured: {len(cgpas)}")
print(f"Min CGPA: {cgpas[0]:.2f}, Max CGPA: {cgpas[-1]:.2f}")
print(f"Below 5.0 (Target 15): {sum(1 for c in cgpas if c < 5.0)}")
print(f"5.0 - 5.5: {sum(1 for c in cgpas if 5.0 <= c < 5.5)}")
print(f"5.5 - 6.5: {sum(1 for c in cgpas if 5.5 <= c < 6.5)}")
print(f"6.5 - 9.0: {sum(1 for c in cgpas if 6.5 <= c < 9.0)}")
print(f"Above 9.0 (Target 15): {sum(1 for c in cgpas if c >= 9.0)}")
print(f"Above 9.3: {sum(1 for c in cgpas if c >= 9.3)}")

print("\n=== BACKLOGS ===")
print(f"Total students with backlogs: {sum(1 for b in backs if b > 0)}")
print(f"Max backlogs: {max(backs)}")
print(f"No Backlogs: {sum(1 for b in backs if b == 0)}")
print(f"Low Backlogs (1-3): {sum(1 for b in backs if 1<=b<=3)}")
print(f"High Backlogs (>3): {sum(1 for b in backs if b>3)}")

# Print 5 random students summary
print("\nSample Students:")
for _ in range(3):
    s = random.choice(students_data)
    print(f" - {s['student_id']}: CGPA {s['cgpa']} | Backlogs: {s['backlogs']} | Target: {s['target_cgpa']}")
