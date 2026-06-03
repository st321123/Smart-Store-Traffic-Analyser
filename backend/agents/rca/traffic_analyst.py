"""
Traffic Analyst - RCA Domain Agent #1
Analyzes stores traffic patterns, anomalies, and trends.

CUBES: StoreTraffic, Calendar, Location
"""


import json 
import os 
from langchain_openai import AzureChatOpenAI
from agents.state import ChatState,QueryRecord, TraceStep
from datetime import datetime, timezone
from tools.cubejs_client import query_cubejs, format_cubejs_response
from agents.rca.guardrails import compute_data_quality, build_safe_finding


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

llm = AzureChatOpenAI(
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key = os.getenv("AZURE_OPENAI_API_KEY"),
    api_version = os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature = 0
)



from datetime import datetime, timezone

from agents.state import ChatState,QueryRecord, TraceStep

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


TRAFFIC_PROMPT = """ You are a retail traffic analyst performing root cause analysis.

AVAILABLE CUBES:
- StoreTraffic : total_visits, avg_daily_traffic, peak_traffic, avg_conversion_rate, traffic_days(measures)
  Dimensions: location_id, traffic_date
  Joins: Location( via location_id)
  

- Location: store_count(measures)
  Dimensions: location_id, location_name, city, state, country, region, store_type

  NOTE: Calendar cube is NOT joined to StoreTraffic. Do NOT use calendar dimensions.
  

USER QUESTION: {user_query}
ENTITIES: {entities}

YOUR TASK:
1. Build Cube.js queries to investigate traffic patterns.
2. Use timeDimensions with traffic_date for date filtering and granularity
3. Compare stores by using location dimensions (via StoreTraffic.Location.region etc.)


STRICT RULES: 
- Only use the exact measure/dimension names listed above. Copy-paste them exactly.
- DO NOT invent measure names - only use what's listed.
- Never user filters with "operator": "beforeDate" or "values": ["now"] - this causes "invalid date" errors

DATE HANDLING (MANDATORY FORMAT):
Use timeDimensions with dateRange string. Example:
{{
    "measures": ["StoreTraffic.total_visits"], "timeDimensions": [{{"dimension": "StoreTraffic.total_visits","dateRange":"Last 30 days"}}]
    
}}
Valid dateRange values: "Last 7 days", "Last 30 days" , "Last 90 days", "Last year", "This month", "This year"

Generate 2-4 Cube.js queries as a valid JSON array only.
Do not include explanations or markdown.
"""

TRAFFIC_ANALYSIS_PROMPT = """ You are a traffic analyst. Based on the data below, 
provide your finding for the root cause analysis.

USER QUESTION :{user_query}
DATA FROM QUERIES:
{query_results}

Respond in this JSON format:
{{
    "summary":"1-2 sentence summary of traffic finding",
    "severity":"high|medium|low|none",
    "metrics":{{
              "current_traffic":0,
              "prior_traffic":0,
              "change_pct": 0,
              "worst_days":[],
              "worst_hours":[]
                
                }},
    "evidence": ["specific data point 1", "specific data point 2"]

}}

"""


async def traffic_analyst_node(state: ChatState) -> dict:
    print("Running: Traffic Analyst Agent....")
    user_query = state["user_query"]
    entities = state.get("entities",{})
    trace: list[TraceStep] = []
    query_records: list[QueryRecord] = []

    trace.append(TraceStep(agent= "traffic_analyst",action = "Generating Cubeljs queries for traffic analysis", detail = "", timestamp = _now()))
    query_response = await llm.ainvoke([
        {"role":"system", "content":TRAFFIC_PROMPT.format(
            user_query = user_query,
            entities = json.dumps(entities),
        )},
        {"role":"user","content":" Generate the Cube.js queries."}
    ])


    try:
        queries = json.loads(query_response.content)

    except json.JSONDecodeError:
        queries = []
    trace.append(TraceStep(agent= "traffic_analyst",action = f"Generated {len(queries)} queries", detail = "", timestamp = _now()))
    results = []
    
    

    for i,q in enumerate(queries[:4]):
        try: 
            # print("Query",q)
            raw = await query_cubejs(q)
            data = format_cubejs_response(raw)
            print("RESULT DATA", data[:5])
            results.append({"query_index":i, "data":data[:30]})
            query_records.append(QueryRecord(agent = "traffic_analyst", query =q, data = data[:20], status = "success" if data else "empty",error = ""))
        except Exception as e:
            results.append({"query_index":i, "error":str(e)})
            query_records.append(QueryRecord(agent = "traffic_analyst", query =q, data = [], status = "error", error = str(e)))


    quality,succeeded,failed = compute_data_quality(results)
    print(f"Traffic data quality: {quality} {succeeded} , {failed}")
    trace.append(TraceStep(agent= "traffic_analyst",action = f"Data quality: {quality} {succeeded} ok, {failed}:falied queries", detail = "", timestamp = _now()))
    if quality == "none":
        trace.append(TraceStep(agent= "traffic_analyst",action = f"Skipped LLM analysis - no usable data", detail = "", timestamp = _now()))
        return{"findings":[build_safe_finding("traffic_analyst",{},quality,succeeded, failed)]}
    
    
    analysis_response = await llm.ainvoke([
        {
            "role":"system",
            "content": TRAFFIC_ANALYSIS_PROMPT.format(
                user_query = user_query,
                query_results = json.dumps(results, indent = 2)
            )
        },
        {
            "role":"user",
            "content": "Provide your traffic analysis finding."
        }])
    
   
    try:
        finding = json.loads(analysis_response.content)

    except json.JSONDecodeError:
        finding = {"summary": "Unable to analyse traffic data", "severity":"none","metrics":{}, "evidence":[]}
         
    trace.append(TraceStep(agent= "traffic_analyst",action = f"Analysis complete - severity: {finding.get('severity','unknown',)}", detail = "", timestamp = _now()))
    return {
        "findings": [ build_safe_finding( "traffic_analyst",finding, quality, succeeded, failed)], "queries_executed": query_records, "agent_trace": trace}