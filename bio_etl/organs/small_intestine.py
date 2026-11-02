"""
Organ 5: The Small Intestine (Absorption & Villi Layer).
Simulates nutrient absorption through intestinal villi and microvilli into the bloodstream.
1. Imputes remaining missing non-critical attributes using mode/median nutrient enrichment.
2. Deduplicates records to ensure pure cellular nourishment.
3. Calculates cohort health statistics (average age, average BMI, % chronic illness, etc.).
4. Integrates with the detachable AI Intelligence agent.
5. Formats clean data into CSV and JSON ready for cellular metabolism.
"""
import io
import csv
import json
import time
import uuid
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter
from bio_etl.models import OrganStage, BioLogEvent, HealthMetrics, PipelineConfig
from bio_etl.ai.ai_analyzer import DetachableHealthAI


class SmallIntestineAbsorber:
    """
    Intestinal villi absorption and metabolic data synthesis.
    """
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.ai_agent = DetachableHealthAI(enabled=config.enable_ai_agent)
        self.absorbed_records: List[Dict[str, Any]] = []

    def compute_modes(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculates dataset mode values for nutrient imputation."""
        modes = {}
        for key in ["gender", "diabetes", "smoker", "dateofvisit", "diagnosis", "yearofvisit"]:
            vals = [r[key] for r in records if r.get(key) not in [None, "", "none"]]
            if vals:
                modes[key] = Counter(vals).most_common(1)[0][0]
            else:
                modes[key] = "Unknown"

        # Age median/mode default
        ages = [r["age"] for r in records if isinstance(r.get("age"), (int, float))]
        modes["age"] = int(sorted(ages)[len(ages)//2]) if ages else 30

        # Height & Weight modes
        heights = [r["height(cm)"] for r in records if isinstance(r.get("height(cm)"), (int, float))]
        modes["height(cm)"] = int(Counter(heights).most_common(1)[0][0]) if heights else 170

        weights = [r["weight(kg)"] for r in records if isinstance(r.get("weight(kg)"), (int, float))]
        modes["weight(kg)"] = int(Counter(weights).most_common(1)[0][0]) if weights else 60

        # BP mode
        bps = [r["bloodpressure"] for r in records if r.get("bloodpressure")]
        modes["bloodpressure"] = Counter(bps).most_common(1)[0][0] if bps else "128/78"

        if "diagnosis" not in modes or modes["diagnosis"] == "Unknown":
            modes["diagnosis"] = "Hypertension"

        return modes

    def absorb_and_metabolize(
        self,
        approved_rows: List[Dict[str, Any]],
        quarantined_approved_rows: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[List[Dict[str, Any]], HealthMetrics, Optional[Dict[str, Any]], List[BioLogEvent]]:
        """
        Absorbs validated nutrients through villi, performs imputation on blanks,
        deduplicates, and computes metabolic analytics.
        """
        events = []
        event_id = str(uuid.uuid4())[:8]

        all_candidate_cleaned: List[Dict[str, Any]] = []

        # Extract cleaned data from row structures
        for row in approved_rows:
            cleaned = row.get("_meta", {}).get("_cleaned", row)
            all_candidate_cleaned.append(cleaned)

        if quarantined_approved_rows:
            all_candidate_cleaned.extend(quarantined_approved_rows)

        if not all_candidate_cleaned:
            return [], HealthMetrics(), None, events

        # Step 1: Compute nutrient replenishment modes
        modes = self.compute_modes(all_candidate_cleaned)

        # Step 2: Villi Absorption & Enrichment
        seen_pids = set()
        deduped_absorbed: List[Dict[str, Any]] = []

        events.append(BioLogEvent(
            id=f"villi-start-{event_id}",
            timestamp=time.time(),
            stage=OrganStage.SMALL_INTESTINE,
            action="Villi Absorption Commenced",
            reason=f"Small intestine microvilli engaging {len(all_candidate_cleaned)} candidate nutrient rows.",
            details={"candidates": len(all_candidate_cleaned)}
        ))

        for idx, rec in enumerate(all_candidate_cleaned):
            pid = rec.get("patientid", f"PID-{idx}")

            # Deduplication
            if pid in seen_pids:
                events.append(BioLogEvent(
                    id=f"villi-dedup-{idx}-{event_id}",
                    timestamp=time.time(),
                    stage=OrganStage.SMALL_INTESTINE,
                    row_idx=idx,
                    patient_id=pid,
                    action="Cellular Satiety (Duplicate Dropped)",
                    reason=f"Patient ID {pid} already absorbed into blood circulation; skipping redundant nutrient.",
                    details={"patient_id": pid}
                ))
                continue

            seen_pids.add(pid)

            # Impute any missing non-critical nutrients
            final_rec = dict(rec)
            for k, default_val in modes.items():
                if final_rec.get(k) is None or final_rec.get(k) == "":
                    final_rec[k] = default_val

            # Re-ensure height(m) and BMI are synchronized
            h_cm = final_rec.get("height(cm)", modes["height(cm)"])
            w_kg = final_rec.get("weight(kg)", modes["weight(kg)"])
            h_m = round(h_cm / 100.0, 2)
            final_rec["height(m)"] = h_m
            final_rec["bmi"] = round(w_kg / (h_m ** 2), 1)

            deduped_absorbed.append(final_rec)

            # Periodic microvilli uptake event
            if idx % 10 == 0 or idx == len(all_candidate_cleaned) - 1:
                events.append(BioLogEvent(
                    id=f"villi-absorb-{idx}-{event_id}",
                    timestamp=time.time(),
                    stage=OrganStage.SMALL_INTESTINE,
                    row_idx=idx,
                    patient_id=pid,
                    action="Nutrient Absorbed",
                    reason=f"Microvilli absorbed pure record for {final_rec.get('name', pid)} into bloodstream.",
                    details={"bmi": final_rec.get("bmi"), "bp": final_rec.get("bloodpressure")},
                    is_absorbed=True
                ))

        self.absorbed_records = deduped_absorbed

        # Step 3: Compute Health Analytics
        metrics = self._calculate_health_metrics(deduped_absorbed)

        # Step 4: Run Detachable AI Agent Analysis
        ai_insights = None
        if self.config.enable_ai_agent:
            ai_insights = self.ai_agent.analyze(deduped_absorbed)

        events.append(BioLogEvent(
            id=f"villi-metabolism-{event_id}",
            timestamp=time.time(),
            stage=OrganStage.BLOODSTREAM,
            action="Metabolism Active",
            reason=f"Absorbed {len(deduped_absorbed)} clean records into bloodstream for cellular metabolism. Final health analytics ready.",
            details=metrics.model_dump()
        ))

        return deduped_absorbed, metrics, ai_insights, events

    def _calculate_health_metrics(self, records: List[Dict[str, Any]]) -> HealthMetrics:
        """Computes population averages and health statistics."""
        if not records:
            return HealthMetrics()

        total = len(records)
        ages = [r["age"] for r in records if isinstance(r.get("age"), (int, float))]
        bmis = [r["bmi"] for r in records if isinstance(r.get("bmi"), (int, float))]

        avg_age = round(sum(ages) / len(ages), 1) if ages else 0.0
        avg_bmi = round(sum(bmis) / len(bmis), 1) if bmis else 0.0

        # BMI categories
        bmi_cats = {"Underweight (<18.5)": 0, "Normal (18.5-24.9)": 0, "Overweight (25-29.9)": 0, "Obese (>=30)": 0}
        for b in bmis:
            if b < 18.5:
                bmi_cats["Underweight (<18.5)"] += 1
            elif b < 25.0:
                bmi_cats["Normal (18.5-24.9)"] += 1
            elif b < 30.0:
                bmi_cats["Overweight (25-29.9)"] += 1
            else:
                bmi_cats["Obese (>=30)"] += 1

        # Chronic illness
        chronic_count = 0
        chronic_breakdown = {}
        for r in records:
            diag = str(r.get("diagnosis", "")).strip()
            has_diabetes = str(r.get("diabetes", "")).lower() == "yes"
            is_chronic = False
            if diag and diag.lower() not in ["none", "null", "nil"]:
                is_chronic = True
                chronic_breakdown[diag] = chronic_breakdown.get(diag, 0) + 1
            elif has_diabetes:
                is_chronic = True
                chronic_breakdown["Diabetes"] = chronic_breakdown.get("Diabetes", 0) + 1

            if is_chronic:
                chronic_count += 1

        chronic_pct = round((chronic_count / total) * 100, 1)

        # Gender & Smokers
        genders = Counter(r.get("gender", "Unknown") for r in records)
        smokers_count = sum(1 for r in records if str(r.get("smoker", "")).lower() in ["yes", "occasionally"])
        smoker_pct = round((smokers_count / total) * 100, 1)

        years = Counter(str(r.get("yearofvisit", "Unknown")) for r in records)

        return HealthMetrics(
            total_absorbed=total,
            average_age=avg_age,
            average_bmi=avg_bmi,
            bmi_categories=bmi_cats,
            chronic_illness_pct=chronic_pct,
            chronic_breakdown=chronic_breakdown,
            gender_distribution=dict(genders),
            smoker_percentage=smoker_pct,
            year_distribution=dict(years)
        )

    def export_csv(self, records: Optional[List[Dict[str, Any]]] = None) -> str:
        """Exports absorbed records to exact CSV schema."""
        recs = records if records is not None else self.absorbed_records
        if not recs:
            return ""

        fieldnames = [
            "patientid", "name", "gender", "age", "height(cm)", "weight(kg)",
            "bmi", "bloodpressure", "diabetes", "smoker", "dateofvisit",
            "diagnosis", "height(m)", "yearofvisit"
        ]

        out = io.StringIO()
        writer = csv.DictWriter(out, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for r in recs:
            writer.writerow(r)
        return out.getvalue()

    def export_json(self, records: Optional[List[Dict[str, Any]]] = None) -> str:
        """Exports absorbed records to JSON format."""
        recs = records if records is not None else self.absorbed_records
        return json.dumps(recs, indent=2)

