from math import sqrt, acos, degrees

G = 9.81

def summarize(samples):
    """samples: list of (t, (ax,ay,az), (gx,gy,gz)). Hanya 3 angka yang dikirim."""
    errs, tilts, rot = [], [], 0.0
    for _, (ax, ay, az), _ in samples:
        m = sqrt(ax * ax + ay * ay + az * az)
        errs.append(m - G)                                     # A: getaran
        tilts.append(degrees(acos(max(-1, min(1, az / m)))) if m else 0.0)  # B: kemiringan
    for (t0, _, _), (t1, _, (gx, gy, gz)) in zip(samples, samples[1:]):
        rot += sqrt(gx * gx + gy * gy + gz * gz) * (t1 - t0)   # C: rotasi
    n = len(samples)
    return {
        "vib_rms": round(sqrt(sum(e * e for e in errs) / n), 3),
        "tilt_deg": round(sum(tilts) / n, 2),
        "rotation_rad": round(rot, 3),
    }