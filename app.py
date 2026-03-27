from fastapi import FastAPI
from fastapi.responses import FileResponse
from src.analysis.scanner import Scanner
from src.config.scanner_runtime import scanner_kwargs_from_env
import uvicorn
import asyncio

app = FastAPI()

TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "ADBE", "AMD",
    "7203.T", "6758.T", "9984.T", "6861.T", "8035.T", "6981.T", "6501.T", "6098.T", "9432.T", "8306.T",
    "7974.T", "4063.T", "6702.T", "6367.T", "6723.T", "9983.T", "7741.T", "4568.T", "6594.T", "6146.T"
]

# Global store for results
state = {"signals": []}

@app.on_event("startup")
async def startup_event():
    scanner = Scanner(TICKERS, **scanner_kwargs_from_env())
    results = scanner.scan()
    state["signals"] = results.to_dict(orient="records")

@app.get("/")
async def read_index():
    return FileResponse('index.html')

@app.get("/signals")
async def get_signals():
    return state["signals"]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
