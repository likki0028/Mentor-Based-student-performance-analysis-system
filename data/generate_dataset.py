import pandas as pd
import random

# ------------------------------
# CONFIGURATION
# ------------------------------
SECTIONS = {
    "SEC_A": "A",
    "SEC_B": "B",
    "SEC_C": "C"
}

SUBJECTS = ["SUB01", "SUB02", "SUB03", "SUB04", "SUB05"]

DISTRIBUTION = {
    "Good": 0.35,
    "Average": 0.50,
    "Poor": 0.15
}

NOISE_RATIO = 0.05   # 5% noise (REALISTIC)

# ------------------------------
# UNIQUE NAME POOL
# ------------------------------
FIRST_NAMES = [
    "Aarav","Vihaan","Aditya","Arjun","Krishna","Rohit","Rahul","Karthik",
    "Ananya","Priya","Kavya","Sneha","Aishwarya","Nithya","Swathi",
    "Siddharth","Kunal","Rajat","Mayank","Tarun","Ashwin","Lokesh",
    "Sai","Srinivas","Balaji","Mohan","Murali","Sekhar","Raghu"
]

LAST_NAMES = [
    "Sharma","Reddy","Patel","Singh","Verma","Gupta","Rao","Iyer","Naidu",
    "Mehta","Joshi","Kulkarni","Deshmukh","Kapoor","Agarwal","Kumar"
]

FULL_NAMES = [f"{f} {l}" for f in FIRST_NAMES for l in LAST_NAMES]
random.shuffle(FULL_NAMES)
name_index = 0

# ------------------------------
# DATA CONTAINERS
# ------------------------------
students, attendance, marks, previous_perf = [], [], [], []

# ------------------------------
# DATA GENERATION
# ------------------------------
for section_id, prefix in SECTIONS.items():

    student_count = random.randint(60, 70)

    noisy_students = set(
        random.sample(
            range(1, student_count + 1),
            max(1, int(student_count * NOISE_RATIO))
        )
    )

    good = round(student_count * DISTRIBUTION["Good"])
    avg = round(student_count * DISTRIBUTION["Average"])
    poor = student_count - good - avg

    perf_list = ["Good"] * good + ["Average"] * avg + ["Poor"] * poor
    random.shuffle(perf_list)

    for i in range(1, student_count + 1):
        student_id = f"{prefix}{i:03}"
        name = FULL_NAMES[name_index]
        name_index += 1

        perf = perf_list[i - 1]
        is_noisy = i in noisy_students

        students.append([student_id, name, section_id])

        # --------------------------
        # PREVIOUS PERFORMANCE
        # --------------------------
        if perf == "Good":
            cgpa = random.uniform(7.5, 9.5)
            backlogs = 0
        elif perf == "Average":
            cgpa = random.uniform(6.0, 7.4)
            backlogs = random.randint(0, 1)
        else:
            cgpa = random.uniform(4.5, 5.9)
            backlogs = random.randint(2, 4)

        # 🔹 5% noise in CGPA/backlogs
        if is_noisy:
            cgpa = max(4.0, min(9.8, cgpa + random.uniform(-0.7, 0.7)))
            if random.random() < 0.25:
                backlogs = max(0, backlogs + random.choice([-1, 1]))

        previous_perf.append([student_id, round(cgpa, 2), backlogs])

        # --------------------------
        # SUBJECT-WISE DATA
        # --------------------------
        for subject in SUBJECTS:

            if perf == "Good":
                att = random.randint(80, 95)
                mid1, mid2 = random.randint(20, 28), random.randint(20, 28)
                quizzes = [random.randint(3, 5) for _ in range(5)]
                assigns = [random.randint(3, 5) for _ in range(5)]
                external = random.randint(42, 60)

            elif perf == "Average":
                att = random.randint(65, 79)
                mid1, mid2 = random.randint(14, 20), random.randint(14, 20)
                quizzes = [random.randint(2, 4) for _ in range(5)]
                assigns = [random.randint(2, 4) for _ in range(5)]
                external = random.randint(30, 41)

            else:
                att = random.randint(40, 64)
                mid1, mid2 = random.randint(6, 13), random.randint(6, 13)
                quizzes = [random.randint(1, 3) for _ in range(5)]
                assigns = [random.randint(1, 3) for _ in range(5)]
                external = random.randint(18, 29)

            # 🔹 5% realistic noise
            if is_noisy:
                att = max(35, min(100, att + random.randint(-10, 10)))
                mid1 = max(0, min(30, mid1 + random.randint(-4, 4)))
                mid2 = max(0, min(30, mid2 + random.randint(-4, 4)))
                quizzes = [max(0, min(5, q + random.choice([-1, 1]))) for q in quizzes]
                assigns = [max(0, min(5, a + random.choice([-1, 1]))) for a in assigns]
                external = max(0, min(60, external + random.randint(-6, 6)))

            attendance.append([student_id, subject, att])
            marks.append([
                student_id, subject,
                mid1, mid2,
                *quizzes,
                *assigns,
                external
            ])

# ------------------------------
# SAVE FILES
# ------------------------------
pd.DataFrame(students, columns=["student_id","name","section_id"]) \
  .to_csv("data/students.csv", index=False)

pd.DataFrame(attendance, columns=["student_id","subject_id","attendance_percentage"]) \
  .to_csv("data/attendance.csv", index=False)

pd.DataFrame(marks, columns=[
    "student_id","subject_id",
    "mid1","mid2",
    "q1","q2","q3","q4","q5",
    "ass1","ass2","ass3","ass4","ass5",
    "external_marks"
]).to_csv("data/marks.csv", index=False)

pd.DataFrame(previous_perf, columns=["student_id","previous_cgpa","backlogs"]) \
  .to_csv("data/previous_performance.csv", index=False)

print("Dataset generated with ~5% realistic noise")
