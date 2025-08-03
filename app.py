from flask import Flask, request, render_template
import threading, requests, time, os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Track all submitted targets
targets = []  # Each is a dict with: url, ip, agent, time

# Send message to Telegram
def send_to_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": message}
        requests.post(url, data=data)
    except:
        pass

# Get visitor IP (Render safe)
def get_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0].strip()

# Get IP location
def get_location(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}").json()
        return res
    except:
        return {"query": ip, "country": "Unknown", "city": "Unknown", "isp": "Unknown"}

# Background ping thread
def ping_forever():
    while True:
        for target in targets:
            try:
                res = requests.get(target['url'], timeout=10)
                if res.status_code != 200:
                    send_to_telegram(f"⚠️ {target['url']} returned {res.status_code}")
            except Exception as e:
                send_to_telegram(f"""
❌ {target['url']} is DOWN!
Submitted by: {target['ip']}
Error: {str(e)}
                """)
        time.sleep(10)

# Start pinger
threading.Thread(target=ping_forever, daemon=True).start()

# Home route
@app.route("/", methods=["GET", "POST"])
def index():
    ip = get_ip()
    agent = request.headers.get("User-Agent")
    geo = get_location(ip)

    # Log visitor silently
    send_to_telegram(f"""
🛸 New Visit:
🌐 IP: {geo['query']}
🛰️ ISP: {geo.get('isp')}
📍 City: {geo.get('city')}
🌍 Country: {geo.get('country')}
🧠 Agent: {agent}
    """)

    if request.method == "POST":
        url = request.form.get("url")
        targets.append({
            "url": url,
            "ip": ip,
            "agent": agent,
            "time": datetime.utcnow().isoformat()
        })
        send_to_telegram(f"""
✅ New Site Submitted:
🔗 {url}
🧠 By: {ip}
📱 Agent: {agent}
⏱️ {datetime.utcnow().isoformat()} UTC
        """)
        return render_template("index.html", success=True)

    return render_template("index.html")
if __name__ == '__main__':
    app.run(host='0.0.0.0', port = 3000)
