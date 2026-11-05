import os, sys
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ML_predictor import predict_from_features, MODEL_PATH
from rules import LEVELS

pytestmark = pytest.mark.skipif(not os.path.exists(MODEL_PATH),
                                reason="model belum dilatih (jalankan train_model.py)")
# urutan fitur: tilt_delta, tilt_rate, slope_vib, ref_vib, rain24

def test_kondisi_normal_aman():
    assert predict_from_features([0.3, 0.1, 0.1, 0.1, 5])["level"] == "AMAN"

def test_getaran_umum_diabaikan():
    assert predict_from_features([0.5, 0.2, 1.5, 1.5, 0])["level"] == "AMAN"

def test_miring_cepat_dan_hujan_deras_berbahaya():
    assert predict_from_features([8, 4, 0.2, 0.1, 150])["level"] in ("SIAGA", "AWAS")

def test_output_valid():
    r = predict_from_features([3, 1.5, 0.2, 0.1, 60])
    assert r["level"] in LEVELS and 0 <= r["confidence"] <= 1
