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
#         "https://borderlessagent-bor-agent.up.railway.app",  # Your backend itself
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

# In your fast.py - Fixed Version
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import re

app = FastAPI(
    title="TCM Agent API",
    description="Traditional Chinese Medicine AI Agent API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    raw_output: Optional[str] = None


def extract_and_map_json(agent_output: str) -> Dict[str, Any]:
    """
    Extract JSON from markdown and map to consistent structure
    """
    # Base structure that your frontend expects
    base_structure = {
        "specimen_description": {
            "botanical_name": "", "common_names": [], "part_used": "",
            "preparation_form": "", "morphology": ""
        },
        "key_compounds": [],
        "compound_distribution": {
            "Flavonoid": None, "Phenolic_acid": None,
            "Carotenoid": None, "Mineral": None
        },
        "toxicities_and_deficiencies": {
            "toxicities": [], "deficiencies": []
        },
        "complementary_botanicals": {
            "iron_deficiency_anemia": [], "enhanced_bioavailability": []
        },
        "treatable_ailments": [],
        "pharmaceutical_comparison": []
    }

    # Try multiple extraction methods
    extracted_json = None

    # Method 1: Direct JSON parse
    try:
        extracted_json = json.loads(agent_output)
    except:
        # Method 2: Extract from markdown code blocks
        try:
            # Look for ```json { ... } ``` pattern
            json_match = re.search(r'```json\s*(.*?)\s*```', agent_output, re.DOTALL)
            if json_match:
                extracted_json = json.loads(json_match.group(1))
            else:
                # Method 3: Look for any JSON object
                json_match = re.search(r'\{.*\}', agent_output, re.DOTALL)
                if json_match:
                    extracted_json = json.loads(json_match.group())
        except:
            extracted_json = None

    if not extracted_json:
        return base_structure

    # Map the extracted data to our consistent structure
    # Handle different JSON structures from the agent

    # If it's the botanical_analysis structure
    if 'botanical_analysis' in extracted_json:
        analysis = extracted_json['botanical_analysis']

        # Map to our structure
        if 'plant_name' in analysis:
            if 'botanical' in analysis['plant_name']:
                base_structure['specimen_description']['botanical_name'] = analysis['plant_name']['botanical']
            if 'common_names' in analysis['plant_name']:
                base_structure['specimen_description']['common_names'] = analysis['plant_name']['common_names']

        if 'morphology' in analysis and 'description' in analysis['morphology']:
            base_structure['specimen_description']['morphology'] = analysis['morphology']['description']

        if 'parts_used_and_preparation' in analysis:
            if 'parts_used' in analysis['parts_used_and_preparation']:
                base_structure['specimen_description']['part_used'] = ', '.join(
                    analysis['parts_used_and_preparation']['parts_used'])
            if 'preparation_methods' in analysis['parts_used_and_preparation']:
                base_structure['specimen_description']['preparation_form'] = ', '.join(
                    analysis['parts_used_and_preparation']['preparation_methods'])

        if 'key_chemical_compounds' in analysis:
            base_structure['key_compounds'] = [
                {"compound": compound, "class": "", "concentration_mg_g": None, "function": ""}
                for compound in analysis['key_chemical_compounds']
            ]

        if 'therapeutic_applications' in analysis and 'treatable_ailments' in analysis['therapeutic_applications']:
            base_structure['treatable_ailments'] = analysis['therapeutic_applications']['treatable_ailments']

        if 'safety_profile' in analysis:
            if 'potential_adverse_effects' in analysis['safety_profile']:
                base_structure['toxicities_and_deficiencies']['toxicities'] = analysis['safety_profile'][
                    'potential_adverse_effects']
            if 'deficiencies' in analysis['safety_profile']:
                base_structure['toxicities_and_deficiencies']['deficiencies'] = [
                    analysis['safety_profile']['deficiencies']] if analysis['safety_profile']['deficiencies'] else []

        if 'pharmaceutical_comparisons' in analysis and 'comparisons' in analysis['pharmaceutical_comparisons']:
            base_structure['pharmaceutical_comparison'] = [
                {"pharmaceutical": comp.get('compound', ''), "comparison": comp.get('comparable_properties', '')}
                for comp in analysis['pharmaceutical_comparisons']['comparisons']
            ]

        if 'complimentary_botanicals' in analysis:
            base_structure['complementary_botanicals']['enhanced_bioavailability'] = analysis[
                'complimentary_botanicals']

    return base_structure


@app.post("/api/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    try:
        from aggg import crew
        result = crew.kickoff(inputs={"query": request.query})

        # Extract and map the JSON to consistent structure
        consistent_data = extract_and_map_json(result.raw)

        return QueryResponse(
            success=True,
            data=consistent_data,
            raw_output=result.raw  # Keep original for debugging
        )

    except Exception as e:
        return QueryResponse(
            success=False,
            error=f"API Error: {str(e)}",
            raw_output=None
        )


@app.get("/")
async def root():
    return {"message": "TCM Agent API is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)