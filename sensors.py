import json, math, random, subprocess, time
import atexit
import queue
import threading


G = 9.81

def parse_json_stream(text):
    dec = json.JSONDecoder()
    i, n, out = 0, len(text), {}
    while i < n:
        while i < n and text[i].isspace():
            i += 1
        if i >= n:
            break
        obj, i = dec.raw_decode(text, i)
        if isinstance(obj, dict):
            out.update(obj)
    return out

class TermuxSensor:
    def __init__(self, delay_ms=200):
        out = subprocess.run(["termux-sensor", "-l"], capture_output=True, text=True, check=True).stdout
        names = json.loads(out)["sensors"]
        self.acc = next(n for n in names if "ccelerometer" in n and "ncalibrated" not in n)
        self.gyr = next(n for n in names if "yroscope" in n and "ncalibrated" not in n)
        self.gyr_last = (0.0, 0.0, 0.0)
        self.q = queue.Queue(maxsize=50)
        self.p = subprocess.Popen(
            ["termux-sensor", "-s", f"{self.acc},{self.gyr}", "-d", str(delay_ms)],
            stdout=subprocess.PIPE, text=True)
        atexit.register(self.p.terminate)
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        buf, dec = "", json.JSONDecoder()
        for line in self.p.stdout:
            buf += line
            try:
                d, _ = dec.raw_decode(buf.lstrip())
            except json.JSONDecodeError:
                continue
            buf = ""
            if self.gyr in d:
                self.gyr_last = tuple(float(v) for v in d[self.gyr]["values"][:3])
            if self.acc in d:
                a = tuple(float(v) for v in d[self.acc]["values"][:3])
                if self.q.full():
                    try:
                        self.q.get_nowait()
                    except queue.Empty:
                        pass
                self.q.put((time.monotonic(), a, self.gyr_last))

    def read(self):
        return self.q.get(timeout=12)
class Simulator:
    """Skenario: still | creep (miring pelan) | slide (miring cepat) | vehicle (getaran umum)"""
    def __init__(self, scenario="still"):
        self.s = scenario
        self.t0 = time.monotonic()

    def read(self):
        time.sleep(0.2)
        t = time.monotonic() - self.t0
        tilt, noise = 0.0, 0.02
        if self.s == "creep":
            tilt = min(t * 0.15, 12)
        elif self.s == "slide":
            tilt, noise = min(t * 0.5, 25), 0.3
        elif self.s == "vehicle":
            noise = 0.8
        th = math.radians(tilt)
        a = (G * math.sin(th) + random.gauss(0, noise),
             random.gauss(0, noise),
             G * math.cos(th) + random.gauss(0, noise))
        g = tuple(random.gauss(0, 0.01 + noise / 20) for _ in range(3))
        return time.monotonic(), a, g

def make_source(kind, scenario="still"):
    return TermuxSensor() if kind == "termux" else Simulator(scenario)