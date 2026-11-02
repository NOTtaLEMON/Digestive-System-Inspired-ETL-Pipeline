"""
Bio-mimetic Digestive System ETL Pipeline Server Launcher.
Run this script to launch the FastAPI web application and interactive educational dashboard.
"""
import sys
import uvicorn

if __name__ == "__main__":
    print("=" * 70)
    print("🧬 Starting Bio-mimetic Digestive System ETL Pipeline Server")
    print("Children's Educational Data Metabolism & Immune Surveillance Engine")
    print("Server running at: http://localhost:8000")
    print("=" * 70)
    uvicorn.run("bio_etl.server:app", host="0.0.0.0", port=8000, reload=True)

