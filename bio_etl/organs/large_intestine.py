"""
Organ 6: The Large Intestine (Excretion Layer).
Collects, compacts, and excretes rejected toxic payloads, squashed security threats,
and non-absorbed data debris as cellular waste.
"""
import io
import csv
import json
import time
import uuid
from typing import List, Dict, Any, Tuple, Optional
from bio_etl.models import OrganStage, BioLogEvent, ThreatRecord, QuarantinedRecord


class LargeIntestineExcretor:
    """
    Simulates colon peristalsis and excretion of toxic and rejected records.
    Maintains the Ejection Manifest and allows downloading discarded records.
    """
    def __init__(self):
        self.excreted_items: List[Dict[str, Any]] = []

    def collect_and_excrete(
        self,
        threats: List[ThreatRecord],
        squashed_quarantined: List[QuarantinedRecord]
    ) -> Tuple[List[Dict[str, Any]], List[BioLogEvent]]:
        """
        Gathers all discarded and squashed items for colon expulsion.
        """
        events = []
        event_id = str(uuid.uuid4())[:8]

        for t in threats:
            waste_entry = {
                "ejection_id": f"WASTE-THREAT-{t.threat_id}",
                "category": "Toxic Security Threat",
                "patient_id": t.patient_id,
                "row_idx": t.row_idx,
                "reason": f"Squashed {t.threat_type}: {t.detected_payload}",
                "timestamp": time.time(),
                "raw_content": json.dumps(t.raw_data)
            }
            self.excreted_items.append(waste_entry)

            events.append(BioLogEvent(
                id=f"colon-threat-excrete-{t.threat_id}-{event_id}",
                timestamp=time.time(),
                stage=OrganStage.LARGE_INTESTINE,
                row_idx=t.row_idx,
                patient_id=t.patient_id,
                action="Toxic Threat Excreted",
                reason=f"Colon expelled neutralized pathogen: {t.threat_type} from {t.patient_id}.",
                details=waste_entry,
                is_excreted=True
            ))

        for q in squashed_quarantined:
            waste_entry = {
                "ejection_id": f"WASTE-QUARANTINE-{q.quarantine_id}",
                "category": "High-Priority Violation (Rejected)",
                "patient_id": q.patient_id,
                "row_idx": q.row_idx,
                "reason": f"Rejected by user or priority squashing: {', '.join(q.flagged_reasons)}",
                "timestamp": time.time(),
                "raw_content": json.dumps(q.raw_data)
            }
            self.excreted_items.append(waste_entry)

            events.append(BioLogEvent(
                id=f"colon-quarantine-excrete-{q.quarantine_id}-{event_id}",
                timestamp=time.time(),
                stage=OrganStage.LARGE_INTESTINE,
                row_idx=q.row_idx,
                patient_id=q.patient_id,
                action="Defective Nutrient Excreted",
                reason=f"Colon eliminated non-viable record {q.patient_id} ({', '.join(q.violated_priorities)}).",
                details=waste_entry,
                is_excreted=True
            ))

        return self.excreted_items, events

    def export_waste_manifest_csv(self) -> str:
        """Exports the waste manifest to CSV."""
        if not self.excreted_items:
            return "ejection_id,category,patient_id,row_idx,reason,timestamp,raw_content\n"

        out = io.StringIO()
        fieldnames = ["ejection_id", "category", "patient_id", "row_idx", "reason", "timestamp", "raw_content"]
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()
        for item in self.excreted_items:
            writer.writerow(item)
        return out.getvalue()

