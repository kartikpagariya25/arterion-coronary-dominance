from typing import List, Literal

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field

from ..accounts.deps import optional_user
from ..accounts.history import record_analysis
from .model import predict

router = APIRouter(prefix="/dominance", tags=["dominance"])


class VideoItem(BaseModel):
    file_url: str
    view: Literal["RCA", "LCA"]


class PredictRequest(BaseModel):
    videos: List[VideoItem] = Field(..., min_length=1, max_length=8, description="One study: its RCA and/or LCA runs")


@router.post("/predict")
def predict_dominance(req: PredictRequest, response: Response, user=Depends(optional_user)):
    result = predict([(v.file_url, v.view) for v in req.videos])
    record_analysis(user, "dominance", [v.file_url for v in req.videos], result, response)
    return result
