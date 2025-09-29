from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
import numpy as np

app = FastAPI()

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
        # Load the JSON file (it exists in /var/task/ according to debug)
        with open('q-vercel-latency.json', 'r') as f:
            data = json.load(f)
        
        results = []
        
        for region in request.regions:
            # Filter data for this region
            region_data = [record for record in data if record.get('region') == region]
            
            if not region_data:
                # If no data for region, return default values
                results.append({
                    "region": region,
                    "avg_latency": 0.0,
                    "p95_latency": 0.0,
                    "avg_uptime": 0.0,
                    "breaches": 0
                })
                continue
            
            latencies = [record['latency_ms'] for record in region_data if 'latency_ms' in record]
            uptimes = [record['uptime_percent'] for record in region_data if 'uptime_percent' in record]
            
            if latencies and uptimes:
                avg_latency = float(np.mean(latencies))
                p95_latency = float(np.percentile(latencies, 95))
                avg_uptime = float(np.mean(uptimes))
                breaches = int(sum(1 for lat in latencies if lat > request.threshold_ms))
            else:
                avg_latency = 0.0
                p95_latency = 0.0
                avg_uptime = 0.0
                breaches = 0
            
            results.append({
                "region": region,
                "avg_latency": round(avg_latency, 2),
                "p95_latency": round(p95_latency, 2),
                "avg_uptime": round(avg_uptime, 2),
                "breaches": breaches
            })
        
        return {"metrics": results}
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Telemetry data file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format in data file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/debug")
def debug_info():
    """Debug endpoint to check file access"""
    try:
        import os
        current_dir = os.getcwd()
        files_in_dir = os.listdir('.')
        
        # Try to read a few lines from the JSON file
        sample_data = None
        try:
            with open('q-vercel-latency.json', 'r') as f:
                sample_data = json.load(f)[:3]  # First 3 records
        except:
            sample_data = "Could not read file"
        
        return {
            "current_directory": current_dir,
            "files": files_in_dir,
            "json_file_exists": os.path.exists('q-vercel-latency.json'),
            "sample_data": sample_data
        }
    except Exception as e:
        return {"debug_error": str(e)}
