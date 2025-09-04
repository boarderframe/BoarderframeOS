#!/usr/bin/env python3
"""
Simple function server for testing Open WebUI integration
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Simple Function Server",
    description="Test functions for Open WebUI",
    version="1.0.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HelloRequest(BaseModel):
    name: str = "World"

@app.post("/hello")
async def hello_function(request: HelloRequest) -> str:
    """Say hello to someone."""
    return f"Hello, {request.name}!"

@app.post("/add")
async def add_numbers(a: int, b: int) -> str:
    """Add two numbers together."""
    result = a + b
    return f"The sum of {a} and {b} is {result}"

@app.get("/")
async def root():
    return {"message": "Simple Function Server is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)