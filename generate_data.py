"""Membuat data latih sintetis dari berbagai skenario lereng.
Label diambil dari rules.decide() (weak supervision)."""
import random
import pandas as pd
from rules import decide, LEVELS

random.seed(42)
U = random.uniform


def make_case(delta, rate, svib, rvib, rain):
    """Bangun riwayat telemetri 45 detik yang menghasilkan delta & rate tsb."""
    t_end = 1_000_000
    slope = []
    for k in range(4):
        t = t_end - (3 - k) * 15_000
        minutes_before_end = (3 - k) * 15_000 / 60000
        slope.append({"sent_at_ms": t, "tilt_deg": delta - rate * minutes_before_end,
                      "vib_rms": svib})
    ref = {"vib_rms": rvib}
    return slope, ref


SCENARIOS = {
    "normal":   lambda: (U(0, 1.5), U(0, 0.8), U(0, .3), U(0, .3), U(0, 40)),
    "common":   lambda: (U(0, 8),   U(0, 5),   U(.5, 2), U(.5, 2), U(0, 120)),
    "creep":    lambda: (U(1, 10),  U(.5, 5),  U(0, .8), U(0, .3), U(0, 80)),
    "heavyrain": lambda: (U(0, 8),  U(0, 4),   U(0, .8), U(0, .3), U(50, 200)),
    "random":   lambda: (U(0, 12),  U(0, 6),   U(0, 2),  U(0, 2),  U(0, 200)),
}


def main(n_per=800):
    rows = []
    for name, gen in SCENARIOS.items():
        for _ in range(n_per):
            delta, rate, svib, rvib, rain = gen()
            slope, ref = make_case(delta, rate, svib, rvib, rain)
            r = decide(slope, ref, 0.0, round(rain, 1))
            rows.append({"tilt_delta": round(delta, 3), "tilt_rate": round(rate, 3),
                         "slope_vib": round(svib, 3), "ref_vib": round(rvib, 3),
                         "rain24": round(rain, 1), "scenario": name,
                         "label": LEVELS.index(r["level"])})
    df = pd.DataFrame(rows).sample(frac=1, random_state=42)
    df.to_csv("data/training.csv", index=False)
    print("Data tersimpan: data/training.csv,", len(df), "baris")
    print(df["label"].map(lambda i: LEVELS[i]).value_counts())


if __name__ == "__main__":
    main()
