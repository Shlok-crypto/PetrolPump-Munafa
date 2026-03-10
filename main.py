from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import os
from fipo_logic import calculate_fipo, DEFAULT_BASE_RETAIL_PETROL, DEFAULT_CRITICAL_BRENT_LEVEL, DEFAULT_CRITICAL_INR_LEVEL, DEFAULT_TANK_CAPACITY_LITERS

app = FastAPI(title="FIPO Dashboard API")

# Ensure static directory exists
os.makedirs("static", exist_ok=True)

# Endpoint to get predictions
@app.get("/api/predict")
def get_prediction(
    base_retail_petrol: float = Query(DEFAULT_BASE_RETAIL_PETROL, description="Base Retail Petrol Price"),
    critical_brent_level: float = Query(DEFAULT_CRITICAL_BRENT_LEVEL, description="Critical Brent Level"),
    critical_inr_level: float = Query(DEFAULT_CRITICAL_INR_LEVEL, description="Critical INR Level"),
    tank_capacity_liters: int = Query(DEFAULT_TANK_CAPACITY_LITERS, description="Tank Capacity in Liters")
):
    return calculate_fipo(
        base_retail_petrol=base_retail_petrol,
        critical_brent_level=critical_brent_level,
        critical_inr_level=critical_inr_level,
        tank_capacity_liters=tank_capacity_liters
    )

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def index():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
