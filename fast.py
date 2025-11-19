from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv
import json
import re

# Load environment variables first
load_dotenv()

# Import your agent
from aggg import crew

app = FastAPI(
    title="TCM Agent API",
    description="Traditional Chinese Medicine AI Agent API with CrewAI integration.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str


class TCMResponse(BaseModel):
    specimen_description: Dict[str, Any]
    key_compounds: List[Dict[str, Any]]
    compound_distribution: Dict[str, Any]
    toxicities_and_deficiencies: Dict[str, List[str]]
    complementary_botanicals: Dict[str, List[str]]
    treatable_ailments: List[str]
    pharmaceutical_comparison: List[Dict[str, str]]


class QueryResponse(BaseModel):
    success: bool
    data: Optional[TCMResponse] = None
    error: Optional[str] = None
    raw_output: Optional[str] = None


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON from text, even if it's wrapped in other content
    """
    try:
        # Try direct JSON parse first
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON pattern in the text
        json_pattern = r'\{.*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)

        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

        return None


def create_consistent_structure(parsed_data: Dict[str, Any]) -> TCMResponse:
    """
    Ensure the response always has the same structure
    """
    # Default structure
    default_structure = {
        "specimen_description": {
            "botanical_name": "",
            "common_names": [],
            "part_used": "",
            "preparation_form": "",
            "morphology": ""
        },
        "key_compounds": [],
        "compound_distribution": {
            "Flavonoid": None,
            "Phenolic_acid": None,
            "Carotenoid": None,
            "Mineral": None
        },
        "toxicities_and_deficiencies": {
            "toxicities": [],
            "deficiencies": []
        },
        "complementary_botanicals": {
            "iron_deficiency_anemia": [],
            "enhanced_bioavailability": []
        },
        "treatable_ailments": [],
        "pharmaceutical_comparison": []
    }

    # Merge parsed data with default structure
    def deep_merge(default, new):
        result = default.copy()
        for key, value in new.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                elif isinstance(result[key], list) and isinstance(value, list):
                    result[key] = value  # Replace lists
                else:
                    result[key] = value
        return result

    merged_data = deep_merge(default_structure, parsed_data)
    return TCMResponse(**merged_data)


@app.post("/api/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    """
    Query the TCM AI Agent with consistent JSON output
    """
    try:
        # Get the raw result from your agent
        result = crew.kickoff(inputs={"query": request.query})

        # Extract and parse JSON
        parsed_data = extract_json_from_text(result.raw)

        if parsed_data:
            # Create consistent structure
            consistent_data = create_consistent_structure(parsed_data)

            return QueryResponse(
                success=True,
                data=consistent_data,
                raw_output=result.raw  # Keep original for debugging
            )
        else:
            return QueryResponse(
                success=False,
                error="Agent did not return valid JSON format",
                raw_output=result.raw
            )

    except Exception as e:
        return QueryResponse(
            success=False,
            error=f"API Error: {str(e)}"
        )


@app.get("/")
async def root():
    return {"message": "TCM Agent API is running", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "tcm-agent-api"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)