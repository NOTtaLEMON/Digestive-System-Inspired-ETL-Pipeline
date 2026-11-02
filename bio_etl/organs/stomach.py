"""
Organ 2: The Stomach (Acidification Layer).
Simulates gastric juice (Hydrochloric Acid & Pepsin enzymes) breaking down tough fibers,
stripping unreadable symbols, control characters, null bytes, and fixing bad formatting.
Weighs rows by column priority before passing acidic chyme to the Liver.
"""
import re
import time
import uuid
from typing import List, Dict, Any, Tuple
from bio_etl.models import OrganStage, BioLogEvent, PipelineConfig, PriorityLevel


class StomachAcidifier:
    """
    Acidifies chunked data rows. Strips non-printable characters, weird delimiters,
    and corrupted text artifacts. Tags rows that require priority review.
    """
    def __init__(self, config: PipelineConfig):
        self.config = config
        # Regex for tough bones/seeds: control characters, null bytes, zero-width chars
        self.bad_chars_pattern = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\ufeff\u200b\u200c\u200d]')

    def acidify_value(self, val: Any) -> Tuple[str, bool]:
        """
        Submerges a single string cell in gastric acid.
        Dissolves unreadable/corrupted characters.
        Returns cleaned string and whether any characters were digested.
        """
        if val is None:
            return "", False
        val_str = str(val)
        cleaned, num_subs = self.bad_chars_pattern.subn('', val_str)
        # Trim leading and trailing stray whitespace/tabs
        cleaned = cleaned.strip()
        was_acidified = (num_subs > 0) or (len(cleaned) != len(val_str.strip()))
        return cleaned, was_acidified

    def acidify_chunk(
        self,
        chunk: List[Dict[str, str]],
        chunk_idx: int,
        global_start_idx: int
    ) -> Tuple[List[Dict[str, Any]], List[BioLogEvent], int]:
        """
        Digests a chunk bolus in the stomach vat.
        Returns:
            - acidified_rows: list of parsed rows with acid tracking metadata
            - events: biological events for visualization
            - stripped_symbols_count: count of characters digested
        """
        events = []
        acidified_rows: List[Dict[str, Any]] = []
        total_stripped_count = 0
        rows_acid_treated = 0

        event_id = str(uuid.uuid4())[:8]
        events.append(BioLogEvent(
            id=f"stomach-churn-{chunk_idx}-{event_id}",
            timestamp=time.time(),
            stage=OrganStage.STOMACH,
            chunk_idx=chunk_idx,
            action="Gastric Churning Started",
            reason=f"Acid vat activated: Submerging Chunk #{chunk_idx + 1} ({len(chunk)} rows) into pH 1.5 gastric acid.",
            details={"chunk_size": len(chunk)}
        ))

        for offset, raw_row in enumerate(chunk):
            row_idx = global_start_idx + offset
            pid = raw_row.get("Patient ID", raw_row.get("patientid", f"Row-{row_idx}"))
            
            cleaned_row: Dict[str, Any] = {}
            row_had_acid_treatment = False
            symbols_in_row = 0

            for col, val in raw_row.items():
                clean_val, treated = self.acidify_value(val)
                cleaned_row[col] = clean_val
                if treated:
                    row_had_acid_treatment = True
                    symbols_in_row += (len(str(val)) - len(clean_val))

            if row_had_acid_treatment:
                rows_acid_treated += 1
                total_stripped_count += symbols_in_row
                events.append(BioLogEvent(
                    id=f"stomach-strip-{row_idx}-{event_id}",
                    timestamp=time.time(),
                    stage=OrganStage.STOMACH,
                    chunk_idx=chunk_idx,
                    row_idx=row_idx,
                    patient_id=pid,
                    action="Acid Dissolution",
                    reason=f"Dissolved {symbols_in_row} unreadable/control character(s) in {pid}'s record.",
                    details={"patient_id": pid, "dissolved_characters": symbols_in_row}
                ))

            # Store digestive metadata with the row
            row_metadata = {
                "_raw": raw_row,
                "_row_idx": row_idx,
                "_chunk_idx": chunk_idx,
                "_acid_treated": row_had_acid_treatment,
                "_symbols_stripped": symbols_in_row,
                "_flagged_for_squash": False,
                "_squash_reasons": []
            }
            cleaned_row["_meta"] = row_metadata
            acidified_rows.append(cleaned_row)

        events.append(BioLogEvent(
            id=f"stomach-chyme-{chunk_idx}-{event_id}",
            timestamp=time.time(),
            stage=OrganStage.STOMACH,
            chunk_idx=chunk_idx,
            action="Chyme Released",
            reason=f"Stomach finished churning Chunk #{chunk_idx + 1}. Acidified chyme passing through pyloric sphincter to Liver.",
            details={
                "chunk_idx": chunk_idx,
                "rows_treated": rows_acid_treated,
                "symbols_dissolved": total_stripped_count
            }
        ))

        return acidified_rows, events, total_stripped_count

