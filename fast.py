# from fastapi import FastAPI
# from pydantic import BaseModel
# from aggg import crew  # Import your existing agent
#
# app = FastAPI(title="Agent API")
#
# class QueryRequest(BaseModel):
#     query: str
#
# @app.get("/")
# def home():
#     return {"message": "Agent API is running"}
#
# @app.post("/api/query")
# def query_agent(request: QueryRequest):
#     """Simple endpoint that calls your existing agent"""
#     try:
#         # This calls YOUR existing agent code directly
#         result = crew.kickoff(inputs={"query": request.query})
#         return {"success": True, "result": result.raw}
#     except Exception as e:
#         return {"success": False, "error": str(e)}
#
# if __name__ == "__fast__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
#
#

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Import your agent
from aggg import crew

# Enhanced FastAPI app with CORS
app = FastAPI(
    title="TCM Agent API",
    description="Traditional Chinese Medicine AI Agent API with CrewAI integration.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",  # Your frontend
        "http://127.0.0.1:5000",  # Alternative localhost
        "https://borderlessagent-bor-agent.up.railway.app",  # Your backend itself
        # Add other domains as needed
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

class QueryRequest(BaseModel):
    query: str
    class Config:
        schema_extra = {
            "example": {
                "query": "bitter leaf"
            }
        }

class QueryResponse(BaseModel):
    success: bool
    result: str = None
    error: str = None

@app.get("/", tags=["Health Check"])
async def root():
    return {"message": "TCM Agent API is running", "version": "1.0.0"}

@app.post("/api/query", response_model=QueryResponse, tags=["TCM Agent"])
async def query_agent(request: QueryRequest):
    """
    Query the TCM AI Agent
    """
    try:
        result = crew.kickoff(inputs={"query": request.query})
        return QueryResponse(
            success=True,
            result=result.raw
        )
    except Exception as e:
        return QueryResponse(
            success=False,
            error=str(e)
        )

@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"status": "healthy", "service": "tcm-agent-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)