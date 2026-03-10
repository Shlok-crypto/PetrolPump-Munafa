import yfinance as yf
import datetime
import pytz
import requests
import re
import urllib.parse
import xml.etree.ElementTree as ET
import email.utils

# Default Constants for UP (March 2026)
DEFAULT_BASE_RETAIL_PETROL = 94.69
DEFAULT_CRITICAL_BRENT_LEVEL = 115.00
DEFAULT_CRITICAL_INR_LEVEL = 92.00
DEFAULT_TANK_CAPACITY_LITERS = 20000

def fetch_market_data():
    """Fetches Brent Crude and USD/INR from yfinance and calculates Indian Basket."""
    data = {"brent_crude": 0.0, "usd_inr": 0.0, "indian_basket": 0.0}
    try:
        # Brent Crude (Spot): BZ=F
        brent = yf.Ticker("BZ=F")
        brent_hist = brent.history(period="1d")
        if not brent_hist.empty:
            brent_val = round(brent_hist["Close"].iloc[-1], 2)
            data["brent_crude"] = brent_val
            # Indian Basket: 65% Oman/Dubai (Sour) + 35% Brent (Sweet)
            # Proxying Dubai as Brent - $2.50 typical spread
            dubai_proxy = brent_val - 2.50
            data["indian_basket"] = round((dubai_proxy * 0.65) + (brent_val * 0.35), 2)
    except Exception as e:
        print(f"Error fetching Brent: {e}")
        data["brent_crude"] = 116.50  # Fallback
        data["indian_basket"] = 114.87 # Fallback

    try:
        # USD/INR: INR=X
        usd_inr = yf.Ticker("INR=X")
        inr_hist = usd_inr.history(period="1d")
        if not inr_hist.empty:
            data["usd_inr"] = round(inr_hist["Close"].iloc[-1], 2)
    except Exception as e:
        print(f"Error fetching USD/INR: {e}")
        data["usd_inr"] = 92.35 # Fallback based on user example
        
    return data

def calculate_mcx_score():
    """Fetch MCX Crude Oil futures from 5paisa and calculate score (20% weight)"""
    try:
        url = "https://www.5paisa.com/commodity-trading/mcx-crudeoil-price"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=5)
        
        # User HTML: <div class="commodity-page__percentage stock--up"><span class="gain-iconarrow"></span>419 (5.01%)</div>
        perc_match = re.search(r'class="commodity-page__percentage[^>]*>.*?\(([-+]?[\d\.]+)%\)', r.text, re.DOTALL)
        
        if perc_match:
            pct_change = float(perc_match.group(1))
            print(f"--- 5PAISA MCX DATA ---")
            print(f"Extracted Percentage Change: {pct_change}%")
            print("-----------------------")
            if pct_change > 2.0:
                return 20, pct_change # Full points for > 2% jump
            elif pct_change > 0:
                return 10, pct_change
            return 0, pct_change
            
        print("--- 5PAISA MCX DATA ---")
        print("Percentage change not found in HTML. Check selector.")
        print("-----------------------")
        return 15, "N/A" # mock if not found
    except Exception as e:
        print(f"Error fetching MCX: {e}")
        return 15, "N/A"

def get_relative_time(pub_date_str):
    try:
        dt = email.utils.parsedate_to_datetime(pub_date_str)
        now = datetime.datetime.now(datetime.timezone.utc)
        diff = now - dt
        if diff.days > 0:
            return f"{diff.days}d ago"
        hours = diff.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        minutes = (diff.seconds % 3600) // 60
        if minutes > 0:
            return f"{minutes}m ago"
        return "Just now"
    except:
        return ""

def calculate_news_score():
    """Fetch Ministry of Petroleum news via Google News RSS and calculate score (10% weight)"""
    try:
        raw_query = (
    '('
    '"Petroleum Ministry" OR "OMC margin" OR "under-recovery" OR "excise duty cut" OR "IOCL" OR "BPCL" OR "HPCL" OR "fuel price hike India"'
    ') when:7d'
)
        query = urllib.parse.quote(raw_query)
        url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        root = ET.fromstring(r.text)
        
        score = 0
        headlines = []

        # Define highly specific Indian market keywords
        omc_loss_keywords = ['under-recovery', 'loss', 'margin hit', 'margin drop', 'debt']
        excise_cut_keywords = ['excise cut', 'tax cut', 'relief', 'duty cut']
        price_change_keywords = ['hike', 'increase', 'revision', 'upward']

        print(f"--- GOOGLE NEWS RSS DATA ---")
        for item in root.findall('./channel/item')[:6]: # Get up to 6 news items for 3-column grid
            title = item.find('title').text.lower()
            original_title = item.find('title').text
            title_parts = original_title.rsplit(' - ', 1)
            clean_title = title_parts[0]
            source = title_parts[1] if len(title_parts) > 1 else ""
            
            pub_date_node = item.find('pubDate')
            pub_date_str = pub_date_node.text if pub_date_node is not None else ""
            rel_time = get_relative_time(pub_date_str)
            
            link_node = item.find('link')
            link = link_node.text if link_node is not None else "#"
            
            headlines.append({
                "title": clean_title,
                "source": source,
                "link": link,
                "time": rel_time
            })
            
            safe_title = title.encode('ascii', 'ignore').decode('ascii')
            print(f"- News Title Found: {safe_title}")

            # calculate hours ago
            try:
                pub_date = date_parser.parse(pub_date_str)
                nowtemp = datetime.now(timezone.utc)
                diff = nowtemp - pub_date
                hours_ago = diff.total_seconds() / 3600  # hours
            except:
                hours_ago = 0

            # Scoring logic
            item_score = 0
            # Price-change keywords
            if any(kw in title for kw in price_change_keywords):
                item_score += 4

            # OMC Under-recovery keywords — high penalty/alert weight
            if any(kw in title for kw in omc_loss_keywords):
                item_score += 6

            # Excise cut / tax relief keywords — very bullish indicator (actually suppresses hike probability, but for our metrics it's max importance)
            if any(kw in title for kw in excise_cut_keywords):
                item_score -= 8  # Reduces hike probability significantly

            # Decay score by recency (more recent, higher weight)
            recency_weight = max(0.5, (168 - hours_ago) / 168)  # between 0.5 and 1
            weighted_score = item_score * recency_weight

            score += weighted_score
        
        final_score = min(round(score, 2), 10)

        print(f"Total News Score: {final_score}")
        print("----------------------------")
                
        return final_score, headlines # Cap at 10
    except Exception as e:
        print(f"Error fetching News: {e}")
        return 8, [] # fallback

def calculate_fipo(
    base_retail_petrol: float = DEFAULT_BASE_RETAIL_PETROL,
    critical_brent_level: float = DEFAULT_CRITICAL_BRENT_LEVEL,
    critical_inr_level: float = DEFAULT_CRITICAL_INR_LEVEL,
    tank_capacity_liters: int = DEFAULT_TANK_CAPACITY_LITERS
):
    market_data = fetch_market_data()
    indian_basket = market_data.get("indian_basket", 0)
    usd_inr = market_data.get("usd_inr", 0)
    
    # Calculate Scores
    # Indian Basket (40%) - Dynamic relative to critical_brent_level (acting as critical basket level)
    basket_score = 0
    if indian_basket >= (critical_brent_level - 5): # e.g. >= 110 if critical is 115
        basket_score = 40
    elif indian_basket >= (critical_brent_level - 25): # e.g. >= 90 if critical is 115
        basket_score = 25
        
    # Currency (30%) - Dynamic relative to critical_inr_level
    inr_score = 0
    if usd_inr >= (critical_inr_level + 0.50): # e.g. >= 92.50 if critical is 92.00
        inr_score = 30
    elif usd_inr >= (critical_inr_level - 0.50): # e.g. >= 91.50 if critical is 92.00
        inr_score = 20
        
    mcx_score, mcx_val = calculate_mcx_score()
    news_score, news_headlines = calculate_news_score()
    
    # Total Probability (Clamp to 0-100)
    hike_prob = max(0, min(100, int(basket_score + inr_score + mcx_score + news_score)))
    print(f"Hike Probability: {hike_prob}")
    
    # Recommendation Logic
    recommendation = "NORMAL"
    if hike_prob > 70:
        recommendation = "MAX_INDENT"
    elif hike_prob < 40:
        recommendation = "MINIMIZE"
        
    # Inventory Gain (Assuming hypothetical hike of ₹5 if probability > 70%, otherwise scale down)
    predicted_hike = 5.0 if hike_prob > 70 else (2.0 if hike_prob > 40 else 0)
    estimated_gain = tank_capacity_liters * predicted_hike
    dealer_commission = 3.2
    
    tz_ist = pytz.timezone('Asia/Kolkata')
    timestamp = datetime.datetime.now(tz_ist).isoformat()
    
    basket_rat = "Critical Crude Basket" if basket_score == 40 else ("High Crude Basket" if basket_score > 0 else "")
    inr_rat = "Severe Rupee Drop" if inr_score == 30 else ("Weak Rupee" if inr_score > 0 else "")
    mcx_rat = "Strong MCX Jump" if mcx_score == 20 else ("Positive MCX Trend" if mcx_score > 0 else "")
    news_rat = "OMC Margin Pressure" if news_score > 5 else ("Excise Cut Hints" if news_score < 0 else "")
    
    rationale_parts = []
    if basket_rat: rationale_parts.append(basket_rat)
    if inr_rat: rationale_parts.append(inr_rat)
    if mcx_rat: rationale_parts.append(mcx_rat)
    if news_rat: rationale_parts.append(news_rat)
    
    rationale = " + ".join(rationale_parts) if rationale_parts else "Market stable."
    
    return {
        "timestamp": timestamp,
        "indian_basket": indian_basket,
        "usd_inr": usd_inr,
        "hike_probability": hike_prob,
        "recommendation": recommendation,
        "predicted_hike_per_liter": predicted_hike,
        "dealer_commission_per_liter": dealer_commission,
        "extra_gain_per_liter": predicted_hike,  # The extra profit is exactly the hike difference avoided
        "estimated_gain": estimated_gain,
        "tank_capacity": tank_capacity_liters,
        "rationale": rationale,
        "rationale_brent": basket_rat,
        "rationale_inr": inr_rat,
        "rationale_mcx": mcx_rat,
        "rationale_news": news_rat,
        "mcx_percent": mcx_val,
        "news_headlines": news_headlines
    }
calculate_fipo()