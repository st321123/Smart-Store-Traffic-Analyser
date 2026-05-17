"""
External Factors Analyst - RCA Domain Agent #6
Identifies external events impacting store traffic.

CUBES: ExternalEvents, Calendar, Location 
"""
import json 
import os
from langchain_openai import AzureChatOpenAI
from agents.state import ChatState, AgentFinding
from tools.cubejs_client import query_cubejs, format_cubejs_response 

llm = AzureChatOpenAI(
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key = os.getenv("AZURE_OPENAI_API_KEY"),
    api_version = os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature = 0
)

EXTERNAL_PROMPT = """ You are a retail external factors analyst performing root cause analysis.

AVAILABLE CUBES:

- ExternalEvents: event_count(measures), distinct_event_types(measures)
  Dimensions: store_id, event_date, event_type, event_description, impact_level
- Calendar: calendar_date, day_of_week, is_holiday, holiday_name, season, fiscal_week, fiscal_month
- Location: location_id, location_name, city , state, region, format_type

USER QUESTION = {user_query}
ENTITIES = {entities}


YOUR TASK:
1. Check for weather events (storms, extreme temperatures)
2. Look for road construction or closures near the store
3. Identify competitor activity (new store openings, competitor promos)
4. Check for community events, holiday, or local disruptions
5. Correlate event timing with traffic changes

Generate 2-4 Cube.js queries as a JSON array.

"""

EXTERNAL_ANALYSIS_PROMPT = """ You are an external factors analyst. Based on the data below, provide your findings
for the root cause analysis.

USER QUESTION: {user_query}

DATA FROM QUERIES:
{query_results}

Respons in this JSON format:{{
    "summary":"1-2 sentence summary of external factors finding",
    "severity":"high|medium|low|none",
    "metrics":{{
        "events_found":0,
        "event_details": [],
        "traffic_impact": "estimated impact description"
}},
    "evidence": ["specific data point 1", "specific data point 2"]


"""

async def external_analyst_node(state: ChatState) -> dict:
    user_query = state["user_query"]
    entities = state.get("entities",{})

    query_response = await llm.ainvoke([
        {"role":"system", "content":EXTERNAL_PROMPT.format(
            user_query = user_query,
            entities = json.dumps(entities),
        )},
        {"role":"user","content":" Generate the Cube.js queries."}
    ])


    try:
        queries = json.loads(query_response.content)

    except json.JSONDecodeError:
        queries = []

    results = []

    for i,q in enumerate(queries[:4]):
        try: 
            raw = await query_cubejs(q)
            data = format_cubejs_response(raw)
            results.append({"query_index":i, "data":data[:30]})
        except Exception as e:
            results.append({"query_index":i, "error":str(e)})

    analysis_response = await llm.ainvoke([
        {
            "role":"system",
            "content": EXTERNAL_ANALYSIS_PROMPT.format(
                user_query = user_query,
                query_results = json.dumps(results, indent = 2)
            )
        },
        {
            "role":"user",
            "content": "Provide your external factors analysis finding."
        }
    ])
    

    try:
        finding = json.loads(analysis_response.content)

    except json.JSONDecodeError:
        finding = {"summary": "Unable to analyse external data", "severity":"none","metrics":{}, "evidence":[]}
         

    return {
        "findings": [ AgentFinding(
            agent = "external_factor_analyst",
            summary = finding.get("summary",""),
            severity = finding.get("severity", "none"),
            metrics = finding.get("metrics",{}),
            evidence = finding.get("evidence",[])
        )

        ]
    }
