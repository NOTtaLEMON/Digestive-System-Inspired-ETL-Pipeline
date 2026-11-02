"""
FastAPI Server for Bio-mimetic Digestive System ETL Pipeline.
Provides REST and Server-Sent Event (SSE) endpoints for real-time educational visual streaming.
"""
import os
import json
import uuid
import asyncio
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from bio_etl.models import PipelineConfig, BPFormat, DateFormat, PriorityLevel
from bio_etl.pipeline import BioDigestivePipeline

app = FastAPI(title="Bio-mimetic Digestive System ETL Pipeline", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active pipeline sessions in memory
SESSIONS: Dict[str, Dict[str, Any]] = {}

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


@app.get("/api/default-config")
async def get_default_config():
    """Returns available configuration formats and default priorities."""
    return {
        "bp_formats": [
            {"value": BPFormat.SLASH.value, "label": "Systolic/Diastolic (e.g. 120/80)"},
            {"value": BPFormat.OVER.value, "label": "Systolic over Diastolic (e.g. 120 over 80)"},
            {"value": BPFormat.DASH.value, "label": "Systolic-Diastolic (e.g. 120-80)"},
            {"value": BPFormat.BY.value, "label": "Systolic by Diastolic (e.g. 120 by 80)"},
        ],
        "date_formats": [
            {"value": DateFormat.ISO.value, "label": "ISO Format (YYYY-MM-DD)"},
            {"value": DateFormat.DMY_DASH.value, "label": "European (DD-MM-YYYY)"},
            {"value": DateFormat.MDY_SLASH.value, "label": "US Format (MM/DD/YYYY)"},
            {"value": DateFormat.YMD_DOT.value, "label": "Dot Separated (YYYY.MM.DD)"},
        ],
        "priority_levels": [
            {"value": PriorityLevel.HIGH.value, "label": "High Priority (Empty/corrupt requires Quarantine & Squash recommendation)"},
            {"value": PriorityLevel.MEDIUM.value, "label": "Medium Priority (Warning and Mode/Median Imputation)"},
            {"value": PriorityLevel.LOW.value, "label": "Low Priority (Safe to auto-impute / optional)"},
        ],
        "default_priorities": {
            "Patient ID": PriorityLevel.HIGH.value,
            "Name": PriorityLevel.HIGH.value,
            "Age": PriorityLevel.MEDIUM.value,
            "Gender": PriorityLevel.LOW.value,
            "Height_cm": PriorityLevel.MEDIUM.value,
            "Weight_kg": PriorityLevel.MEDIUM.value,
            "Blood Pressure": PriorityLevel.MEDIUM.value,
            "Diabetes": PriorityLevel.LOW.value,
            "Smoker": PriorityLevel.LOW.value,
            "Date of Visit": PriorityLevel.MEDIUM.value,
            "Diagnosis": PriorityLevel.LOW.value,
        },
        "chunk_size_modes": [
            {"value": "auto", "label": "Adaptive Mastication (Automatic based on file size)"},
            {"value": "manual", "label": "Manual Bolus Window Size"}
        ]
    }


@app.get("/api/available-files")
async def list_available_workspace_files():
    """Lists CSV files in workspace available for digestion."""
    files = []
    has_short = os.path.exists(os.path.join(WORKSPACE_DIR, "short_messy_health_data.csv"))
    for f in os.listdir(WORKSPACE_DIR):
        if f.endswith(".csv"):
            fpath = os.path.join(WORKSPACE_DIR, f)
            if has_short:
                is_default = (f == "short_messy_health_data.csv")
            else:
                is_default = (f == "expanded_messy_health_data.csv")
            files.append({
                "filename": f,
                "filepath": fpath,
                "size_bytes": os.path.getsize(fpath),
                "is_default": is_default
            })
    return {"files": sorted(files, key=lambda x: (not x["is_default"], x["filename"]))}


class PipelineStartPayload(BaseModel):
    file_source: str  # "server_file" or "upload"
    server_filename: Optional[str] = "messy_health_data.csv"
    bp_format: BPFormat = BPFormat.SLASH
    date_format: DateFormat = DateFormat.ISO
    chunk_size_mode: str = "auto"
    manual_chunk_size: int = 20
    column_priorities: Dict[str, PriorityLevel]
    enable_ai_agent: bool = True
    auto_approve_quarantine: bool = False


@app.post("/api/pipeline/start")
async def start_pipeline(payload: PipelineStartPayload):
    """Initializes and kicks off a bio-mimetic digestion session."""
    session_id = str(uuid.uuid4())[:8]

    # Resolve input bytes
    if payload.file_source == "server_file":
        if not payload.server_filename:
            raise HTTPException(status_code=400, detail="Missing server filename")
        filepath = os.path.join(WORKSPACE_DIR, os.path.basename(payload.server_filename))
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail=f"File {payload.server_filename} not found")
        with open(filepath, "rb") as f:
            file_bytes = f.read()
        filename = payload.server_filename
    else:
        raise HTTPException(status_code=400, detail="For direct file upload use /api/pipeline/upload")

    config = PipelineConfig(
        chunk_size_mode=payload.chunk_size_mode,
        manual_chunk_size=payload.manual_chunk_size,
        standard_bp_format=payload.bp_format,
        standard_date_format=payload.date_format,
        column_priorities=payload.column_priorities,
        enable_ai_agent=payload.enable_ai_agent,
        auto_approve_quarantine=payload.auto_approve_quarantine
    )

    pipeline = BioDigestivePipeline(config=config)

    # Run ingestion & digestion step
    event_queue = list(pipeline.ingest_and_digest(file_bytes, filename=filename))

    SESSIONS[session_id] = {
        "id": session_id,
        "pipeline": pipeline,
        "config": config,
        "events": event_queue,
        "is_waiting_quarantine": pipeline.is_waiting_quarantine_confirmation,
        "is_completed": pipeline.is_completed,
        "filename": filename
    }

    return {
        "session_id": session_id,
        "total_events": len(event_queue),
        "is_waiting_quarantine": pipeline.is_waiting_quarantine_confirmation,
        "is_completed": pipeline.is_completed,
        "chunk_size": pipeline.chunk_size_chosen,
        "total_chunks": pipeline.total_chunks,
        "total_raw_rows": pipeline.total_raw_rows
    }


@app.post("/api/pipeline/upload")
async def upload_and_start(
    file: UploadFile = File(...),
    config_json: str = Form(...)
):
    """Handles direct file upload from user's machine and starts digestion."""
    session_id = str(uuid.uuid4())[:8]
    content = await file.read()

    cfg_dict = json.loads(config_json)
    config = PipelineConfig(**cfg_dict)

    pipeline = BioDigestivePipeline(config=config)
    event_queue = list(pipeline.ingest_and_digest(content, filename=file.filename or "uploaded.csv"))

    SESSIONS[session_id] = {
        "id": session_id,
        "pipeline": pipeline,
        "config": config,
        "events": event_queue,
        "is_waiting_quarantine": pipeline.is_waiting_quarantine_confirmation,
        "is_completed": pipeline.is_completed,
        "filename": file.filename or "uploaded.csv"
    }

    return {
        "session_id": session_id,
        "total_events": len(event_queue),
        "is_waiting_quarantine": pipeline.is_waiting_quarantine_confirmation,
        "is_completed": pipeline.is_completed,
        "chunk_size": pipeline.chunk_size_chosen,
        "total_chunks": pipeline.total_chunks,
        "total_raw_rows": pipeline.total_raw_rows
    }


@app.get("/api/pipeline/{session_id}/events")
async def get_events(session_id: str, after_idx: int = 0):
    """Retrieves generated events for animated playback."""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    sess = SESSIONS[session_id]
    all_events = sess["events"]
    slice_events = all_events[after_idx:]
    return {
        "events": [e.model_dump() for e in slice_events],
        "total_count": len(all_events),
        "is_waiting_quarantine": sess["pipeline"].is_waiting_quarantine_confirmation,
        "is_completed": sess["pipeline"].is_completed
    }


@app.get("/api/pipeline/{session_id}/stream")
async def stream_events(session_id: str):
    """Streams digestion events as Server-Sent Events (SSE)."""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    async def event_generator():
        sess = SESSIONS[session_id]
        events = sess["events"]
        for ev in events:
            yield f"data: {json.dumps(ev.model_dump())}\n\n"
            await asyncio.sleep(0.04)  # Natural visual pacing for educational animation
        yield f"event: complete\ndata: {json.dumps({'waiting_quarantine': sess['pipeline'].is_waiting_quarantine_confirmation, 'completed': sess['pipeline'].is_completed})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


class QuarantineResolutionPayload(BaseModel):
    resolutions: List[Dict[str, Any]]  # [{"quarantine_id": "...", "action": "approve"|"squash"}]


@app.post("/api/pipeline/{session_id}/resolve-quarantine")
async def resolve_quarantine(session_id: str, payload: QuarantineResolutionPayload):
    """User confirms decisions on quarantined records, resuming Small Intestine absorption."""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    sess = SESSIONS[session_id]
    pipeline: BioDigestivePipeline = sess["pipeline"]

    new_events = list(pipeline.complete_absorption(payload.resolutions))
    sess["events"].extend(new_events)
    sess["is_waiting_quarantine"] = pipeline.is_waiting_quarantine_confirmation
    sess["is_completed"] = pipeline.is_completed

    return {
        "status": "resumed_and_completed",
        "new_events_count": len(new_events),
        "is_completed": pipeline.is_completed,
        "final_report": pipeline.final_report.model_dump() if pipeline.final_report else None
    }


@app.get("/api/pipeline/{session_id}/report")
async def get_report(session_id: str):
    """Returns the full pipeline report."""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    sess = SESSIONS[session_id]
    pipeline: BioDigestivePipeline = sess["pipeline"]

    if not pipeline.final_report and pipeline.is_completed:
        # Generate on the fly if needed
        pass

    return {
        "final_report": pipeline.final_report.model_dump() if pipeline.final_report else None,
        "immune_report": pipeline.immune.get_immune_report().model_dump(),
        "is_waiting_quarantine": pipeline.is_waiting_quarantine_confirmation,
        "is_completed": pipeline.is_completed
    }


@app.get("/api/pipeline/{session_id}/download/csv")
async def download_clean_csv(session_id: str):
    """Downloads absorbed clean records in standard CSV schema."""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    sess = SESSIONS[session_id]
    pipeline: BioDigestivePipeline = sess["pipeline"]
    csv_str = pipeline.small_intestine.export_csv()

    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=bio_absorbed_{sess['filename']}"}
    )


@app.get("/api/pipeline/{session_id}/download/json")
async def download_clean_json(session_id: str):
    """Downloads absorbed clean records in JSON format."""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    sess = SESSIONS[session_id]
    pipeline: BioDigestivePipeline = sess["pipeline"]
    json_str = pipeline.small_intestine.export_json()

    return Response(
        content=json_str,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=bio_absorbed_{sess['filename']}.json"}
    )


@app.get("/api/pipeline/{session_id}/download/waste")
async def download_waste_manifest(session_id: str):
    """Downloads Large Intestine excreted waste log."""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    sess = SESSIONS[session_id]
    pipeline: BioDigestivePipeline = sess["pipeline"]
    manifest_csv = pipeline.large_intestine.export_waste_manifest_csv()

    return Response(
        content=manifest_csv,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=bio_waste_manifest_{sess['filename']}"}
    )


# Serve Static UI files
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serves the main interactive children's educational digestive visualizer."""
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r") as f:
            return f.read()
    return "<h1>Bio-mimetic Digestive System ETL Pipeline Visualizer</h1>"

