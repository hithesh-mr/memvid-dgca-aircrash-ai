#!/usr/bin/env python3
"""
FastAPI server to serve the client and provide a search API endpoint.
"""
import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from server.search import search

class SearchRequest(BaseModel):
    query: str
    provider: Optional[str] = "openai"
    model: Optional[str] = None

app = FastAPI(title="MemVid File Chat Server")

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

# Static files (CSS/JS) served under /static
client_dir = os.path.join(os.path.dirname(__file__), '..', 'client')
app.mount("/static", StaticFiles(directory=client_dir), name="static")

# Serve index.html at root
@app.get("/")
async def serve_index():
    index_path = os.path.join(client_dir, "index.html")
    return FileResponse(index_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=5000, reload=True)