"""
Минимальная версия VLM Server для диагностики
"""

import uvicorn
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"status": "ok", "message": "VLM Server is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    print("Starting minimal VLM Server on http://localhost:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False,
                log_level="info")  # Только localhost  # Без reload
