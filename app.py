from flask import Flask, request, render_template
import threading, requests, time, os
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()
app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

targets = []

def send_to_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": message}
        requests.post(url, data=data)
    except:
        pass

def get_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0].strip()

def get_location(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}").json()
        return res
    except:
        return {"query": ip, "country": "Unknown", "city": "Unknown", "isp": "Unknown"}

def chk():
    url = os.getenv("RENDER_EXTERNAL_URL")
    headers = {"User-Agent": "InternalUptimeBot"}
    if not url:
        return
    try:
        if requests.head(url, timeout=5, headers=headers).status_code == 200:
            while True:
                try:
                    requests.get(url, timeout=5, headers=headers)
                except:
                    pass
                time.sleep(10)
    except:
        pass

def is_same_domain(url1, url2):
    return urlparse(url1).netloc.lower().strip() == urlparse(url2).netloc.lower().strip()

def ping_forever():
    render_url = os.getenv("RENDER_EXTERNAL_URL")
    while True:
        for target in targets:
            if is_same_domain(target['url'], render_url):
                continue
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

threading.Thread(target=ping_forever, daemon=True).start()

def sign():
    print("=" * 10)
    print("       SULEIMAN PROJECT")
    print("=" * 10)
    print("   Created for Educational Purposes")
    print("   All rights reserved © 2025")
    print("=" * 10)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.headers.get("User-Agent") == "InternalUptimeBot":
        return "", 204

    ip = get_ip()
    agent = request.headers.get("User-Agent")
    geo = get_location(ip)

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
    threading.Thread(target=chk, daemon=True).start()
    sign()
    app.run(host='0.0.0.0', port=3000)
