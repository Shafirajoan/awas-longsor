"""Komponen AI: prediksi level risiko memakai model Random Forest.
Melengkapi rules.py (rule-based), tidak menggantikannya."""
import os
from rules import LEVELS, VIB_T

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model", "risk_model.pkl")
FEATURES = ["tilt_delta", "tilt_rate", "slope_vib", "ref_vib", "rain24"]

_model = None
_tried = False


def extract_features(slope, ref, tilt_base, rain24):
    """Ubah telemetri mentah jadi 5 fitur numerik untuk model."""
    cur = slope[-1]
    delta = abs(cur["tilt_deg"] - tilt_base)
    pts = [(m["sent_at_ms"] / 60000, m["tilt_deg"]) for m in slope
           if m["sent_at_ms"] >= cur["sent_at_ms"] - 60000]
    rate = 0.0
    if len(pts) >= 3 and pts[-1][0] - pts[0][0] >= 0.1:
        rate = abs(pts[-1][1] - pts[0][1]) / (pts[-1][0] - pts[0][0])
    return [delta, rate, cur["vib_rms"], ref["vib_rms"], rain24]


def _load():
    global _model, _tried
    if _tried:
        return _model
    _tried = True
    try:
        import joblib
        _model = joblib.load(MODEL_PATH)
        print("[ML] model dimuat:", MODEL_PATH)
    except Exception as e:
        print("[ML] model tidak tersedia, pakai rule-based saja:", e)
        _model = None
    return _model


def predict_from_features(feats):
    model = _load()
    if model is None:
        return None
    proba = model.predict_proba([feats])[0]
    idx = int(proba.argmax())
    label = model.classes_[idx]
    return {"level": LEVELS[int(label)], "confidence": round(float(proba[idx]), 3)}


def predict(slope, ref, tilt_base, rain24):
    """Return {'level','confidence'} atau None jika model belum ada."""
    try:
        return predict_from_features(extract_features(slope, ref, tilt_base, rain24))
    except Exception as e:
        print("[ML] gagal prediksi:", e)
        return None
