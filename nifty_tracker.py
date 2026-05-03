import os
import sys
import yfinance as yf
from twilio.rest import Client
from datetime import datetime
import pytz

TWILIO_SID    = os.environ.get("TWILIO_SID")
TWILIO_TOKEN  = os.environ.get("TWILIO_TOKEN")
FROM_WHATSAPP = "whatsapp:+14155238886"
TO_WHATSAPP   = os.environ.get("TO_WHATSAPP")

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

WATCHLIST = {
    "RVNL":     "RVNL.NS",
    "Paradeep": "PARADEEP.NS",
}
ALERT_THRESHOLD = 3.0

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
        except:
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

def fetch_watchlist():
    results = {}
    for name, symbol in WATCHLIST.items():
        try:
            t = yf.Ticker(symbol)
            i = t.fast_info
            results[name] = {"price": round(i.last_price, 2), "chg": get_change_pct(i)}
        except:
            results[name] = {"price": 0, "chg": 0}
    return results

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

def build_morning_message(indices, gainers, losers, watchlist):
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    n50 = indices.get("Nifty 50", {})
    bn  = indices.get("Bank Nifty", {})
    nit = indices.get("Nifty IT", {})
    mid = indices.get("Midcap 50", {})
    vix = indices.get("India VIX", {})
    mood = market_mood(n50.get("chg", 0), vix.get("price", 15))
    lines = [
        f"📊 *Nifty Morning Report* 🌅",
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
        f"👀 *Your Watchlist*",
        f"",
    ]
    for name, data in watchlist.items():
        emoji = "🚨" if data["chg"] >= ALERT_THRESHOLD else "📌"
        lines.append(f"  {emoji} {name:<16} {fmt(data['chg'])}  ₹{data['price']}")
    lines += [
        f"",
        f"━━━━━━━━━━━━━━━━━",
        f"_Sent by your Nifty Tracker_ 🤖",
        f"_Closing summary at 3:45 PM IST_ 📊",
    ]
    return "\n".join(lines)

def build_closing_message(indices, gainers, losers, watchlist):
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    n50 = indices.get("Nifty 50", {})
    bn  = indices.get("Bank Nifty", {})
    nit = indices.get("Nifty IT", {})
    mid = indices.get("Midcap 50", {})
    vix = indices.get("India VIX", {})
    mood = market_mood(n50.get("chg", 0), vix.get("price", 15))
    chg = n50.get("chg", 0)
    if chg >= 0.5:      verdict = "✅ Good day! Market closed strong!"
    elif chg >= 0:      verdict = "😐 Flat day. Market barely moved."
    elif chg >= -0.5:   verdict = "😕 Slightly weak day."
    else:               verdict = "❌ Bad day. Market closed in red."
    lines = [
        f"📊 *Nifty Closing Report* 🌇",
        f"🗓 {now.strftime('%a, %d %b %Y')}  🕐 {now.strftime('%I:%M %p IST')}",
        f"",
        f"*Day Verdict:* {verdict}",
        f"*Market Mood:* {mood}",
        f"",
        f"━━━━━━━━━━━━━━━━━",
        f"📈 *Day Final Numbers*",
        f"",
        f"• *Nifty 50:*    {n50.get('price', 0):,}  {fmt(n50.get('chg', 0))}",
        f"• *Bank Nifty:*  {bn.get('price', 0):,}  {fmt(bn.get('chg', 0))}",
        f"• *Nifty IT:*    {nit.get('price', 0):,}  {fmt(nit.get('chg', 0))}",
        f"• *Midcap 50:*   {mid.get('price', 0):,}  {fmt(mid.get('chg', 0))}",
        f"• *India VIX:*   {vix.get('price', 0)}  {vix_label(vix.get('price', 15))}",
        f"",
        f"━━━━━━━━━━━━━━━━━",
        f"🏆 *Today Best Performers*",
    ]
    for name, chg in gainers:
        lines.append(f"  ✅ {name:<16} +{chg}%")
    lines += [f"", f"💔 *Today Worst Performers*"]
    for name, chg in losers:
        lines.append(f"  🔻 {name:<16} {chg}%")
    lines += [
        f"",
        f"━━━━━━━━━━━━━━━━━",
        f"👀 *Your Watchlist — End of Day*",
        f"",
    ]
    for name, data in watchlist.items():
        emoji = "🚨" if data["chg"] >= ALERT_THRESHOLD else "📌"
        lines.append(f"  {emoji} {name:<16} {fmt(data['chg'])}  ₹{data['price']}")
    lines += [
        f"",
        f"━━━━━━━━━━━━━━━━━",
        f"_Sent by your Nifty Tracker_ 🤖",
        f"_Next update tomorrow 9:15 AM IST_ 🌅",
    ]
    return "\n".join(lines)

def build_urgent_alert(watchlist):
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    lines = [
        f"🚨🚨 *URGENT STOCK ALERT* 🚨🚨",
        f"🕐 {now.strftime('%I:%M %p IST')}",
        f"",
        f"Stock in your watchlist moved *+{ALERT_THRESHOLD}%+* today!",
        f"",
        f"━━━━━━━━━━━━━━━━━",
    ]
    for name, data in watchlist.items():
        if data["chg"] >= ALERT_THRESHOLD:
            lines += [
                f"🔥 *{name}*",
                f"   Price:  ₹{data['price']}",
                f"   Change: +{data['chg']}% ▲",
                f"",
            ]
    lines += [
        f"━━━━━━━━━━━━━━━━━",
        f"_Check your portfolio now!_ 💰",
        f"_Sent by your Nifty Tracker_ 🤖",
    ]
    return "\n".join(lines)

def send_whatsapp(message):
    client = Client(TWILIO_SID, TWILIO_TOKEN)
    msg = client.messages.create(body=message, from_=FROM_WHATSAPP, to=TO_WHATSAPP)
    print(f"✅ Message sent! SID: {msg.sid}")

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "morning"
    print(f"📡 Mode: {mode}")
    print("📡 Fetching Nifty data...")
    indices = fetch_indices()
    print("📊 Fetching movers...")
    gainers, losers = fetch_movers()
    print("👀 Fetching watchlist...")
    watchlist = fetch_watchlist()

    # Send urgent alert if watchlist stock up 3%+
    urgent = {k: v for k, v in watchlist.items() if v["chg"] >= ALERT_THRESHOLD}
    if urgent:
        print(f"🚨 Urgent alert for: {list(urgent.keys())}")
        send_whatsapp(build_urgent_alert(watchlist))

    # Send morning or closing report
    if mode == "closing":
        message = build_closing_message(indices, gainers, losers, watchlist)
    else:
        message = build_morning_message(indices, gainers, losers, watchlist)

    print("\n--- PREVIEW ---")
    print(message)
    print("---------------\n")
    print("📲 Sending WhatsApp...")
    send_whatsapp(message)

if __name__ == "__main__":
    main()
