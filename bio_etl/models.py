"""
Data models and configuration schemas for the Bio-mimetic ETL Pipeline.
"""
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field


class OrganStage(str, Enum):
    MOUTH = "mouth"
    STOMACH = "stomach"
    LIVER = "liver"
    IMMUNE = "immune"
    SMALL_INTESTINE = "small_intestine"
    LARGE_INTESTINE = "large_intestine"
    BLOODSTREAM = "bloodstream"


class BPFormat(str, Enum):
    SLASH = "slash"      # 120/80
    OVER = "over"        # 120 over 80
    DASH = "dash"        # 130-85
    BY = "by"            # 120 by 80


class DateFormat(str, Enum):
    ISO = "YYYY-MM-DD"        # 2023-01-15
    DMY_DASH = "DD-MM-YYYY"   # 15-01-2023
    MDY_SLASH = "MM/DD/YYYY"  # 01/15/2023
    YMD_DOT = "YYYY.MM.DD"    # 2023.01.15


class PriorityLevel(str, Enum):
    HIGH = "high"       # Empty/invalid causes quarantine & recommendation to squash
    MEDIUM = "medium"   # Missing can be imputed or warned
    LOW = "low"         # Optional field, easily imputed


class PipelineConfig(BaseModel):
    chunk_size_mode: str = "auto"  # "auto" or integer string
    manual_chunk_size: int = 20
    standard_bp_format: BPFormat = BPFormat.SLASH
    standard_date_format: DateFormat = DateFormat.ISO
    column_priorities: Dict[str, PriorityLevel] = Field(default_factory=lambda: {
        "Patient ID": PriorityLevel.HIGH,
        "Name": PriorityLevel.HIGH,
        "Age": PriorityLevel.MEDIUM,
        "Gender": PriorityLevel.LOW,
        "Height_cm": PriorityLevel.MEDIUM,
        "Weight_kg": PriorityLevel.MEDIUM,
        "Blood Pressure": PriorityLevel.MEDIUM,
        "Diabetes": PriorityLevel.LOW,
        "Smoker": PriorityLevel.LOW,
        "Date of Visit": PriorityLevel.MEDIUM,
        "Diagnosis": PriorityLevel.LOW,
    })
    enable_ai_agent: bool = True
    auto_approve_quarantine: bool = False  # If False, pauses for user confirmation


class BioLogEvent(BaseModel):
    id: str
    timestamp: float
    stage: OrganStage
    chunk_idx: Optional[int] = None
    row_idx: Optional[int] = None
    patient_id: Optional[str] = None
    action: str
    reason: str
    details: Optional[Dict[str, Any]] = None
    is_threat: bool = False
    is_quarantined: bool = False
    is_absorbed: bool = False
    is_excreted: bool = False


class QuarantinedRecord(BaseModel):
    quarantine_id: str
    row_idx: int
    patient_id: Optional[str] = "Unknown"
    raw_data: Dict[str, Any]
    cleaned_data: Dict[str, Any]
    flagged_reasons: List[str]
    violated_priorities: List[str]
    status: str = "pending"  # "pending", "approved", "squashed"


class ThreatRecord(BaseModel):
    threat_id: str
    row_idx: int
    patient_id: Optional[str] = "Unknown"
    threat_type: str
    detected_payload: str
    field_name: str
    action_taken: str = "SQUASHED by White Blood Cell Phagocytosis"
    raw_data: Dict[str, Any]


class ImmuneReport(BaseModel):
    squashed_threats: List[ThreatRecord] = Field(default_factory=list)
    quarantined_records: List[QuarantinedRecord] = Field(default_factory=list)
    pending_user_confirmations: int = 0
    resolved_count: int = 0


class HealthMetrics(BaseModel):
    total_absorbed: int = 0
    average_age: float = 0.0
    average_bmi: float = 0.0
    bmi_categories: Dict[str, int] = Field(default_factory=dict)
    chronic_illness_pct: float = 0.0
    chronic_breakdown: Dict[str, int] = Field(default_factory=dict)
    gender_distribution: Dict[str, int] = Field(default_factory=dict)
    smoker_percentage: float = 0.0
    year_distribution: Dict[str, int] = Field(default_factory=dict)


class FinalPipelineReport(BaseModel):
    file_name: str
    file_size_bytes: int
    chunk_size_chosen: int
    total_chunks: int
    total_raw_rows: int
    acid_stripped_count: int
    liver_normalized_count: int
    threats_squashed: int
    quarantined_count: int
    quarantined_approved: int
    quarantined_excreted: int
    absorbed_count: int
    total_excreted: int
    immune_report: ImmuneReport
    health_metrics: HealthMetrics
    ai_insights: Optional[Dict[str, Any]] = None

