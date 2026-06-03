"""
Customer & Feedback Analyst - RCA Domain Agen #5 
Analyzes sentiment, loyalty, complaints, and customer satisfaction.

CUBES: Customers, Feedback, ProductReviews , CustomerLoyalty

"""

import json 
import os
from langchain_openai import AzureChatOpenAI
from datetime import datetime, timezone
from agents.state import ChatState,QueryRecord, TraceStep
from tools.cubejs_client import query_cubejs, format_cubejs_response
from agents.rca.guardrails import compute_data_quality, build_safe_finding

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
CUSTOMER_PROMPT = """ You are a retail customer experience analyst performing root cause analysis.

AVAILABLE CUBES:
- Customers: customer_count (measures)
  Dimension: customer_id, first_name, last_name, gender_cd ,email ,city, state,loyalty_status,join_date

- Feedback: feedback_count, avg_rating, low_rating_count, high_rating_count(measures)
  Dimensions: store_id, feedback_date, rating, feedback_category,feedback_comments,resolution_status

- ProductReviews: avg_product_rating,review_count, total_helpful_votes, low_review_count, high_review_count (measures)
  Dimensions: product_id, review_date, rating, review_text, verified_purchase_flag, helpful_votes

- CustomerLoyalty:total_points_earned, total_points_redeemed, avg_points_balance,loyalty_txn_count,avg_points_earned(measures)
  Dimensions: customer_id, loyalty_id, transaction_date, transaction_type

USER QUESTION: {user_query}
ENTITIES: {entities}

STRICT RULES: 
- Only use the exact measure/dimension names listed above. Copy-paste them exactly.
- DO NOT invent measure names - only use what's listed.
- Never user filters with "operator": "beforeDate" or "values": ["now"] - this causes "invalid date" errors

DATE HANDLING (MANDATORY FORMAT):
Use timeDimensions with dateRange string. Example:
{{
    "measures": ["Feedback.feedback_count"], "timeDimensions": [{{"dimension": "Feedback.feedback_date","dateRange":"Last 30 days"}}]
    
}}
Valid dateRange values: "Last 7 days", "Last 30 days" , "Last 90 days", "Last year", "This month", "This year"


  
FORBIDDEN NAMES (these  DO NOT EXIST - never use them):
- "member_count" -> use "loyalty_txn_count" instead
- "feedback_text" -> use "feedback_comments" instead
- "sentiment" -> does not exist
- "avg_rating" on ProductReviews -> use "avg_product_rating" instead
- "avg_age" -> does not exist
- "review_count" on Feedback -> use "feedback_count" instead


YOUR TASK:
1. Check rating trends over time
2. Analyze complaint volume by feedback category.
3. Look at loyalty transaction changes
4. Check product review ratings.

Generate 2-5 cube.js queries as a JSON array.
"""

CUSTOMER_ANALYSIS_PROMPT = """ You are a customer experience analyst. Based on the data below provide your finding for the root
cause analysis.
USER QUESTION: {user_query}

DATA FROM QUERIES:
{query_results}

Response in this JSON format:{{
"summary":"1-2 sentence summary of customer/feedback finding",
"severity":"high|medium|low|none",
"metrics":{{
    "avg_rating_current":0,
    "complaint_count": 0,
    "repeat_rate": 0,
    "loyalty_change":0
}},
"evidence":[ "specific data point 1", "specific data point 2"]
}}

"""


async def customer_analyst_node(state: ChatState)-> dict:
    print("Running: Customers Analyst Agent....")
    user_query = state["user_query"]
    entities = state.get("entities",{})
    # trace: list[TraceStep] = []
# query_records: list[QueryRecord] = []
# trace.append(TraceStep(agent= "kpi_agent",action = "Generating Cube.js from user question",detail = "", timestamp = _now()))
    query_response = await llm.ainvoke([
        { "role":"system","content": CUSTOMER_PROMPT.format(
            user_query = user_query,
            entities = json.dumps(entities),
        )},
        {"role":"user","content":"Generate the Cube.js queries"}
    ])


    try:
        queries = json.loads(query_response.content)

    except json.JSONDecodeError:
        queries = []
    # trace.append(TraceStep(agent= "kpi_agent",action = "LLM returned invalid JSON - could not parse query ",detail = query_response.content[:200], timestamp = _now()))
    results = []
    for i , q in enumerate(queries[:4]):
        try:
            # print("QUERY",q)
            raw = await query_cubejs(q)
            data = format_cubejs_response(raw)
            print("RESULT DATA", data[:5])
            results.append({"query_index":i, "date": data[:30]})
            # query_records.append(QueryRecord(agent= "kpi_agent", query = cubejs_query,data = data[:20], status = "success" if data else "empty", error = ""))
            
        except Exception as e:
            results.append({"query_index":i, "error":str(e)}) 
            # query_records.append(QueryRecord(agent= "kpi_agent", query = cubejs_query,data = data[:20], status = "success" if data else "empty", error = ""))


    quality, succeeded, failed = compute_data_quality(results)
    print(f" Customer data quality : {quality} {succeeded}, {failed}")
    # trace.append(TraceStep(agent= "kpi_agent",action = "LLM returned invalid JSON - could not parse query ",detail = query_response.content[:200], timestamp = _now()))
    if quality == "none":
        # trace.append(TraceStep(agent= "kpi_agent",action = "LLM returned invalid JSON - could not parse query ",detail = query_response.content[:200], timestamp = _now()))
        return {"findings": [ build_safe_finding("customer_feedback_analyst",{}, quality, succeeded, failed)]}
    
    analysis_response = await llm.ainvoke(
        [
        {"role":"system","content": CUSTOMER_ANALYSIS_PROMPT.format(
            user_query = user_query,
            query_results = json.dumps(results, indent = 1),
        )},
        {"role":"user","content":"Provide your customer analysis finding."}
    ])

    try:
        finding = json.loads(analysis_response.content)
    except json.JSONDecodeError:
        finding = {"summary":"Unable to analyze customer data","severity":"none","metric":{},"evidence": []}

    # trace.append(TraceStep(agent= "kpi_agent",action = "LLM returned invalid JSON - could not parse query ",detail = query_response.content[:200], timestamp = _now()))
    return {"findings": [ build_safe_finding("customer_feedback_analyst",finding,quality,succeeded, failed)]}