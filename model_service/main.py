"""
STUB: Grocery Vision Service (FastAPI)
======================================
This is the stub implementation of the CNN-based grocery image processing service.

TO INTEGRATE THE REAL MODEL:
  - Replace the body of the `predict()` function below.
  - The FastAPI interface, PredictRequest/PredictResponse schema, and /predict endpoint stay identical.
  - Add your model dependencies to requirements.txt (e.g. torch, torchvision, tensorflow).
  - Load the model at startup using a lifespan event (example commented out below).
"""

import asyncio
from fastapi import FastAPI
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Uncomment and adapt when integrating the real CNN model:
# ---------------------------------------------------------------------------
# from contextlib import asynccontextmanager
# import torch
#
# model = None
#
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     global model
#     model = torch.load("model_weights.pt")
#     model.eval()
#     yield
#     model = None
#
# app = FastAPI(title="Grocery Vision Service", lifespan=lifespan)
# ---------------------------------------------------------------------------

app = FastAPI(title="Grocery Vision Service (Stub)")


# ── Request / Response Schemas ──────────────────────────────────────────────

class PredictRequest(BaseModel):
    image_paths: list[str]  # absolute paths inside the shared /app/media volume


class ItemResult(BaseModel):
    product_name: str
    quantity: float
    unit_price: float
    remark: str = ""


class PredictResponse(BaseModel):
    remarks: str
    items: list[ItemResult]


# ── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Health check — used by Docker Compose healthcheck."""
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
async def predict(req: PredictRequest):
    """
    Process grocery images and return an itemized bill.

    STUB IMPLEMENTATION — replace the body below with real CNN inference.
    The function signature, request model, and response model must not change.
    """
    # --- STUB: simulated 2-second processing delay ---
    await asyncio.sleep(2)

    return PredictResponse(
        remarks="Please check dairy products — expiry date not clearly visible.",
        items=[
            ItemResult(product_name="Whole Milk 1L",  quantity=2.0, unit_price=55.0,  remark="check expiry"),
            ItemResult(product_name="Brown Bread",    quantity=1.0, unit_price=40.0,  remark=""),
            ItemResult(product_name="Eggs (12 pack)", quantity=1.0, unit_price=90.0,  remark=""),
            ItemResult(product_name="Butter 500g",    quantity=1.0, unit_price=120.0, remark="check expiry"),
        ]
    )
    # --- END STUB ---
