from contextlib import asynccontextmanager
from pathlib import Path
import os
import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field

class Transaction(BaseModel):
    item_description: str = Field(min_length=1, max_length=2000)
    amount: float = Field(ge=0, le=1_000_000_000)
    product_category: str = Field(min_length=1, max_length=100)
    destination_state: str = Field(min_length=2, max_length=2)
    exemption_certificate: str = Field(min_length=1, max_length=100)
    customer_type: str = Field(min_length=1, max_length=100)

@asynccontextmanager
async def lifespan(application):
    # Load only the trusted artifact built with this reviewed application image.
    application.state.model = joblib.load(Path(os.getenv('MODEL_PATH', 'models/model.joblib')))
    yield

app = FastAPI(title='AI application', lifespan=lifespan)

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.post('/predict')
def predict(transaction: Transaction):
    frame = pd.DataFrame([transaction.model_dump()])
    return {'prediction': str(app.state.model.predict(frame)[0]), 'demo': True}
