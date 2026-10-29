VIB_T = 0.5          # m/s², dianggap bergetar
LEVELS = ["AMAN", "WASPADA", "SIAGA", "AWAS"]

def decide(slope, ref, tilt_base, rain24):
    """slope: list telemetri edge1 (terbaru di akhir). ref: telemetri edge2 terakhir."""
    cur = slope[-1]
    delta = abs(cur["tilt_deg"] - tilt_base)

    pts = [(m["sent_at_ms"] / 60000, m["tilt_deg"]) for m in slope
           if m["sent_at_ms"] >= cur["sent_at_ms"] - 60000]
    rate = 0.0                                   # derajat per menit
    if len(pts) >= 3 and pts[-1][0] - pts[0][0] >= 0.5:
        rate = abs(pts[-1][1] - pts[0][1]) / (pts[-1][0] - pts[0][0])

    slope_vib = cur["vib_rms"] >= VIB_T
    common = slope_vib and ref["vib_rms"] >= VIB_T   # keduanya bergetar: kendaraan/gempa/ketukan

    score, why = 0, []
    if common:
        why.append("getaran umum di kedua titik, diabaikan")
    else:
        if delta >= 5:   score += 2; why.append(f"miring {delta:.1f}° dari baseline")
        elif delta >= 2: score += 1; why.append(f"miring {delta:.1f}° dari baseline")
        if rate >= 3:    score += 2; why.append(f"laju {rate:.1f}°/menit")
        elif rate >= 1:  score += 1; why.append(f"laju {rate:.1f}°/menit")
        if slope_vib:    score += 1; why.append("getaran hanya di lereng")
    if rain24 >= 100:  score += 2; why.append(f"hujan 24 jam {rain24} mm")
    elif rain24 >= 50: score += 1; why.append(f"hujan 24 jam {rain24} mm")

    level = LEVELS[0 if score <= 1 else 1 if score == 2 else 2 if score <= 4 else 3]
    return {"level": level, "score": score, "common_motion": common,
            "tilt_delta": round(delta, 2), "tilt_rate": round(rate, 2),
            "rain24": rain24, "reason": "; ".join(why) or "kondisi normal"}