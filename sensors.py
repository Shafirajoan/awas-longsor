import json, math, random, subprocess, time

G = 9.81

class TermuxSensor:
    def __init__(self):
        out = subprocess.run(["termux-sensor", "-l"], capture_output=True,
                             text=True, check=True).stdout
        names = json.loads(out)["sensors"]
        self.acc = next(n for n in names if "ccelerometer" in n and "ncalibrated" not in n)
        self.gyr = next(n for n in names if "yroscope" in n and "ncalibrated" not in n)

    def read(self):
        out = subprocess.run(
            ["termux-sensor", "-s", f"{self.acc},{self.gyr}", "-n", "1"],
            capture_output=True, text=True, timeout=12, check=True).stdout
        d = json.loads(out)
        a = tuple(float(v) for v in d[self.acc]["values"][:3])
        g = tuple(float(v) for v in d[self.gyr]["values"][:3])
        return time.monotonic(), a, g

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