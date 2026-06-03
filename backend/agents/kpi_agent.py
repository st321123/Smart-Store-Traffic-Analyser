"""
KPI Agent - handles direct data question
Converts natural language -> Cube.js JSON query -> fetches data -> answers.

FLOW: Supervisor (intent = kpi) -> KPI Agent -> Response

"""

import json
import os 
from datetime import datetime, timezone
from langchain_openai import AzureChatOpenAI
from agents.state import ChatState,QueryRecord, TraceStep
from tools.cubejs_client import query_cubejs, format_cubejs_response
llm = AzureChatOpenAI(
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key = os.getenv("AZURE_OPENAI_API_KEY"),
    api_version = os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature = 0
)

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    trace: list[TraceStep] = []
    queries: list[QueryRecord] = []

    trace.append(TraceStep(agent= "kpi_agent",action = "Generating Cube.js from user question",detail = "", timestamp = _now()))
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
            raw = "{"+ raw + "}"
        cubejs_query = json.loads(raw)
    except json.JSONDecodeError:
        print(f"DEBUG KPI --LLM returned non-JSON: \n{query_response.content}")
        trace.append(TraceStep(agent= "kpi_agent",action = "LLM returned invalid JSON - could not parse query ",detail = query_response.content[:200], timestamp = _now()))
        return {"response": "I couldn't understand how to query that. Could you rephrase your question?", "agent_trace": trace,}
    trace.append(TraceStep(agent= "kpi_agent",action = f"Generated Cube.js query targetting {list(cubejs_query.get('measures',[]))}",detail = json.dumps(cubejs_query), timestamp = _now()))
    try:
        raw_response = await query_cubejs(cubejs_query)
        data = format_cubejs_response(raw_response)
        queries.append(QueryRecord(agent= "kpi_agent", query = cubejs_query,data = data[:20], status = "success" if data else "empty", error = ""))
        trace.append(TraceStep(agent= "kpi_agent",action = f"cube.js returned {len(data)} row(s)",detail = "", timestamp = _now()))

    except Exception as e :
        queries.append(QueryRecord(agent= "kpi_agent", query = cubejs_query,data = [], status = "error",error = str(e)))
        trace.append(TraceStep(agent= "kpi_agent",action = f"Cube.js query failed:{e} ",detail = "", timestamp = _now()))
        return {"response":f"I had trouble fetching the data. Error: {str(e)}","queries_executed":queries,"agent_trace": trace}
    
    trace.append(TraceStep(agent= "kpi_agent",action = "Generating natural language answer from data",detail = "", timestamp = _now()))
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

    trace.append(TraceStep(agent= "kpi_agent",action = "KPI answer generated successfully",detail ="", timestamp = _now()))
    return {"response": answer_response.content,
            "queries_executed":queries,
            "agent_trace": trace,
            }