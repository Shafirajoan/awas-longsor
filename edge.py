import argparse, json, subprocess, time, uuid
import config as C
from sensors import make_source
from processing import summarize

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--role", choices=["slope", "ref"], required=True)
    p.add_argument("--source", choices=["termux", "simulator"], default="termux")
    p.add_argument("--scenario", default="still")
    p.add_argument("--window", type=int, default=10)
    a = p.parse_args()

    dev = {"slope": "edge1", "ref": "edge2"}[a.role]
    src = make_source(a.source, a.scenario)
    c = C.new_client(f"{dev}-{uuid.uuid4().hex[:6]}")

    def on_connect(cl, ud, flags, rc, props):
        print("[MQTT] connected:", rc)
        cl.subscribe(C.topic("alerts"), qos=1)

    def on_message(cl, ud, msg):
        d = json.loads(msg.payload)
        print("[ALERT]", d)
        if a.role == "ref" and a.source == "termux":
            subprocess.run(["termux-vibrate", "-d", "1500"])
            subprocess.run(["termux-notification", "--title",
                            f"awaslongsor {d['level']}", "--content", d["reason"]])

    c.on_connect, c.on_message = on_connect, on_message
    c.connect(C.HOST, C.PORT, 60)
    c.loop_start()

    seq = 0
    while True:
        win = [src.read() for _ in range(a.window)]
        seq += 1
        payload = {"device_id": dev, "role": a.role, "sequence": seq,
                   "sent_at_ms": int(time.time() * 1000), **summarize(win)}
        c.publish(C.topic(f"edge/{dev}/telemetry"), json.dumps(payload), qos=1)
        print("[TX]", payload)

if __name__ == "__main__":
    main()