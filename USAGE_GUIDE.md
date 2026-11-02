# Bio-mimetic Digestive System ETL Pipeline
## *Enterprise Data Metabolism & Immune Surveillance Engine*

Welcome to the **Bio-mimetic Digestive System ETL Pipeline**. This system reimagines traditional data extraction, transformation, and loading (ETL) through the lens of human gastrointestinal physiology.

Rather than "swallowing" whole CSV files at once (which causes system choking and memory crashes), incoming data is masticated into bite-sized boluses, acidified to dissolve unreadable symbols, detoxified by liver bile, scanned for injection threats by white blood cells, absorbed across intestinal villi, and metabolized into pure, analysis-ready datasets.

---

## Biological Architecture & Pipeline Stages

```
   [ CSV Input File ]
           │
           ▼
     ┌───────────┐
     │ 1. MOUTH  │  Mastication: Weighed dynamically at 1 bolus per KB of file size.
     └─────┬─────┘  Chews large files into bite-sized food boluses.
           │
           ▼
    ┌─────────────┐
    │ 2. STOMACH  │  Gastric Acid (HCl & Pepsin): Dissolves null bytes,
    └──────┬──────┘  non-printable control chars, and corrupt symbols.
           │
           ▼
     ┌───────────┐
     │ 3. LIVER  │  Bile Detoxification: Standardizes number words ("forty"->40),
     └─────┬─────┘  blood pressures ("90 over 70"->90/70), dates & capitalization.
           │        Tags missing high-priority fields for the Immune System.
           ▼
    ┌─────────────┐
    │  4. IMMUNE  │  White Blood Cells (Macrophages & Lymphocytes):
    │   SYSTEM    │  - Threat Scanner: Immediately SQUASHES SQLi, XSS, Cmd Injection!
    └──────┬──────┘  - Quarantine Vault: Holds priority violations for user confirmation.
           │
           ├───────────────────────────────┐
           ▼                               ▼
  ┌──────────────────┐           ┌───────────────────┐
  │5. SMALL INTESTINE│           │6. LARGE INTESTINE │
  │  (Microvilli)    │           │     (Colon)       │
  └────────┬─────────┘           └─────────┬─────────┘
           │ Nutrient Absorption           │ Ejection Manifest
           ▼                               ▼
    [ METABOLISM ]                 [ WASTE EGESTION ]
 Clean CSV / JSON Export          Toxic Threats & Debris
 + Cohort Health Analytics
 + AI Clinical Insights
```

### 1. The Mouth (Mastication Layer)
- **Biological Role:** Chewing and bolus formation.
- **Data Role:** Weighed dynamically based on the incoming CSV file size at **1 bolus per KB of file size**.
  - `messy_health_data.csv` (~6.3 KB) $\rightarrow$ 6 boluses.
  - `expanded_messy_health_data.csv` (~124 KB) $\rightarrow$ 124 boluses.
  - Rows per bolus is dynamically calculated as $\lceil \text{total\_rows} / \text{boluses} \rceil$.
- Users can also configure a custom manual bolus window size if desired.

### 2. The Stomach (Acidification Layer)
- **Biological Role:** Hydrochloric acid (pH 1.5) and pepsin breakdown of tough outer structures.
- **Data Role:** Raw rows are submerged in virtual gastric acid. Unreadable symbols, null bytes (`\x00`), zero-width characters (`\u200b`), BOM markers (`\ufeff`), form feeds, and non-printable control characters are dissolved away. Rows are not deleted here; their priority is weighed before passing acidic chyme through the pyloric sphincter.

### 3. The Liver (Detoxification & Standardization Layer)
- **Biological Role:** Hepatic metabolism and bile juice secretion.
- **Data Role:** Detoxifies mismatches in formatting:
  - **Number words:** Converts `"forty"` to `40`, `"eighty"` to `80`, `"one seventy"` to `170`, `"170cm"` to `170`.
  - **Name Capitalization:** Normalizes names to Title Case (`"marydoe"` -> `Marydoe`, `"ALICE JOHNSON"` -> `Alice Johnson`).
  - **Blood Pressure Harmonization:** Parses variations like `110 over 70`, `130-85`, `90 by 70`, `140/90` and reformats them into the user's chosen standard (`120/80`, `120 over 80`, `120-85`, or `120 by 80`).
  - **Date Normalization:** Parses mixed date strings (`2023.04.01`, `15-02-2023`, `March 5 2023`) into the user's selected standard date format (`YYYY-MM-DD`, `DD-MM-YYYY`, `MM/DD/YYYY`).
  - **Metric Calculations:** Computes height in meters (`height_m = height_cm / 100`) and BMI (`weight_kg / (height_m ** 2)`).
  - **Priority Weighing:** Compares columns against user-defined priority levels (High, Medium, Low). If a **High Priority** column (e.g. `Name`) is missing or invalid, the liver **does not delete it**; it flags the row for squashing and sends it to the Immune System for final judgment.

### 4. The Immune System (Threat Surveillance & Quarantine Tribunal)
- **Biological Role:** White Blood Cells (Macrophages, Neutrophils, Antibodies) patrolling the bloodstream.
- **Data Role:**
  1. **Threat Scanner:** Immediately following the liver, all fields are inspected for injection attacks:
     - SQL Injections (`' OR '1'='1`, `UNION SELECT`, `DROP TABLE`, `xp_cmdshell`)
     - Cross-Site Scripting (`<script>`, `javascript:`, `onerror=`, `onload=`)
     - OS Command Injections (`| cat /etc/passwd`, `&& whoami`, `$(reboot)`)
     - CSV Formula Injections (`=cmd|`, `@SUM`, `+calc`)
     - **Action:** Toxic records are **instantly squashed by White Blood Cell Phagocytosis** and routed to the colon!
  2. **Quarantine Holding Facility:** Questionable records flagged by prior layers (missing high-priority attributes) are placed in detention.
  3. **Quarantine Tribunal (User Confirmation):** The pipeline pauses and presents an interactive report. For each quarantined record, the user can choose:
     - **Approve with Imputation:** Repairs missing fields with population mode/median nutrients and releases the record into the Small Intestine.
     - **Excrete Record:** Permanently eliminates the record as biological waste into the colon.

### 5. The Small Intestine (Villi Absorption & Metabolism)
- **Biological Role:** Microvilli absorbing clean amino acids, glucose, and fatty acids into mesenteric capillaries.
- **Data Role:**
  - Absorbs validated rows and enriches remaining optional gaps with mode imputations.
  - Deduplicates records to ensure pure nutrient uptake.
  - Computes cohort health statistics:
    - Average patient age
    - Average BMI & distribution (Underweight, Normal, Overweight, Obese)
    - Chronic illness percentage (Hypertension, Diabetes Type II, Asthma)
    - Smoker percentage and gender distributions.
  - **AI Population Health Insights (`bio_etl/ai/ai_analyzer.py`):** Production-grade clinical intelligence module that can be toggled on/off via the dedicated toolbar checkbox button. Provides clinical risk stratification, cardiometabolic risk cohort alerts, and lifestyle recommendations.
  - **Export Formats:** Generates clean, 100% complete data in **CSV** and **JSON**.

### 6. The Large Intestine (Colon & Excretion Manifest)
- **Biological Role:** Compacting indigestible waste and excretion.
- **Data Role:** Collects all neutralized security threats and squashed quarantine records into a downloadable **Waste Manifest (CSV)** with timestamps and threat descriptions.

---

## Quickstart Guide

### 1. Launch the Server
```bash
./.venv/bin/python main.py
```

Open your browser to:
👉 **[http://localhost:8000](http://localhost:8000)**

---

## Datasets Available

1. **`expanded_messy_health_data.csv` (1,600 Records, ~124 KB):**
   - Contains real-world control characters and null bytes (`\x00`) to exercise the **Stomach Acid Dissolution**.
   - Contains SQL injections, XSS payloads, OS command injections, and CSV formula injections to exercise the **Immune System Threat Scanner**.
   - Contains missing high-priority fields to exercise the **Quarantine Tribunal**.
   - Automatically split into **124 mastication boluses** (1 bolus per KB).
2. **`messy_health_data.csv` (105 Records, ~6.3 KB):**
   - The original dataset, masticated into **6 boluses** (1 bolus per KB).
3. **Custom Upload:**
   - Upload any CSV from your machine via the Configuration dialog.

---

## Programmatic Python API

```python
from bio_etl.pipeline import BioDigestivePipeline
from bio_etl.models import PipelineConfig, PriorityLevel, BPFormat, DateFormat

config = PipelineConfig(
    standard_bp_format=BPFormat.SLASH,
    standard_date_format=DateFormat.ISO,
    column_priorities={
        "Patient ID": PriorityLevel.HIGH,
        "Name": PriorityLevel.HIGH,
        "Age": PriorityLevel.MEDIUM,
        "Blood Pressure": PriorityLevel.MEDIUM
    },
    enable_ai_agent=True,
    auto_approve_quarantine=True
)

with open("expanded_messy_health_data.csv", "rb") as f:
    csv_bytes = f.read()

pipeline = BioDigestivePipeline(config=config)
for event in pipeline.ingest_and_digest(csv_bytes, filename="expanded_messy_health_data.csv"):
    print(f"[{event.stage.upper()}] {event.action}: {event.reason}")

clean_csv = pipeline.small_intestine.export_csv()
metrics = pipeline.final_report.health_metrics
print(f"Absorbed Patients: {metrics.total_absorbed}")
print(f"Average BMI: {metrics.average_bmi}")
```
