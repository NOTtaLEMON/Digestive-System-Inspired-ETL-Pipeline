"""
AI Population Health Intelligence Module.
Production-grade clinical analytics engine for patient cohort synthesis,
cardiometabolic risk stratification, and preventive health recommendations.
"""
from typing import Dict, List, Any, Optional


class DetachableHealthAI:
    """
    Production-grade AI Health Intelligence Agent for Clinical Data Insights.
    Operates on absorbed patient cohort data.
    """
    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def analyze(self, absorbed_rows: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Runs clinical demographic & risk analysis on absorbed records.
        Returns None if disabled.
        """
        if not self.enabled or not absorbed_rows:
            return None

        total = len(absorbed_rows)
        ages = [r["age"] for r in absorbed_rows if isinstance(r.get("age"), (int, float))]
        bmis = [r["bmi"] for r in absorbed_rows if isinstance(r.get("bmi"), (int, float))]

        avg_age = sum(ages) / len(ages) if ages else 0.0
        avg_bmi = sum(bmis) / len(bmis) if bmis else 0.0

        # High risk cohort detection (Hypertension + High BMI, Diabetes + Smoker, etc.)
        metabolic_syndrome_risk = 0
        cardiovascular_risk = 0
        respiratory_risk = 0

        diagnoses = {}
        smokers_with_chronic = 0

        for r in absorbed_rows:
            diag = str(r.get("diagnosis", "")).strip()
            if diag:
                diagnoses[diag] = diagnoses.get(diag, 0) + 1

            bmi_val = r.get("bmi", 0)
            is_smoker = str(r.get("smoker", "")).lower() in ["yes", "occasionally", "y"]
            has_diabetes = str(r.get("diabetes", "")).lower() in ["yes", "y"]
            has_htn = "hypertension" in diag.lower()
            has_asthma = "asthma" in diag.lower()

            # Cardio/Metabolic risk
            if (bmi_val >= 25.0 and has_htn) or (has_diabetes and has_htn):
                metabolic_syndrome_risk += 1
            if has_htn and (is_smoker or bmi_val >= 30.0):
                cardiovascular_risk += 1
            if has_asthma and is_smoker:
                respiratory_risk += 1
            if is_smoker and (has_htn or has_diabetes or has_asthma):
                smokers_with_chronic += 1

        top_diagnoses = sorted(diagnoses.items(), key=lambda x: x[1], reverse=True)

        summary = (
            f"Cohort analysis completed across {total} patients. "
            f"Mean cohort age is {avg_age:.1f} years with a mean BMI of {avg_bmi:.1f}. "
            f"{metabolic_syndrome_risk} individuals exhibit elevated cardiometabolic comorbidity, "
            f"and {respiratory_risk} asthmatic patients indicate concurrent tobacco exposure requiring intervention."
        )

        recommendations = [
            f"Prioritize targeted cardiovascular screening for {cardiovascular_risk} high-risk patients.",
            f"Deploy nutritional and lifestyle management protocols for the {avg_bmi:.1f} mean BMI population.",
            f"Enroll {smokers_with_chronic} chronic disease patients with documented tobacco use into cessation programs."
        ]

        return {
            "status": "active",
            "population_summary": summary,
            "metrics": {
                "total_patients": total,
                "mean_age": round(avg_age, 1),
                "mean_bmi": round(avg_bmi, 1),
                "cardiometabolic_risk_cohort": metabolic_syndrome_risk,
                "cardiovascular_risk_cohort": cardiovascular_risk,
                "respiratory_risk_cohort": respiratory_risk,
                "smokers_with_comorbidity": smokers_with_chronic
            },
            "top_diagnoses": [{"diagnosis": d, "count": c, "pct": round(c / total * 100, 1)} for d, c in top_diagnoses],
            "clinical_recommendations": recommendations,
            "pipeline_biological_note": "Nutrient absorption completed across the intestinal villi into systemic circulation."
        }
