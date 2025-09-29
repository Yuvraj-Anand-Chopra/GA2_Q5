from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
import numpy as np

app = FastAPI()

# Add CORS middleware
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
def analyze_telemetry(request: TelemetryRequest):
    try:
        # Load your telemetry data
        with open('q-vercel-latency.json', 'r') as f:
            data = json.load(f)
        
        results = []
        
        for region in request.regions:
            # Filter data for this region
            region_data = [record for record in data if record.get('region') == region]
            
            if not region_data:
                continue
                
            latencies = [record['latency_ms'] for record in region_data]
            uptimes = [record['uptime_percent'] for record in region_data]
            
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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
