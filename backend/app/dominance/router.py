from typing import List, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .model import predict

router = APIRouter(prefix="/dominance", tags=["dominance"])


class VideoItem(BaseModel):
    file_url: str
    view: Literal["RCA", "LCA"]


class PredictRequest(BaseModel):
    videos: List[VideoItem] = Field(..., min_length=1, max_length=8, description="One study: its RCA and/or LCA runs")


@router.post("/predict")
def predict_dominance(req: PredictRequest):
    return predict([(v.file_url, v.view) for v in req.videos])
