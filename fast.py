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

# In your fast.py - Ultimate Parser Version
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


def smart_json_extractor(agent_output: str) -> Dict[str, Any]:
    """
    Extract JSON from any format and normalize field names
    """
    extracted_data = {}

    # Try multiple extraction methods
    try:
        # Method 1: Direct JSON parse
        extracted_data = json.loads(agent_output)
    except:
        try:
            # Method 2: Extract from markdown code blocks
            json_match = re.search(r'```json\s*(.*?)\s*```', agent_output, re.DOTALL)
            if json_match:
                extracted_data = json.loads(json_match.group(1))
            else:
                # Method 3: Look for any JSON object
                json_match = re.search(r'\{.*\}', agent_output, re.DOTALL)
                if json_match:
                    extracted_data = json.loads(json_match.group())
        except:
            # If all parsing fails, return empty
            return {}

    return extracted_data


def normalize_to_consistent_structure(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map ANY agent output structure to our consistent format
    """
    # Base structure
    consistent_structure = {
        "specimen_description": {
            "botanical_name": "",
            "common_names": [],
            "part_used": "",
            "preparation_form": "",
            "morphology": ""
        },
        "key_compounds": [],
        "compound_distribution": {
            "Flavonoid": None, "Phenolic_acid": None,
            "Carotenoid": None, "Mineral": None
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

    # Field mapping dictionary - maps any field name to our standard names
    field_mappings = {
        # Botanical name mappings
        "botanical_name": ["botanicalName", "scientific_name", "botanical_name", "botanicalName", "plant_name"],
        "common_names": ["commonNames", "common_names", "synonyms"],
        "part_used": ["partUsed", "part_used", "parts_used", "harvestedPart"],
        "preparation_form": ["preparationForm", "preparation_forms", "preparation_form", "processing"],
        "morphology": ["morphology", "plant_description", "description", "morphological_description"],

        # Key compounds mappings
        "key_compounds": ["keyCompounds", "key_compounds", "chemical_compounds", "chemical_composition",
                          "key_chemical_compounds"],

        # Treatable ailments mappings
        "treatable_ailments": ["treatableAilments", "treatable_ailments", "therapeutic_applications", "applications"],

        # Toxicities mappings
        "toxicities": ["toxicities", "potential_adverse_effects", "side_effects", "safety_profile"],
        "deficiencies": ["deficiencies", "contraindications"],

        # Complementary botanicals mappings
        "complementary_botanicals": ["complimentaryBotanicals", "complimentary_botanicals", "synergistic_combinations",
                                     "synergistic_use"],

        # Pharmaceutical comparison mappings
        "pharmaceutical_comparison": ["pharmaceuticalComparisons", "pharmaceutical_comparisons",
                                      "pharmaceutical_context"]
    }

    def extract_value(data, possible_keys):
        """Extract value using any of the possible keys"""
        for key in possible_keys:
            if key in data:
                return data[key]
        return None

    def extract_nested_value(data, path):
        """Extract value from nested structure"""
        current = data
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current

    # Map botanical description
    botanical_name = (extract_value(extracted_data, field_mappings["botanical_name"]) or
                      extract_nested_value(extracted_data, ["botanical_identification", "botanical_name"]) or
                      extract_nested_value(extracted_data, ["botanicalInformation", "botanicalName"]))

    if botanical_name:
        consistent_structure["specimen_description"]["botanical_name"] = botanical_name

    # Map common names
    common_names = (extract_value(extracted_data, field_mappings["common_names"]) or
                    extract_nested_value(extracted_data, ["botanical_identification", "common_names"]) or
                    extract_nested_value(extracted_data, ["botanicalInformation", "commonNames"]))

    if common_names:
        consistent_structure["specimen_description"]["common_names"] = common_names

    # Map parts used
    part_used = (extract_value(extracted_data, field_mappings["part_used"]) or
                 extract_nested_value(extracted_data, ["plant_utilization", "parts_used"]) or
                 extract_nested_value(extracted_data, ["botanicalInformation", "harvestedPart"]))

    if part_used:
        if isinstance(part_used, list):
            consistent_structure["specimen_description"]["part_used"] = ", ".join(part_used)
        else:
            consistent_structure["specimen_description"]["part_used"] = str(part_used)

    # Map preparation forms
    prep_form = (extract_value(extracted_data, field_mappings["preparation_form"]) or
                 extract_nested_value(extracted_data, ["plant_utilization", "preparation_forms"]) or
                 extract_nested_value(extracted_data, ["botanicalInformation", "processing"]))

    if prep_form:
        if isinstance(prep_form, list):
            consistent_structure["specimen_description"]["preparation_form"] = ", ".join(prep_form)
        else:
            consistent_structure["specimen_description"]["preparation_form"] = str(prep_form)

    # Map morphology
    morphology = (extract_value(extracted_data, field_mappings["morphology"]) or
                  extract_nested_value(extracted_data, ["morphological_description"]) or
                  extract_nested_value(extracted_data, ["botanicalInformation", "morphology"]))

    if morphology and isinstance(morphology, dict):
        # Handle nested morphology objects
        morphology_text = []
        for key, value in morphology.items():
            if isinstance(value, (str, int, float)):
                morphology_text.append(f"{key}: {value}")
            elif isinstance(value, dict):
                for subkey, subvalue in value.items():
                    morphology_text.append(f"{key}.{subkey}: {subvalue}")
        consistent_structure["specimen_description"]["morphology"] = "; ".join(morphology_text)
    elif morphology:
        consistent_structure["specimen_description"]["morphology"] = str(morphology)

    # Map key compounds
    compounds_data = extract_value(extracted_data, field_mappings["key_compounds"])
    if compounds_data:
        if isinstance(compounds_data, list):
            for compound in compounds_data:
                if isinstance(compound, str):
                    consistent_structure["key_compounds"].append({
                        "compound": compound,
                        "class": "",
                        "concentration_mg_g": None,
                        "function": ""
                    })
                elif isinstance(compound, dict):
                    consistent_structure["key_compounds"].append({
                        "compound": compound.get("name", compound.get("compound", "")),
                        "class": compound.get("class", ""),
                        "concentration_mg_g": compound.get("concentration_mg_g", None),
                        "function": compound.get("description", compound.get("function", ""))
                    })

    # Map treatable ailments
    ailments_data = extract_value(extracted_data, field_mappings["treatable_ailments"])
    if ailments_data:
        if isinstance(ailments_data, list):
            consistent_structure["treatable_ailments"] = ailments_data
        elif isinstance(ailments_data, dict) and "treatable_ailments" in ailments_data:
            consistent_structure["treatable_ailments"] = ailments_data["treatable_ailments"]

    # Map toxicities
    toxicities_data = extract_value(extracted_data, field_mappings["toxicities"])
    if toxicities_data:
        if isinstance(toxicities_data, list):
            consistent_structure["toxicities_and_deficiencies"]["toxicities"] = toxicities_data
        elif isinstance(toxicities_data, dict):
            if "toxicities" in toxicities_data:
                consistent_structure["toxicities_and_deficiencies"]["toxicities"] = toxicities_data["toxicities"]

    # Map complementary botanicals
    botanicals_data = extract_value(extracted_data, field_mappings["complementary_botanicals"])
    if botanicals_data:
        if isinstance(botanicals_data, list):
            consistent_structure["complementary_botanicals"]["enhanced_bioavailability"] = botanicals_data

    # Map pharmaceutical comparisons
    pharma_data = extract_value(extracted_data, field_mappings["pharmaceutical_comparison"])
    if pharma_data:
        if isinstance(pharma_data, list):
            for item in pharma_data:
                if isinstance(item, dict):
                    consistent_structure["pharmaceutical_comparison"].append({
                        "pharmaceutical": item.get("compound", item.get("pharmaceutical", "")),
                        "comparison": item.get("description", item.get("comparison", ""))
                    })

    return consistent_structure


@app.post("/api/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    try:
        from aggg import crew
        result = crew.kickoff(inputs={"query": request.query})

        # Extract JSON from agent output
        extracted_data = smart_json_extractor(result.raw)

        # Normalize to consistent structure
        consistent_data = normalize_to_consistent_structure(extracted_data)

        return QueryResponse(
            success=True,
            data=consistent_data,
            raw_output=result.raw
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