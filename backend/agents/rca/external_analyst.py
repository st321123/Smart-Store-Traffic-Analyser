"""
External Factors Analyst - RCA Domain Agent #6
Identifies external events impacting store traffic.

CUBES: ExternalEvents, Calendar, Location 
"""
import json 
import os
from langchain_openai import AzureChatOpenAI
from datetime import datetime, timezone
from agents.state import ChatState,QueryRecord, TraceStep
from tools.cubejs_client import query_cubejs, format_cubejs_response 
from agents.rca.guardrails import build_safe_finding,compute_data_quality

llm = AzureChatOpenAI(
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key = os.getenv("AZURE_OPENAI_API_KEY"),
    api_version = os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature = 0
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

# trace: list[TraceStep] = []
# query_records: list[QueryRecord] = []
# trace.append(TraceStep(agent= "kpi_agent",action = "Generating Cube.js from user question",detail = "", timestamp = _now()))
# trace.append(TraceStep(agent= "kpi_agent",action = "LLM returned invalid JSON - could not parse query ",detail = query_response.content[:200], timestamp = _now()))
# return {"response": "I couldn't understand how to query that. Could you rephrase your question?", "agent_trace": trace,}
# trace.append(TraceStep(agent= "kpi_agent",action = f"Generated Cube.js query targetting {list(cubejs_query.get('measures',[]))}",detail = json.dumps(cubejs_query), timestamp = _now()))
# query_records.append(QueryRecord(agent= "kpi_agent", query = cubejs_query,data = data[:20], status = "success" if data else "empty", error = ""))
#         trace.append(TraceStep(agent= "kpi_agent",action = f"cube.js returned {len(data)} row(s)",detail = "", timestamp = _now()))
#         query_records.append(QueryRecord(agent= "kpi_agent", query = cubejs_query,data = [], status = "error",error = str(e)))
#         trace.append(TraceStep(agent= "kpi_agent",action = f"Cube.js query failed:{e} ",detail = "", timestamp = _now()))
#         return {"response":f"I had trouble fetching the data. Error: {str(e)}","queries_executed":query_records,"agent_trace": trace}
    
#     trace.append(TraceStep(agent= "kpi_agent",action = "Generating natural language answer from data",detail = "", timestamp = _now()))
# trace.append(TraceStep(agent= "kpi_agent",action = "KPI answer generated successfully",detail ="", timestamp = _now()))
#     return {"response": answer_response.content,
#             "queries_executed":query_records,
#             "agent_trace": trace,
#             }
EXTERNAL_PROMPT = """ You are a retail external factors analyst performing root cause analysis.

AVAILABLE CUBES:

- ExternalEvents: event_count(measures), distinct_event_types(measures)
  Dimensions: store_id, event_date, event_type, event_description, impact_level
- Calendar: calendar_date, day_of_week, is_holiday, holiday_name, season, fiscal_week, fiscal_month
- Location: location_id, location_name, city , state, region, format_type

USER QUESTION = {user_query}
ENTITIES = {entities}

STRICT RULES: 
- Only use the exact measure/dimension names listed above. Copy-paste them exactly.
- DO NOT invent measure names - only use what's listed.
- Never user filters with "operator": "beforeDate" or "values": ["now"] - this causes "invalid date" errors

DATE HANDLING (MANDATORY FORMAT):
Use timeDimensions with dateRange string. Example:
{{
    "measures": ["ExternalEvents.event_count"], "timeDimensions": [{{"dimension": "ExternalEvents.event_date","dateRange":"Last 30 days"}}]
    
}}
Valid dateRange values: "Last 7 days", "Last 30 days" , "Last 90 days", "Last year", "This month", "This year"


YOUR TASK:
1. Check event counts by event_type
2. Look at impact_level distribution
3. Check events by store_id

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
    print("Running: External Analyst Agent....")
    user_query = state["user_query"]
    entities = state.get("entities",{})
    # trace: list[TraceStep] = []
# query_records: list[QueryRecord] = []
# trace.append(TraceStep(agent= "kpi_agent",action = "Generating Cube.js from user question",detail = "", timestamp = _now()))

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
# trace.append(TraceStep(agent= "kpi_agent",action = "Generating Cube.js from user question",detail = "", timestamp = _now()))
    results = []

    for i,q in enumerate(queries[:4]):
        try: 
            # print("QUERY",q)
            raw = await query_cubejs(q)
            data = format_cubejs_response(raw)
            print("RESULT DATA", data[:5])
            results.append({"query_index":i, "data":data[:30]})
            # query_records.append(QueryRecord(agent= "kpi_agent", query = cubejs_query,data = data[:20], status = "success" if data else "empty", error = ""))
        except Exception as e:
            results.append({"query_index":i, "error":str(e)})
            # query_records.append(QueryRecord(agent= "kpi_agent", query = cubejs_query,data = data[:20], status = "success" if data else "empty", error = ""))

    quality, succeeded, failed = compute_data_quality(results)
    print(f" External data quality : {quality} {succeeded}, {failed}")
    # trace.append(TraceStep(agent= "kpi_agent",action = "Generating Cube.js from user question",detail = "", timestamp = _now()))
    if quality == "none":
        # trace.append(TraceStep(agent= "kpi_agent",action = "Generating Cube.js from user question",detail = "", timestamp = _now()))
        return {"findings": [ build_safe_finding("external_factors_analyst",{}, quality, succeeded, failed)]}
    
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
         
# trace.append(TraceStep(agent= "kpi_agent",action = "Generating Cube.js from user question",detail = "", timestamp = _now()))
    return {"findings": [ build_safe_finding("external_factors_analyst",finding,quality,succeeded, failed)]}
