#!/usr/bin/env python3
"""
FastAPI server to serve the client and provide a search API endpoint.
"""
import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .search import search

class SearchRequest(BaseModel):
    query: str
    provider: Optional[str] = "openai"
    model: Optional[str] = None

app = FastAPI(title="MemVid Search API")

# Enable CORS for all origins (adjust as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API endpoint for search
@app.post("/api/search")
async def api_search(request: SearchRequest):
    try:
        answer = search(request.query, provider=request.provider, model=request.model)
        return {"answer": answer}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

# Simple root endpoint
@app.get("/")
async def read_root():
    return JSONResponse(content={"message": "MemVid Search API is running"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=5000, reload=True)