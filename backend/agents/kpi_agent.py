"""
KPI Agent - handles direct data question
Converts natural language -> Cube.js JSON query -> fetches data -> answers.

FLOW: Supervisor (intent = kpi) -> KPI Agent -> Response

"""

import json
import os 
from langchain_openai import AzureChatOpenAI
from agents.state import ChatState
from tools.cubejs_client import query_cubejs, format_cubejs_response





llm = AzureChatOpenAI(
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key = os.getenv("AZURE_OPENAI_API_KEY"),
    api_version = os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature = 0
)


KPI_QUERY_PROMPT = """" You are a retail data analyst. Your job is to convert the user's natural langugage 
question into a Cube.js JSON query.
AVAILABLE CUBE METADATA:
{cube_metadata}

ENTITIES EXTRACTED BY SUPERVISOR:
{entities}

RULES:
1. Use only measures and dimensions that exist in the metadata above.
2. Cube.js query format:
    {{
        "measures":[CubeName.measure_name],
        "dimensions":[CubeName.dimension_name],
        "timeDimensions":[{{
            "dimensions": "CubeName.date_field",
            "dateRange": ["YYYY-MM-DD","YYYY-MM-DD"]
            "granularity": "day|week|month"
        
        }}],
        "filters":[{{
            "member": "CubeName.dimension",
            "operator":"equals",
            "values":["value"]
        }}],
        "limit": 10,
        "order":{{"CubeName.measure":"desc"}}
    
    
    }}




3. Only include fields that are needed. Don't add empty arrays.
4. For "top N" questions, add order + limit.
5. For trends, use timeDimensions with granularity.
6. For comparison, you may need two queries.

RESPOND WITH ONLY THE JSON OBJECT. 
- Must strat with {{ and end with }}
- Keys must be in double quotes
- No markdown, no, explanation, no code blocks
- Example: {{"measures": ["SalesDaily.total_sales"]}}


"""




KPI_ANSWER_PROMPT = """You are a retail analytics assistant. The user asked: {user_query}

Here is the data from the database:
{data}

Generate a clear, consise answer:
- Lead with the key number(s)
- Add context (comparison , trends) if data supports it
- Use formatting: bold for key metrics, bullet points for lists
- If the data is empty, say "No data found for the given criteria"
- Keep it converstaional but professional

"""

async def kpi_node(state: ChatState) -> dict:
    print("Running: KPI Agent....")
    user_query = state["user_query"]
    entities = state.get("entities", {})
    cube_metadata = state.get("cube_metadata", "No metadata available")
    
    query_response = await llm.ainvoke([
        { "role":"system", "content": KPI_QUERY_PROMPT.format(
                cube_metadata = cube_metadata,
                entities = json.dumps(entities),

         )},
        {
            "role": "user", "content": user_query
        },
    ])

    try: 
        raw = query_response.content.strip()
        if raw.startswith("```"):
            raw = raw.strip("` \n").removeprefix("json").strip()
        if not raw.startswith("{"):
            raw = "{"+ raw + "{"
        cubejs_query = json.loads(query_response.content)
    except json.JSONDecodeError:
        print(f"DEBUG KPI --LLM returned non-JSON: \n{query_response.content}")
        return {"response": "I couldn't understand how to query that. Could you rephrase your question?" }
    
    try:
        raw_response = await query_cubejs(cubejs_query)
        data = format_cubejs_response(raw_response)

    except Exception as e :
        return {"response":f"I had trouble fetching the data. Error: {str(e)}"}
    

    answer_response = await llm.ainvoke([
        {
            "role": "system", "content": KPI_ANSWER_PROMPT.format(
                user_query = user_query,
                data = json.dumps(data[:50], indent = 2),
            )
        },
        {
            "role": "user", "content": "Generate the answer. "
        },
    ])


    return {"response": answer_response.content}