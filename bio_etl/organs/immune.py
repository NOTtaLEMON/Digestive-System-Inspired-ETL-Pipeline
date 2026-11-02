"""
Organ 4: The Immune System Layer.
Spans over all layers.
1. Scans for injection threats (SQLi, XSS, Cmd Injection, Formula Injection) just after the liver layer.
   Threats are immediately SQUASHED by White Blood Cell (WBC) Phagocytosis!
2. Analyzes other rejected/flagged entries sent by prior layers (e.g. missing high-priority fields).
   Holds questionable records in Quarantine.
3. Produces an Immune Report and coordinates user confirmation for quarantined records:
   - User can confirm squashing (ejected to Large Intestine)
   - User can confirm absorption with bio-imputation (repaired and passed to Small Intestine).
"""
import re
import time
import uuid
from typing import List, Dict, Any, Tuple, Optional
from bio_etl.models import (
    OrganStage, BioLogEvent, PipelineConfig, PriorityLevel,
    ThreatRecord, QuarantinedRecord, ImmuneReport
)


# Security injection patterns
THREAT_PATTERNS = [
    ("SQL Injection", re.compile(r"(\b(UNION(\s+ALL)?\s+SELECT|SELECT.+FROM|DROP\s+TABLE|INSERT\s+INTO|DELETE\s+FROM|--|\bOR\b\s+['\"]?1['\"]?\s*=\s*['\"]?1|xp_cmdshell)\b|;)", re.IGNORECASE)),
    ("Cross-Site Scripting (XSS)", re.compile(r"(<script\b|javascript:|onerror\s*=|onload\s*=|alert\(|<img\s+src=)", re.IGNORECASE)),
    ("OS Command Injection", re.compile(r"(\||;|&&|\$\(|\`)\s*(cat|ls|rm|whoami|curl|wget|reboot|sh|bash)", re.IGNORECASE)),
    ("CSV Formula Injection", re.compile(r"^[=+\-@]\s*(cmd|exec|calc|powershell|SUM\(|AVERAGE\()", re.IGNORECASE)),
]


class ImmuneSystem:
    """
    Simulates White Blood Cells (macrophages, neutrophils, lymphocytes)
    neutralizing malicious payloads and quarantining questionable records.
    """
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.squashed_threats: List[ThreatRecord] = []
        self.quarantined_records: Dict[str, QuarantinedRecord] = {}  # quarantine_id -> record

    def scan_for_threats(self, row: Dict[str, Any]) -> Optional[Tuple[str, str, str]]:
        """
        Scans all values in a record for injection attacks.
        Returns (threat_type, matched_field, payload) if threat found, else None.
        """
        raw_dict = row.get("_meta", {}).get("_raw", row)
        for field, val in raw_dict.items():
            if not val or field.startswith("_"):
                continue
            val_str = str(val).strip()
            for threat_name, pattern in THREAT_PATTERNS:
                if pattern.search(val_str):
                    return (threat_name, field, val_str)
        return None

    def process_chunk(
        self,
        liver_chunk: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[BioLogEvent]]:
        """
        Processes a chunk:
        1. Threat scan -> immediate squashing of malicious rows.
        2. Priority / Flag evaluation -> quarantine of problematic rows.
        3. Healthy rows passed through toward Small Intestine.
        Returns:
            - pass_through_rows: rows ready for absorption
            - rejected_or_held_rows: rows squashed or quarantined
            - events: biological immune events
        """
        events = []
        pass_through_rows: List[Dict[str, Any]] = []
        rejected_or_held_rows: List[Dict[str, Any]] = []
        event_id = str(uuid.uuid4())[:8]

        chunk_idx = liver_chunk[0]["_meta"]["_chunk_idx"] if liver_chunk else 0

        events.append(BioLogEvent(
            id=f"immune-patrol-{chunk_idx}-{event_id}",
            timestamp=time.time(),
            stage=OrganStage.IMMUNE,
            chunk_idx=chunk_idx,
            action="Immune Surveillance Patrol",
            reason=f"White Blood Cells (macrophages & lymphocytes) scanning Chunk #{chunk_idx + 1} for injection threats and priority violations.",
            details={"rows_to_scan": len(liver_chunk)}
        ))

        for row in liver_chunk:
            meta = row.get("_meta", {})
            row_idx = meta.get("_row_idx", 0)
            cleaned = meta.get("_cleaned", {})
            pid = cleaned.get("patientid") or f"Row-{row_idx}"

            # Step 1: Scan for injection threats
            threat_found = self.scan_for_threats(row)
            if threat_found:
                threat_type, field_name, payload = threat_found
                threat_rec = ThreatRecord(
                    threat_id=f"THREAT-{uuid.uuid4().hex[:6].upper()}",
                    row_idx=row_idx,
                    patient_id=pid,
                    threat_type=threat_type,
                    detected_payload=payload[:100],
                    field_name=field_name,
                    raw_data=meta.get("_raw", {})
                )
                self.squashed_threats.append(threat_rec)

                meta["_threat_squashed"] = True
                meta["_threat_details"] = threat_rec.model_dump()
                meta["_destination"] = "large_intestine"
                row["_meta"] = meta
                rejected_or_held_rows.append(row)

                events.append(BioLogEvent(
                    id=f"immune-threat-squash-{row_idx}-{event_id}",
                    timestamp=time.time(),
                    stage=OrganStage.IMMUNE,
                    chunk_idx=chunk_idx,
                    row_idx=row_idx,
                    patient_id=pid,
                    action="WBC Threat Neutralized",
                    reason=f"SECURITY ALERT! Squashed {threat_type} payload '{payload[:40]}' in field '{field_name}'. Cell destroyed by phagocytosis.",
                    details=threat_rec.model_dump(),
                    is_threat=True
                ))
                continue

            # Step 2: Check for quarantine flags from Liver/Stomach
            if meta.get("_flagged_for_squash", False):
                qid = f"Q-{uuid.uuid4().hex[:6].upper()}"
                q_rec = QuarantinedRecord(
                    quarantine_id=qid,
                    row_idx=row_idx,
                    patient_id=pid,
                    raw_data=meta.get("_raw", {}),
                    cleaned_data=cleaned,
                    flagged_reasons=meta.get("_squash_reasons", []),
                    violated_priorities=meta.get("_violated_priorities", []),
                    status="pending"
                )
                self.quarantined_records[qid] = q_rec

                meta["_quarantined"] = True
                meta["_quarantine_id"] = qid
                row["_meta"] = meta
                rejected_or_held_rows.append(row)

                events.append(BioLogEvent(
                    id=f"immune-quarantine-{row_idx}-{event_id}",
                    timestamp=time.time(),
                    stage=OrganStage.IMMUNE,
                    chunk_idx=chunk_idx,
                    row_idx=row_idx,
                    patient_id=pid,
                    action="Quarantined by Immune System",
                    reason=f"Held record {pid} in quarantine cell. Violated priority: {', '.join(q_rec.violated_priorities)}.",
                    details=q_rec.model_dump(),
                    is_quarantined=True
                ))
                continue

            # Step 3: Healthy row passed to absorption
            meta["_approved"] = True
            row["_meta"] = meta
            pass_through_rows.append(row)

        return pass_through_rows, rejected_or_held_rows, events

    def get_immune_report(self) -> ImmuneReport:
        """Returns the current state of threats and quarantined records."""
        q_list = list(self.quarantined_records.values())
        pending = sum(1 for q in q_list if q.status == "pending")
        resolved = sum(1 for q in q_list if q.status != "pending")
        return ImmuneReport(
            squashed_threats=self.squashed_threats,
            quarantined_records=q_list,
            pending_user_confirmations=pending,
            resolved_count=resolved
        )

    def resolve_quarantined_record(
        self,
        quarantine_id: str,
        action: str,  # "approve" or "squash"
        imputation_values: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        User confirmation action:
        - "approve": repairs record with imputation and releases to Small Intestine
        - "squash": permanently rejects and sends to Large Intestine
        """
        if quarantine_id not in self.quarantined_records:
            return None

        rec = self.quarantined_records[quarantine_id]
        if action == "approve":
            rec.status = "approved"
            if imputation_values:
                for k, v in imputation_values.items():
                    if rec.cleaned_data.get(k) is None or rec.cleaned_data.get(k) == "":
                        rec.cleaned_data[k] = v
            return rec.cleaned_data
        else:
            rec.status = "squashed"
            return None

