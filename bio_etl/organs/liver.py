"""
Organ 3: The Liver (Detoxification & Standardization Layer).
Detoxifies chemical mismatches:
- Replaces number words ('forty', 'eighty', 'one seventy') and cleans units ('170cm' -> 170)
- Standardizes name capitalization (Title Case)
- Normalizes blood pressure across variations ('90/70', '90 over 70', '90 by 70', '130-85')
- Harmonizes mixed dates into the user's chosen standard date format
- Calculates height(m) and BMI
- Weighs columns by priority (High, Medium, Low).
  CRITICAL: If a High-priority column is missing, the Liver DOES NOT squash it.
  Instead, it flags the row and sends it to the Immune System for verdict!
"""
import re
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from bio_etl.models import OrganStage, BioLogEvent, PipelineConfig, PriorityLevel, BPFormat, DateFormat


# Word to number dictionary for clinical records
WORD_NUMBERS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    "one hundred": 100, "one sixty": 160, "one sixty five": 165,
    "one seventy": 170, "one seventy five": 175, "one eighty": 180
}


class LiverDetoxifier:
    """
    Simulates liver hepatic detoxification and bile secretion.
    Standardizes types, cleans strings, checks column priorities,
    and forwards questionable records to the Immune System.
    """
    def __init__(self, config: PipelineConfig):
        self.config = config

    def normalize_word_number(self, val: Any) -> Optional[float]:
        """Convert word numbers or unit strings ('forty', '170cm') to float/int."""
        if val is None or val == "":
            return None
        val_str = str(val).strip().lower()
        val_str = re.sub(r'(cm|kg|lbs|years|yrs)', '', val_str).strip()

        if val_str in WORD_NUMBERS:
            return float(WORD_NUMBERS[val_str])
        
        try:
            return float(val_str)
        except ValueError:
            return None

    def normalize_name(self, name_val: Any) -> str:
        """Standardizes name capitalization: 'marydoe' -> 'Marydoe', 'ALICE JOHNSON' -> 'Alice Johnson'."""
        if not name_val:
            return ""
        name_str = str(name_val).strip()
        # Title case while preserving intentional word breaks
        words = name_str.split()
        return " ".join(w.capitalize() for w in words)

    def parse_blood_pressure(self, bp_val: Any) -> Optional[Tuple[int, int]]:
        """
        Parses variations like:
        - 140/90
        - 110 over 70
        - 130-85
        - 90 by 70
        Returns (systolic, diastolic) integers or None.
        """
        if not bp_val:
            return None
        bp_str = str(bp_val).strip().lower()
        # Regex matching systolic and diastolic with various delimiters
        match = re.search(r'(\d{2,3})\s*(?:/|over|-|by|\s)\s*(\d{2,3})', bp_str)
        if match:
            try:
                sys_val = int(match.group(1))
                dia_val = int(match.group(2))
                return sys_val, dia_val
            except ValueError:
                return None
        return None

    def format_blood_pressure(self, systolic: int, diastolic: int) -> str:
        """Formats (sys, dia) according to user standard setting."""
        fmt = self.config.standard_bp_format
        if fmt == BPFormat.OVER:
            return f"{systolic} over {diastolic}"
        elif fmt == BPFormat.DASH:
            return f"{systolic}-{diastolic}"
        elif fmt == BPFormat.BY:
            return f"{systolic} by {diastolic}"
        else:
            return f"{systolic}/{diastolic}"

    def parse_date(self, date_val: Any) -> Optional[datetime]:
        """
        Parses messy date formats:
        - 2023.04.01
        - 15-02-2023
        - 2023/01/15
        - March 5 2023
        """
        if not date_val:
            return None
        date_str = str(date_val).strip()

        patterns = [
            "%Y.%m.%d",
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%B %d %Y",
            "%b %d %Y",
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y"
        ]
        for p in patterns:
            try:
                return datetime.strptime(date_str, p)
            except ValueError:
                continue
        return None

    def format_date(self, dt: datetime) -> str:
        """Formats datetime according to user standard setting."""
        fmt = self.config.standard_date_format
        if fmt == DateFormat.DMY_DASH:
            return dt.strftime("%d-%m-%Y")
        elif fmt == DateFormat.MDY_SLASH:
            return dt.strftime("%m/%d/%Y")
        elif fmt == DateFormat.YMD_DOT:
            return dt.strftime("%Y.%m.%d")
        else:
            return dt.strftime("%Y-%m-%d")

    def normalize_gender(self, gender_val: Any) -> Optional[str]:
        """Normalizes gender: 'FEMALE', 'f', 'F' -> 'Female'; 'MALE', 'm', 'M' -> 'Male'."""
        if not gender_val:
            return None
        g = str(gender_val).strip().lower()
        if g in ['m', 'male']:
            return "Male"
        elif g in ['f', 'female']:
            return "Female"
        return g.capitalize()

    def normalize_boolean_choice(self, val: Any) -> Optional[str]:
        """Normalizes 'y', 'yes', 'YES' -> 'Yes'; 'n', 'no', 'NO' -> 'No'."""
        if not val:
            return None
        v = str(val).strip().lower()
        if v in ['y', 'yes']:
            return "Yes"
        elif v in ['n', 'no']:
            return "No"
        elif v in ['occasionally']:
            return "Occasionally"
        return v.capitalize()

    def detoxify_chunk(
        self,
        acidified_chunk: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[BioLogEvent], int]:
        """
        Runs liver enzymatic cleaning across all rows in the acidified chunk.
        Checks column priorities and flags high-priority violations for the Immune System.
        """
        events = []
        normalized_rows: List[Dict[str, Any]] = []
        normalizations_count = 0
        event_id = str(uuid.uuid4())[:8]

        chunk_idx = acidified_chunk[0]["_meta"]["_chunk_idx"] if acidified_chunk else 0

        events.append(BioLogEvent(
            id=f"liver-bile-intro-{chunk_idx}-{event_id}",
            timestamp=time.time(),
            stage=OrganStage.LIVER,
            chunk_idx=chunk_idx,
            action="Liver Secretion & Detoxification",
            reason=f"Liver secreting bile juice over Chunk #{chunk_idx + 1}. Harmonizing types, dates, and BP formats.",
            details={"chunk_size": len(acidified_chunk)}
        ))

        for row in acidified_chunk:
            meta = row.get("_meta", {})
            row_idx = meta.get("_row_idx", 0)

            # Map raw fields flexibly (handling case differences)
            def get_f(keys: List[str]) -> str:
                for k in keys:
                    for rk in row.keys():
                        if rk.lower().replace(" ", "").replace("_", "").replace("(", "").replace(")", "") == k.lower().replace(" ", "").replace("_", "").replace("(", "").replace(")", ""):
                            return str(row[rk]).strip() if row[rk] is not None else ""
                return ""

            raw_pid = get_f(["Patient ID", "patientid", "PID"])
            raw_name = get_f(["Name", "name"])
            raw_gender = get_f(["Gender", "gender"])
            raw_age = get_f(["Age", "age"])
            raw_height = get_f(["Height_cm", "height(cm)", "height_cm", "height"])
            raw_weight = get_f(["Weight_kg", "weight(kg)", "weight_kg", "weight"])
            raw_bp = get_f(["Blood Pressure", "bloodpressure", "bp"])
            raw_diabetes = get_f(["Diabetes", "diabetes"])
            raw_smoker = get_f(["Smoker", "smoker"])
            raw_date = get_f(["Date of Visit", "dateofvisit", "date"])
            raw_diagnosis = get_f(["Diagnosis", "diagnosis"])

            cleaned_record: Dict[str, Any] = {}
            row_changes = 0

            # 1. Patient ID
            cleaned_record["patientid"] = raw_pid.strip()

            # 2. Name
            norm_name = self.normalize_name(raw_name)
            if norm_name != raw_name:
                row_changes += 1
            cleaned_record["name"] = norm_name

            # 3. Gender
            norm_gender = self.normalize_gender(raw_gender)
            if norm_gender and norm_gender != raw_gender:
                row_changes += 1
            cleaned_record["gender"] = norm_gender

            # 4. Age
            norm_age = self.normalize_word_number(raw_age)
            if norm_age is not None:
                norm_age = int(norm_age)
                if str(norm_age) != str(raw_age):
                    row_changes += 1
            cleaned_record["age"] = norm_age

            # 5. Height (cm) & Height (m)
            norm_height_cm = self.normalize_word_number(raw_height)
            if norm_height_cm is not None:
                norm_height_cm = int(round(norm_height_cm))
                if str(norm_height_cm) != str(raw_height):
                    row_changes += 1
                norm_height_m = round(norm_height_cm / 100.0, 2)
            else:
                norm_height_m = None
            cleaned_record["height(cm)"] = norm_height_cm
            cleaned_record["height(m)"] = norm_height_m

            # 6. Weight (kg)
            norm_weight_kg = self.normalize_word_number(raw_weight)
            if norm_weight_kg is not None:
                norm_weight_kg = int(round(norm_weight_kg))
                if str(norm_weight_kg) != str(raw_weight):
                    row_changes += 1
            cleaned_record["weight(kg)"] = norm_weight_kg

            # 7. BMI
            if norm_weight_kg and norm_height_m and norm_height_m > 0:
                calc_bmi = round(norm_weight_kg / (norm_height_m ** 2), 1)
            else:
                calc_bmi = None
            cleaned_record["bmi"] = calc_bmi

            # 8. Blood Pressure
            parsed_bp = self.parse_blood_pressure(raw_bp)
            if parsed_bp:
                norm_bp = self.format_blood_pressure(parsed_bp[0], parsed_bp[1])
                if norm_bp != raw_bp:
                    row_changes += 1
                cleaned_record["bloodpressure"] = norm_bp
            else:
                cleaned_record["bloodpressure"] = None

            # 9. Diabetes
            norm_diabetes = self.normalize_boolean_choice(raw_diabetes)
            if norm_diabetes and norm_diabetes != raw_diabetes:
                row_changes += 1
            cleaned_record["diabetes"] = norm_diabetes

            # 10. Smoker
            norm_smoker = self.normalize_boolean_choice(raw_smoker)
            if norm_smoker and norm_smoker != raw_smoker:
                row_changes += 1
            cleaned_record["smoker"] = norm_smoker

            # 11. Date of Visit & Year of Visit
            parsed_dt = self.parse_date(raw_date)
            if parsed_dt:
                norm_date = self.format_date(parsed_dt)
                year_visit = parsed_dt.year
                if norm_date != raw_date:
                    row_changes += 1
                cleaned_record["dateofvisit"] = norm_date
                cleaned_record["yearofvisit"] = year_visit
            else:
                cleaned_record["dateofvisit"] = None
                cleaned_record["yearofvisit"] = None

            # 12. Diagnosis
            diag_str = raw_diagnosis.strip()
            if diag_str.lower() in ["none", "null", "nil"]:
                diag_clean = "none"
            elif diag_str:
                diag_clean = diag_str.title()
            else:
                diag_clean = None
            cleaned_record["diagnosis"] = diag_clean

            normalizations_count += row_changes

            # Priority Evaluation:
            # Check user-configured priorities for each field
            flag_squash = False
            squash_reasons = []
            violated_cols = []

            # Mapping for priority check
            field_check_map = {
                "Patient ID": cleaned_record["patientid"],
                "Name": cleaned_record["name"],
                "Age": cleaned_record["age"],
                "Gender": cleaned_record["gender"],
                "Height_cm": cleaned_record["height(cm)"],
                "Weight_kg": cleaned_record["weight(kg)"],
                "Blood Pressure": cleaned_record["bloodpressure"],
                "Diabetes": cleaned_record["diabetes"],
                "Smoker": cleaned_record["smoker"],
                "Date of Visit": cleaned_record["dateofvisit"],
                "Diagnosis": cleaned_record["diagnosis"]
            }

            for col_name, priority in self.config.column_priorities.items():
                val = field_check_map.get(col_name)
                is_missing = (val is None or val == "" or str(val).lower() == "none")
                if is_missing and priority == PriorityLevel.HIGH:
                    flag_squash = True
                    squash_reasons.append(f"High-priority field '{col_name}' is missing or empty")
                    violated_cols.append(col_name)

            meta["_flagged_for_squash"] = flag_squash
            meta["_squash_reasons"] = squash_reasons
            meta["_violated_priorities"] = violated_cols
            meta["_cleaned"] = cleaned_record
            row["_meta"] = meta

            if flag_squash:
                events.append(BioLogEvent(
                    id=f"liver-flag-{row_idx}-{event_id}",
                    timestamp=time.time(),
                    stage=OrganStage.LIVER,
                    chunk_idx=chunk_idx,
                    row_idx=row_idx,
                    patient_id=cleaned_record["patientid"] or f"Row-{row_idx}",
                    action="Liver High-Priority Flag",
                    reason=f"Row flagged: {', '.join(squash_reasons)}. Forwarding to Immune System for judgment.",
                    details={"violated_columns": violated_cols}
                ))
            elif row_changes > 0:
                events.append(BioLogEvent(
                    id=f"liver-clean-{row_idx}-{event_id}",
                    timestamp=time.time(),
                    stage=OrganStage.LIVER,
                    chunk_idx=chunk_idx,
                    row_idx=row_idx,
                    patient_id=cleaned_record["patientid"] or f"Row-{row_idx}",
                    action="Hepatic Bile Detox",
                    reason=f"Detoxified {row_changes} fields in {cleaned_record['patientid'] or 'record'}.",
                    details={"changes": row_changes}
                ))

            normalized_rows.append(row)

        return normalized_rows, events, normalizations_count

