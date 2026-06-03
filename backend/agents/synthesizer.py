"""
Root Cause Synthesizer - Agent #9 
Cross-correlates findings from all 6 domain analysts, ranks root causes,
and generates actionable recommendations.

Does not call Cube.js - only processes the findings from other agents. 
FLOW: All 6 RCA analysts (parallel) -> Synthsizer -> Response

"""

import json 
import os 
from langchain_openai import AzureChatOpenAI
from agents.state import ChatState, RankedCause

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

# trace: list[TraceStep] = []
# queries: list[QueryRecord] = []
# trace.append(TraceStep(agent= "kpi_agent",action = "Generating Cube.js from user question",detail = "", timestamp = _now()))
# trace.append(TraceStep(agent= "kpi_agent",action = "LLM returned invalid JSON - could not parse query ",detail = query_response.content[:200], timestamp = _now()))
# return {"response": "I couldn't understand how to query that. Could you rephrase your question?", "agent_trace": trace,}
# trace.append(TraceStep(agent= "kpi_agent",action = f"Generated Cube.js query targetting {list(cubejs_query.get('measures',[]))}",detail = json.dumps(cubejs_query), timestamp = _now()))
# queries.append(QueryRecord(agent= "kpi_agent", query = cubejs_query,data = data[:20], status = "success" if data else "empty", error = ""))
#         trace.append(TraceStep(agent= "kpi_agent",action = f"cube.js returned {len(data)} row(s)",detail = "", timestamp = _now()))
#         queries.append(QueryRecord(agent= "kpi_agent", query = cubejs_query,data = [], status = "error",error = str(e)))
#         trace.append(TraceStep(agent= "kpi_agent",action = f"Cube.js query failed:{e} ",detail = "", timestamp = _now()))
#         return {"response":f"I had trouble fetching the data. Error: {str(e)}","queries_executed":queries,"agent_trace": trace}
    
#     trace.append(TraceStep(agent= "kpi_agent",action = "Generating natural language answer from data",detail = "", timestamp = _now()))
# trace.append(TraceStep(agent= "kpi_agent",action = "KPI answer generated successfully",detail ="", timestamp = _now()))
#     return {"response": answer_response.content,
#             "queries_executed":queries,
#             "agent_trace": trace,
#             }
SYNTHESIZER_PROMPT = """You are a senior retail analytics lead.

USER QUESTION: {user_query}

PRIMARY AGENTS STATUS: {primary_status}

AGENTS WITH ACTUAL DATA (only these have real evidence):
{verified_findings}

AGENTS WITH NO DATA (do NOT refrence these):
{no_data_agents}

YOUR TASK:
Based ONLY on the verified findings above, identify potential root causes.

RULES:
1. ONLY cite evidence from the "AGENTS WITH ACTUAL DATA" section.
2. Every evidence point MUST include a specific number (e.g., "22 MEDIUM risk flags")
3. NEVER mention agents from the "NO DATA" list - pretend they don't exist
4. NEVER say "absence of X caused Y" - missing data is not evidence.
5. NEVER say "complete halt", "no activity", or "lack of" - these suggest certainty about absence
6. If the primary agent had no data, say: "Insufficient [domain] data for the requested period"
7. Use words like "may", "potentially", "possible contributing factor" - not definitive statements
8. Maximum confidence = {max_confidence}


RESPOND IN THIS JSON FORMAT:
{{
    "root_causes":[
    {{
    
    
        "rank":1,
        "cause": "Description using ONLY verified evidence",
        "category": "traffic|sales|promo|inventory|customer|external",
        "severity": "high|medium|low",
        "confidence":"{max_confidence}",
        "evidence": ["specific number from verified agent"],
        "recommendation": "Specific action ",
    
    }}],

    "summary": "State what data was available. Use 'may' and 'potentially' for any conclusions"
}}



"""

DOMAIN_KEYWORDS= {
    "traffic_analyst":["traffic","footfall","visit","visitor","walk-in"],
    "sales_analyst":["sales","revenue","transaction","basket","conversion"],
    "promo_pricing_analyst":["promo","promotion","discount","pricing","price"],
    "inventory_supply_analyst":["inventory","stock","stockout","supply","shipment","purchase order"],
    "customer_feedback_analyst":["customer","feedback","rating","review", "loyalty","satisfaction","complaint"],
    "external_factors_analyst":["weather","external","event","holiday","construction"]
}

def detect_primary_agent(user_query: str) ->str:
    query_lower = user_query.lower()
    best_agent = "traffic_analyst"
    best_score = 0
    for agent,keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > best_score:
            best_score = score 
            best_agent = agent
    return best_agent

def build_data_quality_report(findings: list, primary_agent: str) -> str:
    lines = [f"Primary agent for this question: {primary_agent}"]
    for f in findings:
        agent = f.get("agent", "unknown")
        quality = f.get("data_quality", "unknown")
        succeeded = f.get("queries_succeeded",0)
        failed = f.get("queries_failed",0)
        is_primary = "<- PRIMARY" if agent == primary_agent else ""
        lines.append(f" - {agent} : data_quality = {quality} ({succeeded} ok, {failed} failed){is_primary}")
    return "\n".join(lines)

async def synthesizer_node( state: ChatState) -> dict:
    print("Running: Synthesizer Agent....")
    user_query = state["user_query"]
    findings = state.get("findings",[])

    if not findings: 
        return {
            "root_causes": [],
            "response": "No findings were generated by the analyst agents. There may not be enough data to perform a root cause analysis for this query.",

        }
    primary_agent = detect_primary_agent(user_query)
    # data_quality_report = build_data_quality_report(findings,primary_agent)
    print(f"Primary Agent : {primary_agent}")
    # print(f"Data quality: {data_quality_report}")

    # agents_with_data = [f for f in findings if f.get("data_quality") in ("good","partial")]
    # agents_without_data = [f for f in findings if f.get("data_quality") == "none"]
    verified_findings = []
    no_data_agents = []
    primary_has_data = False


    for f in findings:
        agent = f.get("agent","unknown")
        quality = f.get("data_quality", "none")
        succeeded = f.get("queries_succeeded",0)
        failed = f.get("queries_failed",0)
        print(f" {agent}: quality = {quality} ({succeeded} ok, {failed} failed)")
        if quality in ("good", "partial") and f.get("evidence"):
            verified_findings.append(f)
            if agent == primary_agent:
                primary_has_data = True
        else:
                no_data_agents.append(agent)
        
    if not verified_findings:
            return {
            "root_causes":[],
            "response": (
                "**Insufficient data for root cause analysis.**\n\n"
                "All 6 analyst agents either failed to retrieve data or returned empty results "
                "for the requested period. This may be due to:\n"
                "- Data not available for the requested time range \n"
                "- Query filters not matching existing records \n\n"
                "**Suggestion:** Try a specific time period where data exists (e.g., March 2024)."
            ),
        }
    primary_quality = "none"
    for f in findings:
        if f.get("agent") == primary_agent:
            primary_quality = f.get("data_quality","none")
            break
    if primary_quality in ("none","partial"):
        max_confidence = "low"
    elif len(verified_findings) >=3:
        max_confidence = "high" 
    else:
        max_confidence = "medium"
    

    if primary_quality == "none":
        primary_status = f"PRIMARY agent ({primary_agent}) had NO DATA. Analysis is limited."
    elif primary_quality == "partial":
        primary_status = f"PRIMARY agent ({primary_agent}) had PARTIAL data. Confidence is limited."
    else:
        primary_status = f"PRIMARY agent ({primary_agent}) had GOOD data."
    
    no_data_list = ", ".join(no_data_agents) if no_data_agents else "None"

    response = await llm.ainvoke([
        {
            "role":"system", 
            "content": SYNTHESIZER_PROMPT.format(
                user_query = user_query,
                primary_status = primary_status,
                verified_findings = json.dumps(verified_findings, indent = 2, default = str),
                no_data_agents = no_data_list,
                max_confidence = max_confidence
            )
        },
        {
            "role": "user",
            "content":"Synthesize the findings and rank root causes."
        },
    ])

    try:
        result = json.loads(response.content)

    except json.JSONDecodeError:
        return {
            "root_causes": [],
            "response": response.content,
        }

    root_causes= []

    for rc in result.get("root_causes",[]):
        forced_confidence = max_confidence
        root_causes.append(RankedCause(
            rank= rc.get("rank",0),
            cause = rc.get("cause", ""),
            category = rc.get("category",""),
            severity = rc.get("severity","low"),
            confidence = forced_confidence,
            evidence = rc.get("evidence",[]),
            recommendation = rc.get('recommendation',""),
        ))

    return {
        "root_causes": root_causes
    }