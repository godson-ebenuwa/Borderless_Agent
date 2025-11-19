import sqlite3
import os
import glob
# Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv()
from textwrap import dedent

from IPython.display import display, Markdown
import pandas as pd
from pydantic import Field
from crewai import LLM
from crewai import Agent, Crew, Process, Task
from crewai.tools import tool, BaseTool
from langchain.schema.output import LLMResult
from langchain_community.tools.sql_database.tool import (
    InfoSQLDatabaseTool,
    ListSQLDatabaseTool,
    QuerySQLCheckerTool,
    QuerySQLDataBaseTool,
)
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# conn = sqlite3.connect("tcmbank_database.db")

# # Get all CSV files in a folder
# csv_files = glob.glob(os.path.join("..", "data", "raw", "tcm_bank_csv", "*.csv"))
# print(csv_files)

# # Loop through CSV files and import each into SQLite
# for file in csv_files:
#     # Use filename (without extension) as table name
#     table_name = file.split("\\")[-1].replace(".csv", "")

#     # Read CSV into DataFrame, trying 'latin-1' encoding
#     try:
#         df = pd.read_csv(file, encoding='latin-1')
#     except UnicodeDecodeError:
#         # If 'latin-1' fails, try another common encoding like 'cp1252'
#         try:
#             df = pd.read_csv(file, encoding='cp1252')
#         except Exception as e:
#             print(f"Could not read file {file} with latin-1 or cp1252 encoding: {e}")
#             continue # Skip to the next file

#     # Write to SQLite (if table exists, replace it)
#     df.to_sql(table_name, conn, if_exists="replace", index=False)

# print("All CSV files have been imported into SQLite!")
# conn.close()

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")
google_api_key=os.getenv("GOOGLE_API_KEY")
agent = LLM(model="gemini/gemini-2.5-flash-lite")

db = SQLDatabase.from_uri("sqlite:///tcmbank_database.db")
#db = SQLDatabase.from_uri("sqlite:///app/data/tcmbank_database.db")

@tool("list_tables")
def list_tables() -> str:
    """List the available tables in the database"""
    return ListSQLDatabaseTool(db=db).invoke("")


@tool("tables_schema")
def tables_schema(tables: str) -> str:
    """
    Input is a comma-separated list of tables, output is the schema and sample rows for those
    tables. Be sure that the tables actually exist before calling `list_tables` first!
    Example Input: table1, table2, table3
    """
    tool = InfoSQLDatabaseTool(db=db)
    return tool.invoke(tables)


@tool("execute_sql")
def execute_sql(sql_query: str) -> str:
    """Execute a SQL query against the database. Returns the result"""
    return QuerySQLDataBaseTool(db=db).invoke(sql_query)


@tool("check_sql")
def check_sql(sql_query: str) -> str:
    """
    Use this tool to double check if your query is correct before executing it. Always use this tool before
    using executing a query with `execute_sql`.
    """
    # Use the LangChain ChatGoogleGenerativeAI instance instead of the crewai.LLM wrapper
    return QuerySQLCheckerTool(db=db, llm=llm).invoke({"query": sql_query})


search = GoogleSerperAPIWrapper


class SearchTool(BaseTool):
    name: str = "search"
    description: str = "A search engine. Useful for when you need to find information about current events or topics that are not in your database. Input should be a search query."
    search: GoogleSerperAPIWrapper = Field(default_factory=GoogleSerperAPIWrapper)

    def _run(self, query: str) -> str:
        """Execute the search query and return the results."""
        try:
            return self.search.run(query)
        except Exception as e:
            return f"Error performing search: {str(e)}"


search_tool = SearchTool()

sql_dev = Agent(
    role="Senior Database Developer",
    goal="Construct and execute SQL queries based on a request",
    backstory=dedent(
        """
        You are an experienced database engineer who is master at creating efficient and complex SQL queries.
        You have a deep understanding of how different databases work and how to optimize queries.
        You have access to the following table descriptions to help you understand the database schema:

        *   **disease_all:** This table contains information about various diseases, including their names and potentially related Traditional Chinese Medicine (TCM) concepts. Key columns might include disease names in English and Chinese, and possibly links to other relevant data.<br>**Use For**: Disease identification, medical classifications, symptom mapping, disease relationships.
        *   **gene_all:** This table contains information about genes/proteins that serve as therapeutic targets with chromosomal locations and target validation status. Key columns might include gene identifiers and names.<br>**Use For**: Disease identification, medical classifications, symptom mapping, disease relationships.
        *   **herb_all:** This table contains information about traditional Chinese herbs. It includes details such as TCM names, English names, Latin names, properties, meridians, functions, and indications.<br>**Use For**: Traditional TCM knowledge, herb properties, meridian theory, classical indications
        *   **ingredient_all:** This table contains information about active chemical ingredients/compounds found in TCM herbs. It includes various identifiers, chemical properties, and potentially links to herbs or formulas.<br>**Use For**: Chemical structures, drug-likeness, pharmacokinetic properties, molecular identification

        ## Key Relationships & Data Flow

        **Primary Research Chain**: Herbs → Ingredients → Genes → Diseases

        ### Critical Connections:
        1. **TCMBank_ID**: Links herbs to their constituent ingredients
        2. **Source_ID**: Cross-references across external databases
        3. **Traditional-Modern Bridge**: Herb indications ↔ Disease classifications
        4. **Molecular Mechanisms**: Ingredient structures ↔ Gene targets ↔ Disease pathways

        ## Retrieval Instructions

        ### Query Processing Strategy:
        1. **Identify Query Type**:
          - Traditional TCM (herb names, properties, meridians)
          - Chemical/Molecular (compound names, structures, targets)
          - Medical (diseases, symptoms, conditions)
          - Mechanistic (how/why questions about TCM effects)

        2. **Multi-File Search Approach**:
          - **Single Entity Queries**: Start with the most relevant file, then expand
          - **Relationship Queries**: Search across multiple files simultaneously
          - **Mechanism Queries**: Follow the Herb→Ingredient→Gene→Disease pathway

        3. **Search Field Prioritization**:
          - **Primary**: Exact name matches, IDs
          - **Secondary**: Aliases, synonyms, alternative names
          - **Tertiary**: Descriptions, functions, classifications
          - **Contextual**: Related terms, broader categories

        ### Specific Retrieval Patterns:

        **For Traditional TCM Queries**:
        - Search herb_all for: TCM_name, Properties, Meridians, Function, Indication
        - Cross-reference with ingredient_all using TCMBank_ID
        - Link to disease_all through indication matching

        **For Chemical/Pharmacological Queries**:
        - Search ingredient_all for: compound names, molecular properties, ADMET data
        - Connect to gene_all for target information
        - Trace back to herb_all for source herbs

        **For Disease/Medical Queries**:
        - Search disease_all using multiple classification systems
        - Find related genes in gene_all
        - Identify targeting ingredients in ingredient_all
        - Trace to source herbs in herb_all

        **For Mechanism/Integration Queries**:
        - Follow complete pathway: specific herb → active ingredients → molecular targets → disease effects
        - Use cross-references and IDs to maintain data integrity
        - Combine traditional knowledge with molecular evidence


        Use the `list_tables` to find available tables.
        Use the `tables_schema` to understand the metadata for the tables.
        Use the `check_sql` to check your queries for correctness.
        Use the `execute_sql` to execute queries against the database.
        Use the `search_tool` to find information outside of the database.
    """
    ),
    llm=agent,
    tools=[list_tables, tables_schema, execute_sql, check_sql, search_tool],
    allow_delegation=False,
)

data_analyst = Agent(
    role="Senior Data Analyst",
    goal="Transform retrieved botanical research into structured JSON",
    backstory=dedent(
        """
        You have deep experience with analyzing datasets using Python.
        Your work is always based on the provided data and is clear,
        easy-to-understand and to the point. You have attention
        to detail and always produce very detailed work (as long as you need).
    """
    ),
    llm=agent,
    allow_delegation=False,
)

# research_formatter = Agent(
#     role="Formatter Specialist",
#     goal="Transform retrieved botanical research into structured JSON",
#     backstory=dedent(
#         "You are a highly disciplined data formatter. "
#         "Your sole responsibility is to take research output from the retriever agent "
#         "and convert it into a concise, standardized JSON structure for UI rendering."
#     ),
#     instructions=dedent(
#         """
#     - Input: messy or verbose botanical research data from the retriever agent.
#     - Output: valid JSON matching the schema below.
#     - Do not include explanations, markdown, or extra text.
#     - If information is missing, omit that field.
#     - Always ensure valid JSON syntax.
#
#     JSON Schema:
#     {
#       "specimen_description": {
#         "botanical_name": "string",
#         "common_names": ["string"],
#         "part_used": "string",
#         "preparation_form": "string",
#         "morphology": "string"
#       },
#       "key_compounds": [
#         {
#           "compound": "string",
#           "class": "string",
#           "concentration_mg_g": number,
#           "function": "string"
#         }
#       ],
#       "compound_distribution": {
#         "Flavonoid": number,
#         "Phenolic acid": number,
#         "Carotenoid": number,
#         "Mineral": number
#       },
#       "toxicities_and_deficiencies": {
#         "toxicities": ["string"],
#         "deficiencies": ["string"]
#       },
#       "complementary_botanicals": {
#         "iron_deficiency_anemia": ["string"],
#         "enhanced_bioavailability": ["string"]
#       },
#       "treatable_ailments": ["string"],
#       "pharmaceutical_comparison": [
#         {
#           "pharmaceutical": "string",
#           "comparison": "string"
#         }
#       ]
#     }
#
#     botanical_name: Latin name of the herb.
#     common_names: List of common names in English.
#     part_used: Part of the plant used medicinally (e.g., leaves, roots).
#     preparation_form: Form in which the herb is prepared (e.g., extract, powder).
#     morphology: Description of the plant's physical characteristics.
#     key_compounds: List of key chemical compounds found in the herb.
#         compound: Name of the compound.
#         class: Chemical class (e.g., Flavonoid, Alkaloid).
#         concentration_mg_g: Concentration in mg/g.
#         function: Biological function or effect.
#     compound_distribution: Distribution of major compound classes as percentages.
#         Flavonoid: Percentage of flavonoids.
#         Phenolic acid: Percentage of phenolic acids.
#         Carotenoid: Percentage of carotenoids.
#         Mineral: Percentage of minerals.
#     toxicities_and_deficiencies: Known toxicities and nutrient deficiencies.
#         toxicities: List of known toxic effects.
#         deficiencies: List of nutrient deficiencies caused by the herb.
#     complementary_botanicals: Plants that enhance therapeutic effect or bioavailability when combined.
#         iron_deficiency_anemia (example condition-specific synergy) → Plants that pair well to treat a given ailment.
#         enhanced_bioavailability → Plants that improve absorption of key compounds.
#     treatable_ailments: List of ailments treatable with this herb.
#     pharmaceutical_comparison: Comparison with conventional pharmaceuticals.
#     """
#     ),
#     llm=agent,
#     allow_delegation=False,
# )


# second research template
# research_formatter = Agent(
#     role="Formatter Specialist",
#     goal="Transform retrieved botanical research into structured JSON",
#     backstory=dedent(
#         "You are a highly disciplined data formatter. "
#         "Your sole responsibility is to take research output and convert it into a concise, standardized JSON structure."
#     ),
#     instructions=dedent("""
#     CRITICAL INSTRUCTIONS:
#     - You MUST return ONLY valid JSON, no additional text, no explanations
#     - The JSON MUST follow this EXACT structure every time
#     - If information is missing for any field, use null or empty arrays/objects
#     - Always ensure valid JSON syntax that can be parsed by json.loads()
#
#     REQUIRED JSON STRUCTURE:
#     {
#       "specimen_description": {
#         "botanical_name": "string",
#         "common_names": ["string"],
#         "part_used": "string",
#         "preparation_form": "string",
#         "morphology": "string"
#       },
#       "key_compounds": [
#         {
#           "compound": "string",
#           "class": "string",
#           "concentration_mg_g": "number or null",
#           "function": "string"
#         }
#       ],
#       "compound_distribution": {
#         "Flavonoid": "number or null",
#         "Phenolic_acid": "number or null",
#         "Carotenoid": "number or null",
#         "Mineral": "number or null"
#       },
#       "toxicities_and_deficiencies": {
#         "toxicities": ["string"],
#         "deficiencies": ["string"]
#       },
#       "complementary_botanicals": {
#         "iron_deficiency_anemia": ["string"],
#         "enhanced_bioavailability": ["string"]
#       },
#       "treatable_ailments": ["string"],
#       "pharmaceutical_comparison": [
#         {
#           "pharmaceutical": "string",
#           "comparison": "string"
#         }
#       ]
#     }
#
#     RULES:
#     1. Return ONLY the JSON object, nothing else
#     2. Use null for missing numerical values
#     3. Use empty arrays [] for missing list values
#     4. Use empty strings "" for missing string values
#     5. Maintain the exact field names and structure
#     """),
#     llm=agent,
#     allow_delegation=False,
# )


# research_formatter = Agent(
#     role="Strict JSON Formatter",
#     goal="Transform botanical research into EXACT JSON structure using ONLY specified field names",
#     backstory=dedent(
#         "You are an extremely disciplined data formatter who follows instructions precisely. "
#         "You NEVER invent field names and ALWAYS use the exact variable names provided."
#     ),
#     instructions=dedent("""
#     CRITICAL: You MUST use ONLY these exact field names. DO NOT invent new names.
#
#     REQUIRED JSON STRUCTURE - USE THESE EXACT FIELD NAMES:
#     {
#       "specimen_description": {
#         "botanical_name": "string",           // NEVER use: plant_name, scientific_name, botanical_information
#         "common_names": ["string"],           // NEVER use: synonyms, other_names, common_names_list
#         "part_used": "string",                // NEVER use: parts_used, plant_parts, utilized_parts
#         "preparation_form": "string",         // NEVER use: preparation_forms, preparation_methods, forms
#         "morphology": "string"                // NEVER use: description, plant_description, physical_characteristics
#       },
#       "key_compounds": [                      // NEVER use: chemical_compounds, active_compounds, compounds
#         {
#           "compound": "string",               // NEVER use: name, chemical_name, component
#           "class": "string",
#           "concentration_mg_g": "number or null",
#           "function": "string"                // NEVER use: description, effect, property
#         }
#       ],
#       "compound_distribution": {
#         "Flavonoid": "number or null",
#         "Phenolic_acid": "number or null",
#         "Carotenoid": "number or null",
#         "Mineral": "number or null"
#       },
#       "toxicities_and_deficiencies": {        // NEVER use: safety_profile, side_effects, adverse_effects
#         "toxicities": ["string"],             // NEVER use: potential_adverse_effects, safety_concerns
#         "deficiencies": ["string"]            // NEVER use: contraindications, limitations
#       },
#       "complementary_botanicals": {           // NEVER use: synergistic_combinations, herb_combinations
#         "iron_deficiency_anemia": ["string"],
#         "enhanced_bioavailability": ["string"] // NEVER use: complementary_herbs, synergistic_herbs
#       },
#       "treatable_ailments": ["string"],       // NEVER use: therapeutic_applications, medical_uses, conditions
#       "pharmaceutical_comparison": [          // NEVER use: drug_comparisons, pharmaceutical_context
#         {
#           "pharmaceutical": "string",         // NEVER use: drug_name, medicine, compound
#           "comparison": "string"              // NEVER use: description, effect_comparison, similarity
#         }
#       ]
#     }
#
#     FIELD MAPPING RULES - TRANSFORM THESE TO CORRECT FIELDS:
#     If you see "plant_name" → USE "specimen_description.botanical_name"
#     If you see "scientific_name" → USE "specimen_description.botanical_name"
#     If you see "parts_used" → USE "specimen_description.part_used" (convert array to string)
#     If you see "preparation_forms" → USE "specimen_description.preparation_form" (convert array to string)
#     If you see "chemical_compounds" → USE "key_compounds"
#     If you see "therapeutic_applications" → USE "treatable_ailments"
#     If you see "safety_profile" → USE "toxicities_and_deficiencies"
#     If you see "synergistic_combinations" → USE "complementary_botanicals.enhanced_bioavailability"
#     If you see "pharmaceutical_comparisons" → USE "pharmaceutical_comparison"
#
#     STRICT FORMATTING RULES:
#     1. Return ONLY the JSON object, no explanations, no markdown, no code blocks
#     2. Use EXACT field names from above - no variations allowed
#     3. Convert arrays to strings for part_used and preparation_form
#     4. If data is missing, use: null for numbers, [] for arrays, "" for strings
#     5. NEVER include additional fields like "conclusion", "notes", "data_limitations"
#     6. ALWAYS use this structure even if some fields are empty
#
#     EXAMPLES OF WRONG → RIGHT:
#     WRONG: "plant_name": "Neem"
#     RIGHT: "specimen_description": {"botanical_name": "Neem"}
#
#     WRONG: "parts_used": ["Leaves", "Bark"]
#     RIGHT: "specimen_description": {"part_used": "Leaves, Bark"}
#
#     WRONG: "chemical_compounds": ["Azadirachtin"]
#     RIGHT: "key_compounds": [{"compound": "Azadirachtin", "class": "", "concentration_mg_g": null, "function": ""}]
#
#     WRONG: "therapeutic_applications": ["Malaria"]
#     RIGHT: "treatable_ailments": ["Malaria"]
#
#     WRONG: "safety_profile": {"side_effects": ["Nausea"]}
#     RIGHT: "toxicities_and_deficiencies": {"toxicities": ["Nausea"]}
#
#     FINAL OUTPUT MUST BE: { ... } with no surrounding text
#     """),
#     llm=agent,
#     allow_delegation=False,
# )

research_formatter = Agent(
    role="Strict Data Extractor",
    goal="Extract ONLY these 9 variables from any botanical response - ignore everything else",
    backstory=dedent(
        "You are a precise data extractor. You scan botanical information and extract ONLY "
        "the 9 specified variables. You ignore all other data, notes, assessments, and additional fields."
    ),
    instructions=dedent("""
    CRITICAL: Extract ONLY these 9 variables. Ignore ALL other data including:
    - data_completeness_assessment
    - plant_morphology (extract only the description for Morphology)
    - therapeutic_applications (extract all ailments into one list)
    - safety_profile (extract toxicities and deficiencies into one list)
    - Any other fields not in the 9 variables below

    REQUIRED 9 VARIABLES - EXTRACT AND RETURN ONLY THESE:
    {
      "Botanical_name": "string",
      "Common_name": ["string"], 
      "Parts_used": ["string"],
      "Preparation_form": ["string"],
      "Morphology": "string",
      "Key_compounds": ["string"],
      "Toxicities_and_Deficiencies": ["string"],
      "Complementary_Botanicals": ["string"],
      "Treatable_ailments": ["string"],
      "Pharmaceutical_Comparisons": ["string"]
    }

    EXTRACTION RULES FROM YOUR SAMPLE RESPONSE:

    1. "Botanical_name" - Extract directly from "botanical_name" field
       • "Cymbopogon citratus" → "Cymbopogon citratus"

    2. "Common_name" - Extract array from "common_names" field
       • ["Lemongrass", "Barbed wire grass"...] → ["Lemongrass", "Barbed wire grass"...]

    3. "Parts_used" - Extract from "usable_parts_and_preparations.part_used"
       • "The leaves and stalks..." → Extract and convert to ["Leaves", "Stalks"]
       • If it's a string describing parts, extract the plant parts mentioned

    4. "Preparation_form" - Extract from "usable_parts_and_preparations.preparation_forms"
       • ["Tea", "Essential Oil", "Tinctures"] → ["Tea", "Essential Oil", "Tinctures"]

    5. "Morphology" - Extract description from "plant_morphology"
       • Take the main growth description: "Tall grass, reaching up to 5 feet..."
       • Combine key points into one descriptive string

    6. "Key_compounds" - Extract directly from "key_chemical_constituents"
       • ["Citral", "Geraniol", "Citronellol", "Limonene"] → ["Citral", "Geraniol", "Citronellol", "Limonene"]

    7. "Toxicities_and_Deficiencies" - Extract from "safety_profile"
       • Toxicities: Extract from "safety_profile.toxicities.general" and "safety_profile.toxicities.caution"
       • Deficiencies: Extract from "safety_profile.deficiencies"
       • Combine into one array: ["No widely documented toxicities", "Potential skin irritation from essential oil", "No specific deficiencies"]

    8. "Complementary_Botanicals" - Extract directly from "complimentary_botanicals"
       • ["Ginger", "Mint"] → ["Ginger", "Mint"]

    9. "Treatable_ailments" - Extract ALL from "therapeutic_applications"
       • Combine ALL subcategories into one flat array:
         - digestive_system: ["Digestive disorders", "Stomachache", "Vomiting"]
         - fever_and_inflammation: ["Fever", "Rheumatism"]
         - respiratory_system: ["Coughs"]
         - etc.
       • Final: ["Digestive disorders", "Stomachache", "Vomiting", "Fever", "Rheumatism", "Coughs"...]

    10. "Pharmaceutical_Comparisons" - Extract directly from "pharmaceutical_comparisons"
        • ["Anti-inflammatory Drugs: Its properties...", "Digestive Aids: Its use..."] 
        → ["Anti-inflammatory Drugs: Its properties...", "Digestive Aids: Its use..."]

    MISSING DATA RULES:
    • If any variable is not present, use empty array [] or empty string ""
    • If data is nested, extract and flatten it
    • If data is in descriptive text, extract the key information

    IGNORE THESE FIELDS COMPLETELY:
    • data_completeness_assessment
    • Any additional notes, summaries, or assessments
    • Any fields not mapping to the 9 variables

    FINAL OUTPUT MUST CONTAIN ONLY THESE 9 VARIABLES WITH EXACT THESE NAMES.
    """),
    llm=agent,
    allow_delegation=False,
)

# Create Tasks
extract_data = Task(
    description=("Extract data that is required for the query {query}."
                 " First figure out which tables to use and what SQL query to run."
                 "query the database using latin name if common name search fails."
                 " Then check the SQL query for correctness and execute it."
                 " Finally analyze the data and return the results."
                 " Only use the tools available to you. Do not make up any data."
                 "for each query, return: the botanical name, common names, part used, preparation form, key compounds, toxicities and deficiencies, complimentary botanicals, treatable ailments, pharmaceutical comparisons and morphology of the herb mentioned in the query."
                 " If you cannot find the data for any of these fields in the database, search for it using the search tool."
                 "If there are multiple herbs mentioned in the query, return the information for all of them. If no herbs are mentioned in the query, return an empty result."),
    expected_output="Database result for the query including botanical name, common names, part used, preparation form and morphology of the herb.",
    agent=sql_dev,
)

analyze_data = Task(
    description=("Analyze the data from the database and write an analysis for {query}."
                 " Make sure to base your analysis on the provided data and do not make up any information."
                 " If the data is incomplete or insufficient, state that in your analysis."
                 " Write a detailed analysis that covers all aspects of the data."
                 " The analysis should be easy to understand and to the point."
                 " Use bullet points, tables or other formatting to make the analysis clear."
                 " The analysis should be comprehensive and cover all relevant details."),
    expected_output="Detailed analysis text",
    agent=data_analyst,
    context=[extract_data],
)

format_output = Task(
    description=(
        "Extract and return ONLY these 9 variables from the botanical data: "
        "Botanical_name, Common_name, Parts_used, Preparation_form, Morphology, "
        "Key_compounds, Toxicities_and_Deficiencies, Complementary_Botanicals, "
        "Treatable_ailments, Pharmaceutical_Comparisons. "
        "Ignore all other fields including data_completeness_assessment and any additional notes. "
        "Flatten nested therapeutic applications into one Treatable_ailments array. "
        "Combine toxicities and deficiencies into one Toxicities_and_Deficiencies array. "
        "Return ONLY the JSON object with these 9 exact variables."
    ),
    expected_output="JSON with exactly 9 variables containing only the extracted data",
    agent=research_formatter,
    context=[analyze_data],
)


crew = Crew(
    agents=[sql_dev, data_analyst, research_formatter],
    tasks=[extract_data, analyze_data, format_output],
    process=Process.sequential,
    verbose=False,
    memory=False,
)

if __name__ == "__main__":
    inputs = {
        "query": "bitter leaf"
    }
    result = crew.kickoff(inputs=inputs)
    display(Markdown(result.raw))  