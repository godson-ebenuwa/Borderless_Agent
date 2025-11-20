
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from typing import Optional, Dict, Any
# import os
# from dotenv import load_dotenv
# import json
#
# # Load environment variables first
# load_dotenv()
#
# # Import your agent
# from aggg import crew
#
# # Enhanced FastAPI app with CORS
# app = FastAPI(
#     title="Borderless Agent API",
#     description="Traditional Chinese Medicine AI Agent API with CrewAI integration.",
#     version="1.0.0",
#     docs_url="/docs",
#     redoc_url="/redoc",
# )
#
# # Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "http://localhost:5000",  # Your frontend
#         "http://127.0.0.1:5000",  # Alternative localhost
#         "https://borderlessagent-bor-agent.up.railway.app",
#         "https://borderless-sciences-hackaton.vercel.app/", # Your backend itself
#     ],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
#
#
# class QueryRequest(BaseModel):
#     query: str
#
#     class Config:
#         schema_extra = {
#             "example": {
#                 "query": "bitter leaf"
#             }
#         }
#
#
# class QueryResponse(BaseModel):
#     success: bool
#     result: Optional[Dict[str, Any]] = None
#     error: Optional[str] = None
#
#
# def parse_agent_response(raw_response: str) -> Dict[str, Any]:
#     """
#     Parse the agent's raw response into structured JSON
#     """
#     try:
#         # Try to parse as JSON directly
#         return json.loads(raw_response)
#     except json.JSONDecodeError:
#         # If it's not valid JSON, try to extract JSON from the response
#         try:
#             # Look for JSON pattern in the response
#             start_idx = raw_response.find('{')
#             end_idx = raw_response.rfind('}') + 1
#             if start_idx != -1 and end_idx != 0:
#                 json_str = raw_response[start_idx:end_idx]
#                 return json.loads(json_str)
#             else:
#                 # If no JSON found, return the raw text as a message
#                 return {
#                     "message": raw_response,
#                     "raw_output": raw_response
#                 }
#         except:
#             # If all parsing fails, return the raw text
#             return {
#                 "message": raw_response,
#                 "raw_output": raw_response
#             }
#
#
# @app.get("/", tags=["Health Check"])
# async def root():
#     return {"message": "TCM Agent API is running", "version": "1.0.0"}
#
#
# @app.post("/api/query", response_model=QueryResponse, tags=["TCM Agent"])
# async def query_agent(request: QueryRequest):
#     """
#     Query the TCM AI Agent
#     """
#     try:
#         # Get the raw result from your agent
#         result = crew.kickoff(inputs={"query": request.query})
#
#         # Parse the response into structured JSON
#         parsed_result = parse_agent_response(result.raw)
#
#         return QueryResponse(
#             success=True,
#             result=parsed_result
#         )
#     except Exception as e:
#         return QueryResponse(
#             success=False,
#             error=str(e)
#         )
#
#
# @app.get("/health", tags=["Health Check"])
# async def health_check():
#     return {"status": "healthy", "service": "tcm-agent-api"}
#
#
# if __name__ == "__main__":
#     import uvicorn
#
#     uvicorn.run(app, host="0.0.0.0", port=8000)

# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from typing import Optional, Dict, Any
# import os
# from dotenv import load_dotenv
# import json
# import time
# import asyncio
# from httpx import AsyncClient, Timeout, Limits
# import httpx
#
# # Load environment variables first
# load_dotenv()
#
# # Import your agent
# from aggg import crew
#
# # Enhanced FastAPI app with CORS
# app = FastAPI(
#     title="TCM Agent API",
#     description="Traditional Chinese Medicine AI Agent API with CrewAI integration.",
#     version="1.0.0",
#     docs_url="/docs",
#     redoc_url="/redoc",
# )
#
# # Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "http://localhost:5000",  # Your frontend
#         "http://127.0.0.1:5000",  # Alternative localhost
#         "https://borderlessagent-bor-agent.up.railway.app",
#         "https://borderless-sciences-hackaton.vercel.app/",# Your backend itself
#     ],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
#
#
# class QueryRequest(BaseModel):
#     query: str
#
#     class Config:
#         schema_extra = {
#             "example": {
#                 "query": "bitter leaf"
#             }
#         }
#
#
# class QueryResponse(BaseModel):
#     success: bool
#     result: Optional[Dict[str, Any]] = None
#     error: Optional[str] = None
#
#
# # Retry configuration for rate limiting
# class RetryConfig:
#     def __init__(self):
#         self.max_attempts = 5
#         self.base_delay = 1  # seconds
#         self.max_delay = 60  # seconds
#         self.retry_status_codes = [429, 500, 502, 503, 504]
#
#     async def execute_with_retry(self, func, *args, **kwargs):
#         """
#         Execute a function with exponential backoff retry logic
#         """
#         last_exception = None
#
#         for attempt in range(self.max_attempts):
#             try:
#                 return await func(*args, **kwargs)
#             except Exception as e:
#                 last_exception = e
#
#                 # Check if we should retry based on exception type
#                 if not self._should_retry(e):
#                     raise e
#
#                 # Calculate delay with exponential backoff
#                 delay = min(self.base_delay * (2 ** attempt), self.max_delay)
#
#                 # Add jitter to avoid thundering herd
#                 jitter = delay * 0.1  # 10% jitter
#                 delay_with_jitter = delay + (jitter * (0.5 - (os.urandom(1)[0] / 255.0)))
#
#                 print(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay_with_jitter:.2f}s")
#
#                 # Wait before retry
#                 await asyncio.sleep(delay_with_jitter)
#
#         # If all attempts failed, raise the last exception
#         raise last_exception
#
#     def _should_retry(self, exception):
#         """
#         Determine if an exception should trigger a retry
#         """
#         error_str = str(exception).lower()
#
#         # Retry on rate limiting
#         if "rate limit" in error_str or "quota" in error_str or "429" in error_str:
#             return True
#
#         # Retry on connection issues
#         if "timeout" in error_str or "connection" in error_str:
#             return True
#
#         # Retry on server errors
#         if any(str(code) in error_str for code in self.retry_status_codes):
#             return True
#
#         return False
#
#
# # Initialize retry config
# retry_config = RetryConfig()
#
#
# def parse_agent_response(raw_response: str) -> Dict[str, Any]:
#     """
#     Parse the agent's raw response into structured JSON
#     """
#     try:
#         # Try to parse as JSON directly
#         return json.loads(raw_response)
#     except json.JSONDecodeError:
#         # If it's not valid JSON, try to extract JSON from the response
#         try:
#             # Look for JSON pattern in the response
#             start_idx = raw_response.find('{')
#             end_idx = raw_response.rfind('}') + 1
#             if start_idx != -1 and end_idx != 0:
#                 json_str = raw_response[start_idx:end_idx]
#                 return json.loads(json_str)
#             else:
#                 # If no JSON found, return the raw text as a message
#                 return {
#                     "message": raw_response,
#                     "raw_output": raw_response
#                 }
#         except:
#             # If all parsing fails, return the raw text
#             return {
#                 "message": raw_response,
#                 "raw_output": raw_response
#             }
#
#
# async def execute_agent_query(query: str) -> str:
#     """
#     Execute agent query with built-in error handling
#     """
#     try:
#         result = crew.kickoff(inputs={"query": query})
#         return result.raw
#     except Exception as e:
#         raise e
#
#
# @app.get("/", tags=["Health Check"])
# async def root():
#     return {"message": "TCM Agent API is running", "version": "1.0.0"}
#
#
# @app.post("/api/query", response_model=QueryResponse, tags=["TCM Agent"])
# async def query_agent(request: QueryRequest):
#     """
#     Query the TCM AI Agent with automatic retry on rate limiting
#     """
#     try:
#         # Execute with retry logic
#         raw_result = await retry_config.execute_with_retry(
#             execute_agent_query,
#             request.query
#         )
#
#         # Parse the response into structured JSON
#         parsed_result = parse_agent_response(raw_result)
#
#         return QueryResponse(
#             success=True,
#             result=parsed_result
#         )
#
#     except Exception as e:
#         error_msg = str(e)
#
#         # Provide more user-friendly error messages
#         if "rate limit" in error_msg.lower() or "429" in error_msg:
#             error_msg = "API rate limit exceeded. Please try again in a few moments."
#         elif "quota" in error_msg.lower():
#             error_msg = "API quota exceeded. Please check your API key limits."
#         elif "timeout" in error_msg.lower():
#             error_msg = "Request timed out. Please try again."
#
#         return QueryResponse(
#             success=False,
#             error=error_msg
#         )
#
#
# @app.get("/health", tags=["Health Check"])
# async def health_check():
#     return {"status": "healthy", "service": "tcm-agent-api"}
#
#
# # Rate limiting middleware (optional)
# from slowapi import Limiter, _rate_limit_exceeded_handler
# from slowapi.util import get_remote_address
# from slowapi.errors import RateLimitExceeded
#
# # Optional: Add rate limiting for your API endpoints
# limiter = Limiter(key_func=get_remote_address)
# app.state.limiter = limiter
# app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
#
#
# @app.get("/api/status")
# @limiter.limit("10/minute")  # Limit to 10 requests per minute
# async def api_status(request):
#     """
#     Check API status with rate limiting
#     """
#     return {
#         "status": "operational",
#         "timestamp": time.time(),
#         "retry_config": {
#             "max_attempts": retry_config.max_attempts,
#             "base_delay": retry_config.base_delay,
#             "max_delay": retry_config.max_delay
#         }
#     }
#
#
# if __name__ == "__main__":
#     import uvicorn
#
#     uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import os
import json
import time
import asyncio
import hashlib
from collections import deque

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
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "https://borderlessagent-bor-agent.up.railway.app",
        "https://borderless-sciences-hackaton.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Request Throttling
class RequestThrottler:
    def __init__(self, max_requests: int = 2, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()

    async def wait_if_needed(self):
        now = time.time()
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()

        if len(self.requests) >= self.max_requests:
            oldest_request = self.requests[0]
            wait_time = (oldest_request + self.time_window) - now
            if wait_time > 0:
                print(f"Rate limit: Waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)

        self.requests.append(now)


# Simple Cache
class SimpleCache:
    def __init__(self, max_size: int = 50):
        self.cache: Dict[str, str] = {}
        self.max_size = max_size

    def get_key(self, query: str) -> str:
        return hashlib.md5(query.encode()).hexdigest()

    def get(self, query: str) -> Optional[str]:
        return self.cache.get(self.get_key(query))

    def set(self, query: str, result: str):
        key = self.get_key(query)
        if len(self.cache) >= self.max_size:
            first_key = next(iter(self.cache))
            del self.cache[first_key]
        self.cache[key] = result


# Initialize
throttler = RequestThrottler(max_requests=2, time_window=60)
cache = SimpleCache()


def parse_agent_response(raw_response: str) -> Dict[str, Any]:
    try:
        return json.loads(raw_response)
    except json.JSONDecodeError:
        try:
            start_idx = raw_response.find('{')
            end_idx = raw_response.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = raw_response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return {"message": raw_response, "raw_output": raw_response}
        except:
            return {"message": raw_response, "raw_output": raw_response}


async def execute_agent_query(query: str) -> str:
    try:
        # Check cache first
        cached_result = cache.get(query)
        if cached_result:
            print("Returning cached result")
            return cached_result

        # Throttle requests
        await throttler.wait_if_needed()

        result = crew.kickoff(inputs={"query": query})

        # Cache successful result
        cache.set(query, result.raw)

        return result.raw
    except Exception as e:
        raise e


@app.get("/")
async def root():
    return {"message": "TCM Agent API is running", "version": "1.0.0"}


@app.post("/api/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    try:
        raw_result = await execute_agent_query(request.query)
        parsed_result = parse_agent_response(raw_result)
        return QueryResponse(success=True, result=parsed_result)
    except Exception as e:
        error_msg = str(e)
        if "rate limit" in error_msg.lower() or "429" in error_msg:
            error_msg = "API rate limit exceeded. Please try again in a few minutes."
        return QueryResponse(success=False, error=error_msg)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "tcm-agent-api"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)