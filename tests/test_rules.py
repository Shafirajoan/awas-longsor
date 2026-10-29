import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from rules import decide

def m(tilt, vib, t=0):
    return {"tilt_deg": tilt, "vib_rms": vib, "sent_at_ms": t}

def test_aman():
    r = decide([m(0.1, 0.05)], m(0, 0.05), 0.0, 0)
    assert r["level"] == "AMAN"

def test_miring_tanpa_getaran_waspada():
    assert decide([m(6, 0.05)], m(0, 0.05), 0.0, 0)["level"] == "WASPADA"

def test_getaran_umum_diabaikan():
    r = decide([m(6, 1.0)], m(0, 1.0), 0.0, 0)
    assert r["common_motion"] and r["level"] == "AMAN"

def test_miring_getar_lereng_siaga():
    assert decide([m(6, 0.9)], m(0, 0.05), 0.0, 0)["level"] == "SIAGA"

def test_hujan_lebat_plus_miring_siaga():
    assert decide([m(6, 0.05)], m(0, 0.05), 0.0, 120)["level"] == "SIAGA"