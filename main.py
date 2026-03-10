from fastapi import FastAPI, Query, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
import os
import pywhatkit
from fipo_logic import calculate_fipo, DEFAULT_BASE_RETAIL_PETROL, DEFAULT_CRITICAL_BRENT_LEVEL, DEFAULT_CRITICAL_INR_LEVEL, DEFAULT_TANK_CAPACITY_LITERS

app = FastAPI(title="FIPO Dashboard API")

# Models for Request Payloads
class WhatsAppNotification(BaseModel):
    number: str
    indian_basket: float
    usd_inr: float
    mcx_percent: float
    hike_probability: int
    predicted_hike: float
    dealer_commission: float
    extra_gain: float
    tank_capacity: int

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

def send_whatsapp_alert(payload: WhatsAppNotification):
    try:
        message = (
            f"📢 *Fuel Market Alert – Possible Price Hike*\n\n"
            f"🛢 Indian Crude Basket: ${payload.indian_basket:.2f}\n"
            f"📊 MCX Crude Oil: {payload.mcx_percent}%\n\n"
            f"📈 Price Hike Probability: {payload.hike_probability}%\n"
            f"⬆ Expected Price Increase: ₹{payload.predicted_hike:.2f} / L\n\n"
            f"💰 *Dealer Advantage*\n\n"
            f"• Dealer Commission: ₹{payload.dealer_commission:.2f} / L\n"
            f"• Estimated Extra Gain (Post Hike): ₹{payload.predicted_hike + payload.dealer_commission:.2f} / L\n\n"
            f"📦 *Strategy Tip:*\n"
            f"Stocking fuel before the price revision could increase margin on current inventory by ₹{payload.extra_gain * payload.tank_capacity:,.0f}."
        )
        
        # Ensures the number is formatted correctly (assumes frontend passes +91 format, if not it will fail)
        phone = payload.number if payload.number.startswith("+") else "+" + payload.number
        print(f"Sending WA alert to {phone}...")
        
        # sendwhatmsg_instantly opens whatsapp web, types the message and presses send.
        # wait_time=15 (time to allow whatsapp web to load), tab_close=True (closes tab after)
        pywhatkit.sendwhatmsg_instantly(phone, message, wait_time=15, tab_close=True, close_time=3)
        print("WA Notification Sent.")
    except Exception as e:
        print(f"Error sending WhatsApp notification: {e}")

@app.post("/api/notify/whatsapp")
def trigger_whatsapp_notification(payload: WhatsAppNotification, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_whatsapp_alert, payload)
    return {"status": "accepted", "message": "Notification dispatched"}

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def index():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
