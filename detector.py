import json, time, urllib.request
from collections import deque
import config as C
from rules import decide

slope_hist = deque(maxlen=30)
ref_last = None
calib = []
baseline = None
rain = {"mm24": 0.0, "manual_until": 0, "fetched": 0}
pending = {"level": "AMAN", "n": 0}
current = "AMAN"

def fetch_rain():
    url = ("https://api.open-meteo.com/v1/forecast?"
           f"latitude={C.LAT}&longitude={C.LON}&hourly=precipitation"
           "&past_hours=24&forecast_hours=1&timezone=Asia%2FJakarta")
    with urllib.request.urlopen(url, timeout=10) as r:
        vals = json.load(r)["hourly"]["precipitation"]
    return round(sum(v for v in vals if v is not None), 1)

def refresh_rain():
    now = time.time()
    if now < rain["manual_until"] or now - rain["fetched"] < 600:
        return
    rain["fetched"] = now
    try:
        rain["mm24"] = fetch_rain()
        print("[RAIN] 24 jam:", rain["mm24"], "mm")
    except Exception as e:
        print("[RAIN] gagal:", e)

def on_connect(c, ud, flags, rc, props):
    print("[MQTT] connected:", rc)
    c.subscribe(C.topic("edge/+/telemetry"), qos=1)
    c.subscribe(C.topic("rain"), qos=1)
    c.subscribe(C.topic("cmd/calibrate"), qos=1)

def handle(c, msg):
    global ref_last, baseline, calib, current
    t = msg.topic
    data = json.loads(msg.payload)
    if t.endswith("/cmd/calibrate"):
        baseline, calib = None, []
        print("[CAL] kalibrasi ulang")
        return
    if t.endswith("/rain"):                       # override manual untuk demo
        rain["mm24"] = float(data["mm24"])
        rain["manual_until"] = time.time() + 1800
        return
    if data["device_id"] == "edge2":
        data["_rx"] = time.time()
        ref_last = data
        return
    slope_hist.append(data)
    if baseline is None:                          # 5 pesan pertama = baseline
        calib.append(data["tilt_deg"])
        if len(calib) >= 5:
            baseline = sum(calib) / len(calib)
            print(f"[CAL] baseline {baseline:.2f}°")
        return
    if ref_last is None or time.time() - ref_last["_rx"] > 60:
        c.publish(C.topic("status"), json.dumps({"level": "OFFLINE",
                  "reason": "edge2 belum/tidak mengirim data"}), retain=True)
        return
    refresh_rain()
    r = decide(list(slope_hist), ref_last, baseline, rain["mm24"])

    # debounce: level baru harus muncul 2x berturut-turut
    if r["level"] == pending["level"]:
        pending["n"] += 1
    else:
        pending["level"], pending["n"] = r["level"], 1
    changed = pending["n"] >= 2 and r["level"] != current
    if changed:
        current = r["level"]
    r["level"] = current
    r["sent_at_ms"] = int(time.time() * 1000)
    c.publish(C.topic("status"), json.dumps(r), retain=True)
    print("[STATUS]", r)
    if changed and current in ("SIAGA", "AWAS"):
        c.publish(C.topic("alerts"), json.dumps(r), qos=1)
        print("[ALERT SENT]", current)
        
def on_message(c, ud, msg):
    try:
        handle(c, msg)
    except (KeyError, ValueError) as e:
        print("[SKIP] pesan tidak dikenali:", msg.topic, e)

def main():
    c = C.new_client("detector-awaslongsor")
    c.on_connect, c.on_message = on_connect, on_message
    c.connect(C.HOST, C.PORT, 60)
    print("[DETECTOR] menunggu edge1 & edge2, PROJECT_ID =", C.PROJECT_ID)
    c.loop_forever()

if __name__ == "__main__":
    main()