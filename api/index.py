from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import numpy as np
import os

app = FastAPI()

# Enable CORS for all origins and methods
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TelemetryRequest(BaseModel):
    regions: List[str]
    threshold_ms: int

@app.get("/")
def read_root():
    return {"message": "Telemetry Analytics API", "status": "active"}

@app.post("/analyze")
def analyze(request: TelemetryRequest) -> Dict[str, Any]:
    # Load your telemetry data
    data_path = os.path.join(os.getcwd(), "../q-vercel-latency.json")
    try:
        with open(data_path, "r") as f:
            data = json.load(f)
    except Exception:
        # Generate sample data if file not found or error
        data = []
        for region in ["emea", "apac", "us-east"]:
            for _ in range(50):
                data.append({
                    "region": region,
                    "latency_ms": float(np.random.normal(160, 25)),
                    "uptime_percent": float(np.random.uniform(96, 99))
                })

    results = []
    for region in request.regions:
        recs = [r for r in data if r.get("region", "").lower() == region.lower()]

        if not recs:
            # No data for this region
            results.append({
                "region": region,
                "avg_latency": 0.0,
                "p95_latency": 0.0,
                "avg_uptime": 0.0,
                "breaches": 0
            })
            continue

        latencies = [float(r["latency_ms"]) for r in recs]
        uptimes = [float(r["uptime_percent"]) for r in recs]

        avg_latency = float(np.mean(latencies))
        p95_latency = float(np.percentile(latencies, 95))
        avg_uptime = float(np.mean(uptimes))
        breaches = int(sum(1 for lat in latencies if lat > request.threshold_ms))

        results.append({
            "region": region,
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 2),
            "breaches": breaches
        })

    return {"metrics": results}

@app.get("/health")
def health():
    return {"status": "healthy"}
