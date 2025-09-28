from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import json
from pathlib import Path
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

class MetricsRequest(BaseModel):
    regions: list[str]
    threshold_ms: float

# Updated path for telemetry JSON (file at root level)
DATA_PATH = Path(__file__).parent.parent / "q-vercel-latency.json"

# Debug prints to verify environment during deployment
print("Current working directory:", os.getcwd())
print("File __file__ location:", __file__)
print("Telemetry JSON file path:", DATA_PATH)
print("Telemetry JSON exists:", DATA_PATH.exists())

with open(DATA_PATH) as f:
    telemetry_data = json.load(f)

@app.get("/")
async def root():
    return {"message": "FastAPI server running"}

@app.post("/metrics")
async def metrics_endpoint(req: MetricsRequest):
    response = {}
    for region in req.regions:
        recs = telemetry_data.get(region, [])
        if not recs:
            response[region] = {"avg_latency": None, "p95_latency": None,
                                "avg_uptime": None, "breaches": None}
            continue
        latencies = np.array([r["latency"] for r in recs])
        uptimes = np.array([r["uptime"] for r in recs])
        threshold = req.threshold_ms
        response[region] = {
            "avg_latency": round(float(np.mean(latencies)), 2),
            "p95_latency": round(float(np.percentile(latencies, 95)), 2),
            "avg_uptime": round(float(np.mean(uptimes)), 4),
            "breaches": int(np.sum(latencies > threshold))
        }
    return response
