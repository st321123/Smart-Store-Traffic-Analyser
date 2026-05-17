"""
Customer & Feedback Analyst - RCA Domain Agen #5 
Analyzes sentiment, loyalty, complaints, and customer satisfaction.

CUBES: Customers, Feedback, ProductReviews , CustomerLoyalty

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

CUSTOMER_PROMPT = """ You are a retail customer experience analyst performing root cause analysis.

AVAILABLE CUBES:
- Customers: customer_count, avg_age(measures)
  Dimension: customer_id, first_name, last_name, gender,city, state, registration_date

- Feedback: feedback_count, avg_rating, low_rating_count, high_rating_count(measures)
  Dimensions: store_id, feedback_date, rating, feedback_category,feedback_comments, feedback_text, resolution_status

- ProductReviews: review_count, avg_rating, low_review_count, high_review_count (measures)
  Dimensions: product_id, review_date, rating, review_text, verified_purchase

- CustomerLoyalty: member_count, avg_points, total_points (measures)
  Dimensions: customer_id, loyalty_tier, enrollment_date, points_balance, last_activity_date

USER QUESTION: {user_query}
ENTITIES: {entities}

YOUR TASK:
1. Check NPS/ rating trends over time
2. Analyze complaint volume and categories (what are customers unhappy about?)
3. Look at loyalty engagement changes
4. Identify sentiment shifts in feedback text categories

Generate 2-5 cube.js queries as a JSON array.
"""

CUSTOMER_ANALYSIS_PROMPT = """ You are a customer experience analyst. Based on the data below provide your finding for the root
cause analysis.
USER QUESTION: {user_query}

DATA FROM QUERIES:
{query_results}

Respons in this JSON format:{{
"summary":"1-2 sentence summary of customer/feedback finding",
"severity":"high|medium|low|none",
"metrics":{{
    "avg_rating_current":0,
    "complaint_count": 0,
    "repeat_rate" 0,
    "loyalty_change":0
}},
"evidence":[ "specific data point 1", "specific data point 2"]
}}

"""


async def customer_analyst_node(state: ChatState)-> dict:
    user_query = state["user_query"]
    entities = state.get("entities",{})

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

    results = []
    for i , q in enumerate(queries[:4]):
        try:
            raw = await query_cubejs(q)
            data = format_cubejs_response(raw)

            results.append({"query_index":i, "date": data[:30]})
        except Exception as e:
            results.append({"query_index":i, "error":str(e)}) 


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


    return {
        "findings": [AgentFinding(
            agent = "customer_feedback_analyst",
            summary = finding.get("summary",""),
            severity = finding.get("severity", "none"),
            metrics = finding.get("metrics",{}),
            evidence = finding.get("evidence",[])
        )]
    }