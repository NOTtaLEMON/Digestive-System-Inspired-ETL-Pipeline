"""
Organ 1: The Mouth (Mastication Layer).
Breaks incoming data into digestible windows (chunks / food boluses) based on file size
to avoid swallowing whole datasets at once and prevent pipeline choking or memory crashes.
Mapping: One bolus per KB of incoming file size.
"""
import io
import csv
import math
import time
import uuid
from typing import List, Dict, Any, Tuple
from bio_etl.models import OrganStage, BioLogEvent, PipelineConfig


class MouthMasticator:
    """
    Simulates mechanical breakdown of data into digestible food boluses.
    Weighs chunk size dynamically: exactly 1 bolus per KB of file size.
    """
    def __init__(self, config: PipelineConfig):
        self.config = config

    def calculate_bolus_distribution(self, total_rows: int, file_size_bytes: int) -> Tuple[int, int]:
        """
        Calculates target number of boluses and chunk row size.
        Rule: 1 bolus per KB of file size.
        """
        if self.config.chunk_size_mode != "auto":
            chunk_size = max(1, self.config.manual_chunk_size)
            target_boluses = max(1, math.ceil(total_rows / chunk_size))
            return target_boluses, chunk_size

        size_kb = max(1.0, file_size_bytes / 1024.0)
        target_boluses = max(1, int(round(size_kb)))
        # If total rows is fewer than boluses, clamp to total_rows
        target_boluses = min(target_boluses, max(1, total_rows))
        chunk_size = max(1, math.ceil(total_rows / target_boluses))
        return target_boluses, chunk_size

    def masticate(self, file_content_bytes: bytes) -> Tuple[List[str], List[List[Dict[str, str]]], List[BioLogEvent], int]:
        """
        Chews the input CSV bytes into header and chunked row boluses.
        Returns:
            - headers: list of field names
            - chunks: list of chunked row lists
            - events: list of mouth mastication events
            - chunk_size: chosen chunk size
        """
        events = []
        file_size_bytes = len(file_content_bytes)

        # Decode content with fallback
        try:
            text = file_content_bytes.decode('utf-8')
        except UnicodeDecodeError:
            text = file_content_bytes.decode('latin-1', errors='replace')

        stream = io.StringIO(text)
        reader = csv.reader(stream)
        
        try:
            headers = next(reader)
        except StopIteration:
            headers = []
            return headers, [], events, 20

        # Clean header whitespace
        headers = [h.strip() for h in headers]

        all_rows: List[Dict[str, str]] = []
        for raw_line_idx, row in enumerate(reader):
            row_dict = {}
            for col_idx, h in enumerate(headers):
                row_dict[h] = row[col_idx] if col_idx < len(row) else ""
            all_rows.append(row_dict)

        total_rows = len(all_rows)
        target_boluses, chunk_size = self.calculate_bolus_distribution(total_rows, file_size_bytes)

        event_id = str(uuid.uuid4())[:8]
        events.append(BioLogEvent(
            id=f"mouth-intro-{event_id}",
            timestamp=time.time(),
            stage=OrganStage.MOUTH,
            action="Mouth Ingestion",
            reason=f"Ingested CSV file of {file_size_bytes} bytes ({file_size_bytes/1024:.2f} KB). Target boluses: {target_boluses} (1 bolus per KB).",
            details={
                "file_size_bytes": file_size_bytes,
                "file_size_kb": round(file_size_bytes / 1024.0, 2),
                "target_boluses": target_boluses,
                "rows_per_bolus": chunk_size
            }
        ))

        chunks = []
        for i in range(0, total_rows, chunk_size):
            chunks.append(all_rows[i:i + chunk_size])

        actual_chunks_count = len(chunks)
        events.append(BioLogEvent(
            id=f"mouth-chew-{event_id}",
            timestamp=time.time(),
            stage=OrganStage.MOUTH,
            action="Mastication Complete",
            reason=f"Chewed {total_rows} records into {actual_chunks_count} distinct boluses ({chunk_size} rows per bolus).",
            details={
                "total_rows": total_rows,
                "total_chunks": actual_chunks_count,
                "rows_per_bolus": chunk_size
            }
        ))

        return headers, chunks, events, chunk_size
