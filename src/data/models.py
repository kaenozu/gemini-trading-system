from pydantic import BaseModel, field_validator
import pandas as pd

class OHLCVModel(BaseModel):
    Open: float
    High: float
    Low: float
    Close: float
    Volume: float

    @field_validator('Open', 'High', 'Low', 'Close', 'Volume')
    def check_non_negative(cls, v):
        if v < 0:
            raise ValueError("Value must be non-negative")
        return v
