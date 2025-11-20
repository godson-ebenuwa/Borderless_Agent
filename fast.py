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
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv
import json

# Load environment variables first
load_dotenv()

# Import your agent
from aggg import crew

# Enhanced FastAPI app with CORS
app = FastAPI(
    title="Borderless Agent API",
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
        "https://borderlessagent-bor-agent.up.railway.app",
        "https://borderless-sciences-hackaton.vercel.app/", # Your backend itself
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


def parse_agent_response(raw_response: str) -> Dict[str, Any]:
    """
    Parse the agent's raw response into structured JSON
    """
    try:
        # Try to parse as JSON directly
        return json.loads(raw_response)
    except json.JSONDecodeError:
        # If it's not valid JSON, try to extract JSON from the response
        try:
            # Look for JSON pattern in the response
            start_idx = raw_response.find('{')
            end_idx = raw_response.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = raw_response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # If no JSON found, return the raw text as a message
                return {
                    "message": raw_response,
                    "raw_output": raw_response
                }
        except:
            # If all parsing fails, return the raw text
            return {
                "message": raw_response,
                "raw_output": raw_response
            }


@app.get("/", tags=["Health Check"])
async def root():
    return {"message": "TCM Agent API is running", "version": "1.0.0"}


@app.post("/api/query", response_model=QueryResponse, tags=["TCM Agent"])
async def query_agent(request: QueryRequest):
    """
    Query the TCM AI Agent
    """
    try:
        # Get the raw result from your agent
        result = crew.kickoff(inputs={"query": request.query})

        # Parse the response into structured JSON
        parsed_result = parse_agent_response(result.raw)

        return QueryResponse(
            success=True,
            result=parsed_result
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