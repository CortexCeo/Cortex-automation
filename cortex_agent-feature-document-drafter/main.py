from pathlib import Path
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from api.api_router import api_router
import uvicorn
from utils.logger_config import service_logger as logger

app = FastAPI(
    title="Cortex",
    description="Knowledge workers second brain",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(api_router, prefix="/api", tags=["API"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Cortex",
        "status": "operational"
    }

if __name__ == "__main__":
    logger.info("Starting the application...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=9000,
        reload=False,
        workers=4
    )