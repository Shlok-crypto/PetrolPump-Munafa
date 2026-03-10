# Fuel Inventory Profit Optimizer (FIPO) ⛽📈

*A modern, algorithmic dashboard designed to help petrol pump dealers proactively manage inventory and maximize profits ahead of retail fuel price hikes.*

FIPO (Fuel Inventory Profit Optimizer) is a real-time web application tailored for petroleum dealers (starting with Uttar Pradesh constants). It continuously monitors global economic factors—specifically **Brent Crude**, the **USD/INR exchange rate**, **MCX Crude futures**, and **live market news**—to compute a statistical probability of an impending government-mandated retail fuel price hike. 

By leveraging this probabilistic foresight, pump owners can make informed decisions to maximize their underground tank inventories before price hikes, effectively earning additional gain per liter beyond standard dealer commissions.

---

## 🎯 Key Features

*   **Live Market Data:** Fetches latest spot prices for Brent Crude ($/bbl) and USD to INR exchange rates.
*   **MCX Crude Monitoring:** Tracks real-time percentage changes in domestic crude oil futures via 5Paisa.
*   **Algorithmic Probability Engine:** Weighs critical thresholds of Brent, INR deprecation, positive MCX trends, and live "supply-disruption" news catalysts to generate a **0-100% Hike Probability Score**.
*   **Actionable Recommendations:** Outputs clear, actionable inventory advice:
    *   🟢 **NORMAL:** Maintain standard inventory operations.
    *   🟡 **MINIMIZE:** Restrict buying; prices may drop.
    *   🔴 **MAX INDENT:** Maximize underground inventory; price hike imminent.
*   **Integrated Profit Calculator:** A dynamic tool that lets dealers input their current underground tank fuel level and their own predicted hike amount to calculate exactly how much extra profit they stand to make by indenting early.
*   **Customizable Thresholds:** Features an Advanced Settings modal allowing owners to dynamically adjust the underlying mathematical triggers (Critical Brent price, Critical Rupee drop, and custom Tank Capacities) without touching the code.
*   **Premium Glassmorphism UI:** A sleek, dark-themed dashboard built with pure CSS grids, vibrant accents, and smooth data-loading animations.

<img width="1075" height="1723" alt="PetrolPump Munafa" src="https://github.com/user-attachments/assets/3ddc3fbc-84fd-460f-9dc2-c3700d385848" />

<img width="1115" height="877" alt="image" src="https://github.com/user-attachments/assets/c123ff0c-321d-4036-a620-3b75ae56c52c" />

---

## 🛠️ Tech Stack

**Backend**
*   [Python 3.10+](https://www.python.org/)
*   [FastAPI](https://fastapi.tiangolo.com/) - High-performance modern web framework for the API layer.
*   [Uvicorn](https://www.uvicorn.org/) - ASGI web server implementation.
*   [yfinance](https://pypi.org/project/yfinance/) - Scrapes Yahoo Finance for global benchmark data.
*   [BeautifulSoup4](https://pypi.org/project/beautifulsoup4/) & [Requests](https://pypi.org/project/requests/) - For live web scraping of MCX data.
*   **XML ElementTree** - For parsing live Google News RSS feeds.

**Frontend**
*   **HTML5 / Vanilla JavaScript** - No heavy frameworks, purely event-driven architecture using `fetch` API.
*   **Pure CSS3** - utilizing CSS Grid, Flexbox, native variables (`var(--)`), and backdrop-filters for the glassmorphism aesthetic.
*   **`localStorage` Interface** - Persists user-defined mathematical constants natively in the browser.

---

## 🚀 Getting Started

### Prerequisites
*   Python 3.8 or higher installed on your machine.
*   Git (optional, to clone the repository).

### Installation & Execution

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/PetrolPump-Munafa.git
   cd PetrolPump-Munafa
   ```

2. **Install dependencies**
   It is highly recommended to use a virtual environment.
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**
   Start the FastAPI Uvicorn server:
   ```bash
   python main.py
   # Or directly through uvicorn:
   # uvicorn main:app --reload
   ```

4. **Access the Dashboard**
   Open your preferred modern web browser and navigate to:
   ```text
   http://localhost:8000/
   ```
   *The dashboard data auto-refreshes every 60 seconds.*

---

## ⚙️ Configuration

The dashboard uses default constants tailored for Uttar Pradesh (March 2026 conditions). If market dynamics shift, you can modify the core logic natively inside the UI:

1. Click the **⚙️ Settings Gear** in the top right corner of the dashboard.
2. Edit the **Base Retail Petrol (₹)**, **Critical Brent Level ($)**, **Critical INR Level (₹)**, or **Tank Capacity (Liters)**.
3. Click **Save Changes**. The dashboard will instantly recalculate probabilities and profit margins natively based on your new parameters.

---

## 🛡️ License & Disclaimer
*This project is built for educational and demonstrative purposes only. Predictive algorithms rely on volatile market data and past performance does not guarantee future price revisions. Always consult official OMC (Oil Marketing Company) notices for actual price changes.*
