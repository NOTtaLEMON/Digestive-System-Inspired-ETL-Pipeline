"""
Bio-mimetic Digestive System ETL Pipeline Orchestrator.
Coordinates the flow of data boluses through:
1. Mouth (Mastication & Dynamic Chunk Sizing)
2. Stomach (Acidification & Character Dissolution)
3. Liver (Detoxification, Standardization & Priority Weighing)
4. Immune System (Threat Neutralization & Quarantine Surveillance)
5. Small Intestine (Villi Absorption & Metabolism Analytics)
6. Large Intestine (Excretion & Waste Manifestation)
"""
import time
from typing import List, Dict, Any, Tuple, Optional, Generator
from bio_etl.models import (
    PipelineConfig, BioLogEvent, FinalPipelineReport,
    HealthMetrics, ImmuneReport, OrganStage
)
from bio_etl.organs.mouth import MouthMasticator
from bio_etl.organs.stomach import StomachAcidifier
from bio_etl.organs.liver import LiverDetoxifier
from bio_etl.organs.immune import ImmuneSystem
from bio_etl.organs.small_intestine import SmallIntestineAbsorber
from bio_etl.organs.large_intestine import LargeIntestineExcretor


class BioDigestivePipeline:
    """
    Main Bio-mimetic ETL Pipeline Engine.
    """
    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self.mouth = MouthMasticator(self.config)
        self.stomach = StomachAcidifier(self.config)
        self.liver = LiverDetoxifier(self.config)
        self.immune = ImmuneSystem(self.config)
        self.small_intestine = SmallIntestineAbsorber(self.config)
        self.large_intestine = LargeIntestineExcretor()

        # State tracking
        self.events: List[BioLogEvent] = []
        self.approved_rows: List[Dict[str, Any]] = []
        self.held_or_rejected_rows: List[Dict[str, Any]] = []
        self.absorbed_rows: List[Dict[str, Any]] = []
        self.file_name: str = "health_data.csv"
        self.file_size_bytes: int = 0
        self.chunk_size_chosen: int = 20
        self.total_chunks: int = 0
        self.total_raw_rows: int = 0
        self.acid_stripped_count: int = 0
        self.liver_normalized_count: int = 0
        self.is_waiting_quarantine_confirmation: bool = False
        self.is_completed: bool = False
        self.final_report: Optional[FinalPipelineReport] = None

    def ingest_and_digest(
        self,
        file_bytes: bytes,
        filename: str = "health_data.csv"
    ) -> Generator[BioLogEvent, None, None]:
        """
        Runs the pipeline up through the Immune System layer.
        Yields events in real-time as chunks move down the digestive tract.
        """
        self.file_name = filename
        self.file_size_bytes = len(file_bytes)

        # 1. Mouth (Mastication)
        headers, chunks, mouth_events, chunk_size = self.mouth.masticate(file_bytes)
        self.chunk_size_chosen = chunk_size
        self.total_chunks = len(chunks)
        self.total_raw_rows = sum(len(c) for c in chunks)

        for ev in mouth_events:
            self.events.append(ev)
            yield ev

        global_row_cursor = 0

        # Process each food bolus (chunk)
        for chunk_idx, chunk in enumerate(chunks):
            # Mouth bolus release
            mouth_bolus_ev = BioLogEvent(
                id=f"mouth-bolus-{chunk_idx}-{str(time.time())[-4:]}",
                timestamp=time.time(),
                stage=OrganStage.MOUTH,
                chunk_idx=chunk_idx,
                action=f"Bolus #{chunk_idx + 1} Masticated",
                reason=f"Mouth masticated Bolus #{chunk_idx + 1} of {self.total_chunks} ({len(chunk)} records). Passing down esophagus.",
                details={"chunk_idx": chunk_idx, "total_chunks": self.total_chunks, "rows": len(chunk)}
            )
            self.events.append(mouth_bolus_ev)
            yield mouth_bolus_ev

            # 2. Stomach (Acidification)
            acid_rows, stomach_events, stripped = self.stomach.acidify_chunk(
                chunk=chunk,
                chunk_idx=chunk_idx,
                global_start_idx=global_row_cursor
            )
            self.acid_stripped_count += stripped
            for ev in stomach_events:
                self.events.append(ev)
                yield ev

            # 3. Liver (Detoxification & Standardization)
            liver_rows, liver_events, norm_count = self.liver.detoxify_chunk(acid_rows)
            self.liver_normalized_count += norm_count
            for ev in liver_events:
                self.events.append(ev)
                yield ev

            # 4. Immune System (Surveillance & Threat Neutralization)
            pass_through, rejected_or_held, immune_events = self.immune.process_chunk(liver_rows)
            for ev in immune_events:
                self.events.append(ev)
                yield ev

            # Bolus queues at small intestine entrance
            bolus_queue_ev = BioLogEvent(
                id=f"bolus-queue-{chunk_idx}-{str(time.time())[-4:]}",
                timestamp=time.time(),
                stage=OrganStage.IMMUNE,
                chunk_idx=chunk_idx,
                action=f"Bolus #{chunk_idx + 1} Cleared",
                reason=f"Bolus #{chunk_idx + 1} of {self.total_chunks} cleared liver & immune scan. Queued at small intestine for collective absorption.",
                details={"chunk_idx": chunk_idx, "total_chunks": self.total_chunks}
            )
            self.events.append(bolus_queue_ev)
            yield bolus_queue_ev

            self.approved_rows.extend(pass_through)
            self.held_or_rejected_rows.extend(rejected_or_held)
            global_row_cursor += len(chunk)

        # Check quarantine requirements
        immune_rep = self.immune.get_immune_report()
        if immune_rep.pending_user_confirmations > 0 and not self.config.auto_approve_quarantine:
            self.is_waiting_quarantine_confirmation = True
        else:
            # Auto-absorb if no confirmation needed
            yield from self.complete_absorption([])

    def complete_absorption(
        self,
        quarantine_resolutions: List[Dict[str, Any]]
    ) -> Generator[BioLogEvent, None, None]:
        """
        Step 5 & 6: Resolves quarantined records, runs Small Intestine absorption,
        and excretes waste through Large Intestine.
        """
        quarantined_approved = []
        squashed_quarantined = []

        # Process user decisions on quarantined records
        for res in quarantine_resolutions:
            qid = res.get("quarantine_id")
            action = res.get("action", "squash")  # "approve" or "squash"
            imputation = res.get("imputation_values")
            resolved_data = self.immune.resolve_quarantined_record(qid, action, imputation)
            if resolved_data:
                quarantined_approved.append(resolved_data)
            else:
                if qid in self.immune.quarantined_records:
                    squashed_quarantined.append(self.immune.quarantined_records[qid])

        # Auto-handle any remaining pending records if auto-approval was requested
        if self.config.auto_approve_quarantine:
            for qid, qrec in self.immune.quarantined_records.items():
                if qrec.status == "pending":
                    res_data = self.immune.resolve_quarantined_record(qid, "approve")
                    if res_data:
                        quarantined_approved.append(res_data)

        # 5. Small Intestine (Absorption & Villi Metabolism)
        # Emit collective absorption event for all boluses
        collective_ev = BioLogEvent(
            id=f"villi-collective-{str(time.time())[-4:]}",
            timestamp=time.time(),
            stage=OrganStage.SMALL_INTESTINE,
            action="Collective Villi Absorption",
            reason=f"All {self.total_chunks} boluses converged in small intestine. Microvilli absorbing all nutrients simultaneously into bloodstream.",
            details={"total_chunks": self.total_chunks, "is_collective": True}
        )
        self.events.append(collective_ev)
        yield collective_ev

        absorbed, metrics, ai_insights, si_events = self.small_intestine.absorb_and_metabolize(
            approved_rows=self.approved_rows,
            quarantined_approved_rows=quarantined_approved
        )
        self.absorbed_rows = absorbed
        for ev in si_events:
            self.events.append(ev)
            yield ev

        # 6. Large Intestine (Excretion of Squashed Threats & Rejected Records)
        waste_manifest, li_events = self.large_intestine.collect_and_excrete(
            threats=self.immune.squashed_threats,
            squashed_quarantined=squashed_quarantined
        )
        for ev in li_events:
            self.events.append(ev)
            yield ev

        self.is_waiting_quarantine_confirmation = False
        self.is_completed = True

        immune_report = self.immune.get_immune_report()

        self.final_report = FinalPipelineReport(
            file_name=self.file_name,
            file_size_bytes=self.file_size_bytes,
            chunk_size_chosen=self.chunk_size_chosen,
            total_chunks=self.total_chunks,
            total_raw_rows=self.total_raw_rows,
            acid_stripped_count=self.acid_stripped_count,
            liver_normalized_count=self.liver_normalized_count,
            threats_squashed=len(self.immune.squashed_threats),
            quarantined_count=len(self.immune.quarantined_records),
            quarantined_approved=len(quarantined_approved),
            quarantined_excreted=len(squashed_quarantined),
            absorbed_count=len(self.absorbed_rows),
            total_excreted=len(waste_manifest),
            immune_report=immune_report,
            health_metrics=metrics,
            ai_insights=ai_insights
        )

