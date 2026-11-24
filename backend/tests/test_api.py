import io
import os
import tempfile

import cv2
import numpy as np
from fastapi.testclient import TestClient

from app.dominance import model as m
from app.main import app

client = TestClient(app)


def _avi(n=20, size=96):
    path = os.path.join(tempfile.mkdtemp(), "v.avi")
    vw = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"MJPG"), 15, (size, size))
    rng = np.random.default_rng(0)
    for _ in range(n):
        vw.write(rng.integers(0, 255, (size, size, 3), dtype=np.uint8))
    vw.release()
    return open(path, "rb").read()


def _npz(key="pixel_array", frames=12, size=64):
    buf = io.BytesIO()
    np.savez(buf, **{key: np.random.default_rng(0).integers(0, 255, (frames, size, size), dtype=np.uint8)})
    return buf.getvalue()


def _upload(data: bytes, name="v.avi") -> str:
    return client.post("/uploads", files={"file": (name, io.BytesIO(data))}).json()["file_url"]


def _predict(videos):
    return client.post("/dominance/predict", json={"videos": videos})


class FakeSession:
    """ONNX stand-in. Returns logits [0, left_logit] so p_left = sigmoid(left_logit)."""

    def __init__(self, left_logit=2.0):
        self.left_logit, self.calls = left_logit, []

    def run(self, names, feed):
        f, v = feed["frames"], feed["views"]
        assert f.dtype == np.float32 and f.shape[0] == 1 and f.shape[2:] == (4, 3, 160, 160)
        assert v.dtype == np.int64 and v.shape == (1, f.shape[1])
        self.calls.append(v.copy())
        return [np.array([[0.0, self.left_logit]], dtype=np.float32)]


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_upload_empty_rejected():
    assert client.post("/uploads", files={"file": ("a.avi", io.BytesIO(b""))}).status_code == 400


def test_predict_without_weights_returns_fallback(monkeypatch):
    monkeypatch.setattr(m, "_model_available", lambda: False)
    monkeypatch.setattr(m, "_session", None)
    r = _predict([{"file_url": _upload(_avi()), "view": "RCA"}])
    assert r.status_code == 200 and "weights not found" in r.json()["summary"]


def test_non_media_rejected():
    r = _predict([{"file_url": _upload(b"just some text", "n.txt"), "view": "RCA"}])
    assert r.status_code == 422 and "detail" in r.json()


def test_unknown_view_rejected():
    r = _predict([{"file_url": _upload(_avi()), "view": "XYZ"}])
    assert r.status_code == 422


def test_empty_and_oversized_study_rejected():
    assert _predict([]).status_code == 422
    url = _upload(_avi())
    assert _predict([{"file_url": url, "view": "RCA"}] * 9).status_code == 422


def test_single_rca_view_reports_views_used(monkeypatch):
    monkeypatch.setattr(m, "_session", FakeSession(2.0))
    j = _predict([{"file_url": _upload(_avi()), "view": "RCA"}]).json()
    assert j["views_used"] == ["RCA"]
    assert j["dominance_type"] == "left"
    assert abs(j["p_left"] - 0.8808) < 1e-3 and abs(j["confidence"] - 0.8808) < 1e-3
    assert len(j["per_video"]) == 1 and j["per_video"][0]["view"] == "RCA"


def test_both_views_and_right_dominance(monkeypatch):
    fake = FakeSession(-3.0)
    monkeypatch.setattr(m, "_session", fake)
    vids = [{"file_url": _upload(_avi()), "view": "RCA"}, {"file_url": _upload(_avi(30)), "view": "LCA"}]
    j = _predict(vids).json()
    assert j["views_used"] == ["LCA", "RCA"] and j["dominance_type"] == "right"
    assert abs(j["confidence"] - 0.9526) < 1e-3
    assert len(j["per_video"]) == 2
    assert any(v.shape == (1, 2) and sorted(v[0].tolist()) == [0, 1] for v in fake.calls)  # combined study call


def test_npz_study_is_accepted(monkeypatch):
    monkeypatch.setattr(m, "_session", FakeSession(0.0))
    j = _predict([{"file_url": _upload(_npz(), "v.npz"), "view": "LCA"}]).json()
    assert j["views_used"] == ["LCA"] and j["p_left"] == 0.5


def test_npz_without_pixel_array_rejected(monkeypatch):
    monkeypatch.setattr(m, "_session", FakeSession())
    r = _predict([{"file_url": _upload(_npz(key="other"), "v.npz"), "view": "LCA"}])
    assert r.status_code == 422 and "pixel_array" in r.json()["detail"]


def test_single_image_is_accepted(monkeypatch):
    monkeypatch.setattr(m, "_session", FakeSession())
    png = cv2.imencode(".png", np.full((80, 80, 3), 90, np.uint8))[1].tobytes()
    assert _predict([{"file_url": _upload(png, "a.png"), "view": "RCA"}]).status_code == 200
