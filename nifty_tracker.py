import os
import yfinance as yf
from twilio.rest import Client
from datetime import datetime
import pytz

# ─────────────────────────────────────────
# YOUR TWILIO CREDENTIALS
# ─────────────────────────────────────────
TWILIO_SID    = os.environ.get("TWILIO_SID", "ACxxxxxxxxxxxxxxxx")
TWILIO_TOKEN  = os.environ.get("TWILIO_TOKEN", "your_auth_token")
FROM_WHATSAPP = "whatsapp:+14155238886"
TO_WHATSAPP   = os.environ.get("TO_WHATSAPP", "whatsapp:+91XXXXXXXXXX")

# ─────────────────────────────────────────
# INDICES
# ─────────────────────────────────────────
INDICES = {
    "Nifty 50":   "^NSEI",
    "Bank Nifty": "^NSEBANK",
    "Nifty IT":   "^CNXIT",
    "Midcap 50":  "^NSEMDCP50",
    "India VIX":  "^INDIAVIX",
}

TOP_STOCKS = {
    "Reliance":      "RELIANCE.NS",
    "HDFC Bank":     "HDFCBANK.NS",
    "Infosys":       "INFY.NS",
    "TCS":           "TCS.NS",
    "ICICI Bank":    "ICICIBANK.NS",
    "Bajaj Finance": "BAJFINANCE.NS",
    "Wipro":         "WIPRO.NS",
    "HUL":           "HINDUNILVR.NS",
    "L&T":           "LT.NS",
    "Asian Paints":  "ASIANPAINT.NS",
}

def get_change_pct(info):
    try:
        return round((info.last_price / info.previous_close - 1) * 100, 2)
    except:
        return 0.0

def fetch_indices():
    results = {}
    for name, symbol in INDICES.items():
        try:
            t = yf.Ticker(symbol)
            i = t.fast_info
            results[name] = {"price": round(i.last_price, 2), "chg": get_change_pct(i)}
        except Exception as e:
            results[name] = {"price": 0, "chg": 0}
    return results

def fetch_movers():
    moves = []
    for name, symbol in TOP_STOCKS.items():
        try:
            chg = get_change_pct(yf.Ticker(symbol).fast_info)
            moves.append((name, chg))
        except:
            pass
    moves.sort(key=lambda x: x[1], reverse=True)
    return moves[:3], moves[-3:][::-1]

def market_mood(chg, vix):
    if chg >= 1.0 and vix < 16:  return "🟢 STRONGLY BULLISH"
    elif chg >= 0.3:              return "🟢 BULLISH"
    elif chg <= -1.0:             return "🔴 STRONGLY BEARISH"
    elif chg <= -0.3:             return "🔴 BEARISH"
    else:                         return "🟡 FLAT / SIDEWAYS"

def vix_label(vix):
    if vix < 12:   return "😴 Very Calm"
    elif vix < 16: return "😌 Calm"
    elif vix < 20: return "😐 Moderate"
    elif vix < 25: return "😬 Elevated"
    else:          return "😱 High Fear"

def fmt(chg):
    return f"{'▲' if chg >= 0 else '▼'} {'+' if chg >= 0 else ''}{chg}%"

def build_message(indices, gainers, losers):
    ist  = pytz.timezone("Asia/Kolkata")
    now  = datetime.now(ist)
    n50  = indices.get("Nifty 50",   {})
    bn   = indices.get("Bank Nifty", {})
    nit  = indices.get("Nifty IT",   {})
    mid  = indices.get("Midcap 50",  {})
    vix  = indices.get("India VIX",  {})
    mood = market_mood(n50.get("chg", 0), vix.get("price", 15))

    lines = [
        f"📊 *Nifty Daily Report*",
        f"🗓 {now.strftime('%a, %d %b %Y')}  🕐 {now.strftime('%I:%M %p IST')}",
        f"",
        f"*Market Mood:* {mood}",
        f"",
        f"━━━━━━━━━━━━━━━━━",
        f"📈 *Index Snapshot*",
        f"",
        f"• *Nifty 50:*    {n50.get('price', 0):,}  {fmt(n50.get('chg', 0))}",
        f"• *Bank Nifty:*  {bn.get('price', 0):,}  {fmt(bn.get('chg', 0))}",
        f"• *Nifty IT:*    {nit.get('price', 0):,}  {fmt(nit.get('chg', 0))}",
        f"• *Midcap 50:*   {mid.get('price', 0):,}  {fmt(mid.get('chg', 0))}",
        f"• *India VIX:*   {vix.get('price', 0)}  {vix_label(vix.get('price', 15))}",
        f"",
        f"━━━━━━━━━━━━━━━━━",
        f"🚀 *Top Gainers*",
    ]
    for name, chg in gainers:
        lines.append(f"  ✅ {name:<16} +{chg}%")
    lines += [f"", f"📉 *Top Losers*"]
    for name, chg in losers:
        lines.append(f"  🔻 {name:<16} {chg}%")
    lines += [
        f"",
        f"━━━━━━━━━━━━━━━━━",
        f"_Sent by your Nifty Tracker_ 🤖",
        f"_Next update tomorrow at 9:15 AM IST_",
    ]
    return "\n".join(lines)

def send_whatsapp(message):
    client = Client(TWILIO_SID, TWILIO_TOKEN)
    msg = client.messages.create(body=message, from_=FROM_WHATSAPP, to=TO_WHATSAPP)
    print(f"✅ Message sent! SID: {msg.sid}")

def main():
    print("📡 Fetching Nifty data...")
    indices = fetch_indices()
    print("📊 Fetching movers...")
    gainers, losers = fetch_movers()
    print("📝 Building message...")
    message = build_message(indices, gainers, losers)
    print("\n--- PREVIEW ---")
    print(message)
    print("---------------\n")
    print("📲 Sending WhatsApp...")
    send_whatsapp(message)

if __name__ == "__main__":
    main()
