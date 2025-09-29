from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import numpy as np
import os

app = FastAPI()

# Enable CORS for POST from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS", "GET"],
    allow_headers=["*"],
)

class TelemetryRequest(BaseModel):
    regions: List[str]
    threshold_ms: int

@app.get("/")
def read_root() -> Dict[str, Any]:
    return {"message": "Telemetry Analytics API", "status": "active"}

@app.options("/analyze")
def options_analyze() -> Dict[str, str]:
    # CORS preflight handler
    return {"allow": "POST, OPTIONS"}

@app.post("/analyze")
def analyze_telemetry(request: TelemetryRequest) -> Dict[str, Any]:
    # 1. Load the JSON data
    data_path = os.path.join(os.getcwd(), "q-vercel-latency.json")
    try:
        with open(data_path, "r") as f:
            data = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load data file: {e}")

    # 2. Normalize field names
    #    The file uses "latency_ms" and "uptime_pct"
    for rec in data:
        if "uptime_pct" in rec:
            rec["uptime_percent"] = rec.pop("uptime_pct")

    # 3. Compute metrics per requested region
    results = []
    for region in request.regions:
        # Filter records (case-insensitive)
        recs = [r for r in data if r.get("region", "").lower() == region.lower()]
        if not recs:
            # No data → return zeros
            results.append({
                "region": region,
                "avg_latency": 0.0,
                "p95_latency": 0.0,
                "avg_uptime": 0.0,
                "breaches": 0
            })
            continue

        latencies = [float(r["latency_ms"]) for r in recs]
        uptimes  = [float(r["uptime_percent"]) for r in recs]

        avg_latency = float(np.mean(latencies))
        p95_latency = float(np.percentile(latencies, 95))
        avg_uptime  = float(np.mean(uptimes))
        breaches    = int(sum(1 for x in latencies if x > request.threshold_ms))

        results.append({
            "region": region,
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 2),
            "breaches": breaches
        })

    return {"metrics": results}

@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "healthy", "service": "telemetry-analytics"}

# Vercel serverless handler
handler = app
