import io
import os
import tempfile

import cv2
import numpy as np

from ..common import InvalidInput, fetch_bytes

WEIGHTS_DIR = os.path.join(os.path.dirname(__file__), "weights")
MODEL_PATH = os.path.join(WEIGHTS_DIR, "dominance_model.onnx")

SIZE = 160          # network input resolution
CACHE_SIZE = 192    # frames are first reduced to this, as during training
NFRAMES = 8         # evenly spaced frames kept per video
FRAMES_PER_VIDEO = 4
MEAN, STD = 0.449, 0.226
VIEW_ID = {"RCA": 0, "LCA": 1}

_session = None


def _model_available() -> bool:
    return os.path.exists(MODEL_PATH)


def load_model():
    global _session
    if _session is None and _model_available():
        import onnxruntime as ort

        _session = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
    return _session


def _gray_stack_from_video(raw: bytes) -> np.ndarray:
    fd, path = tempfile.mkstemp(suffix=".avi")
    with os.fdopen(fd, "wb") as f:
        f.write(raw)
    cap, frames = cv2.VideoCapture(path), []
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
    finally:
        cap.release()
        os.remove(path)
    return np.stack(frames) if frames else None


def load_frames(raw: bytes) -> np.ndarray:
    """npz (key pixel_array), video, or a single image -> (NFRAMES, CACHE_SIZE, CACHE_SIZE) uint8."""
    if raw[:4] == b"PK\x03\x04":  # npz is a zip archive
        try:
            z = np.load(io.BytesIO(raw), allow_pickle=False)
            if "pixel_array" not in z.files:
                raise KeyError
            arr = z["pixel_array"]
        except KeyError:
            raise InvalidInput("The .npz file must contain an array named 'pixel_array' (frames, height, width).")
        except Exception:
            raise InvalidInput("Could not read the .npz file.")
        if arr.ndim == 4:
            arr = arr[..., 0]
        if arr.ndim != 3 or arr.shape[0] < 1:
            raise InvalidInput("'pixel_array' must have shape (frames, height, width).")
        arr = arr.astype(np.uint8)
    else:
        arr = _gray_stack_from_video(raw)
        if arr is None:
            img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
            if img is None:
                raise InvalidInput("Each file must be an angiogram video (MP4/AVI), an .npz study, or an image.")
            arr = img[None]
    idx = np.linspace(0, arr.shape[0] - 1, NFRAMES).round().astype(int)
    return np.stack([cv2.resize(arr[i], (CACHE_SIZE, CACHE_SIZE), interpolation=cv2.INTER_AREA) for i in idx])


def _clip(frames: np.ndarray) -> np.ndarray:
    sel = np.linspace(0, frames.shape[0] - 1, FRAMES_PER_VIDEO).round().astype(int)
    small = np.stack([cv2.resize(f, (SIZE, SIZE), interpolation=cv2.INTER_AREA) for f in frames[sel]])
    x = (small.astype(np.float32) / 255.0 - MEAN) / STD
    return np.repeat(x[:, None], 3, axis=1)  # (F, 3, H, W)


def _p_left(clips: list, views: list) -> float:
    logits = _session.run(
        ["logits"],
        {"frames": np.stack(clips)[None].astype(np.float32), "views": np.array([views], dtype=np.int64)},
    )[0][0]
    e = np.exp(logits - logits.max())
    return float((e / e.sum())[1])


def predict(videos: list) -> dict:
    """videos: [(file_url, 'RCA'|'LCA'), ...]"""
    frames = [(load_frames(fetch_bytes(url)), view.upper()) for url, view in videos]
    load_model()
    if _session is None:
        return {
            "dominance_type": "unknown", "confidence": 0.0, "views_used": [], "per_video": [],
            "summary": "Coronary dominance model weights not found, so training has not been completed.",
        }

    clips = [_clip(f) for f, _ in frames]
    views = [VIEW_ID[v] for _, v in frames]
    p_left = _p_left(clips, views)
    per_video = [{"view": v, "p_left": round(_p_left([c], [VIEW_ID[v]]), 4)} for c, (_, v) in zip(clips, frames)]
    dominance = "left" if p_left > 0.5 else "right"
    confidence = round(max(p_left, 1 - p_left), 4)
    return {
        "dominance_type": dominance,
        "confidence": confidence,
        "p_left": round(p_left, 4),
        "views_used": sorted({v for _, v in frames}),
        "per_video": per_video,
        "summary": f"{dominance.capitalize()}-dominant coronary circulation predicted ({confidence * 100:.0f}% model confidence).",
    }
