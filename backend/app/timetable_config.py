"""
Section B Timetable Configuration
Periods: P1(9:00), P2(9:50), P3(10:40), P4(11:30), Lunch, P5(12:55), P6(1:50), P7(2:40)
"""

# Subject short code -> DB subject code mapping
SHORT_TO_CODE = {
    "ML": "GR22A3140",
    "ACD": "GR22A3115",
    "BDA": "GR22A3143",
    "CNS": "GR22A4048",
    "NPTEL": "NPTEL",
    "ML LAB": "GR22A3142",
    "BDA LAB": "GR22A3148",
    "MP": "GR22A3089",
    "COI": "GR22A2003",
}

# Reverse map: DB code -> short code
CODE_TO_SHORT = {v: k for k, v in SHORT_TO_CODE.items() if v}

# Section B timetable: day -> list of 7 periods (index 0 = P1, index 6 = P7)
TIMETABLE_B = {
    "MON": ["NPTEL", "ML LAB", "ML LAB", "ML LAB", "ACD", "ACD", "CNS"],
    "TUE": ["CNS", "MP", "MP", "MP", "BDA", "BDA", "NPTEL"],
    "WED": ["COI", "BDA LAB", "BDA LAB", "BDA LAB", "ML", "ML", "NPTEL"],
    "THU": ["CNS", "BDA", "ML", "ML", "ACD", "COI", "COI"],
    "FRI": None,  # Training day — no attendance
    "SAT": ["ACD", "ACD", "BDA", "BDA", "CNS", "CNS", "ML"],
}

# Weekday number (0=Monday) to day abbreviation
WEEKDAY_TO_DAY = {
    0: "MON", 1: "TUE", 2: "WED", 3: "THU", 4: "FRI", 5: "SAT"
}


def get_day_from_date(d) -> str | None:
    """Convert a date to day abbreviation (MON, TUE, etc). Returns None for Sunday."""
    wd = d.weekday()
    return WEEKDAY_TO_DAY.get(wd)


def get_periods_for_subject(subject_code: str, day_name: str) -> list[int]:
    """
    Returns list of period numbers (1-7) for a subject on a given day.
    Uses the DB subject code (e.g., 'GR22A3140') to look up the timetable.
    Returns empty list if no periods found or if it's a training day.
    """
    if not day_name or day_name == "SUN":
        return []

    periods_list = TIMETABLE_B.get(day_name)
    if periods_list is None:  # Training day (FRI)
        return []

    # Convert DB subject code to short code
    short = CODE_TO_SHORT.get(subject_code, subject_code)

    # Find which periods (1-indexed) match this subject
    result = []
    for i, slot in enumerate(periods_list):
        if slot == short:
            result.append(i + 1)  # 1-indexed

    return result
