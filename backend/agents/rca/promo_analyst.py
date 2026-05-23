"""
Promo & Pricing Analyst - RCA Domain Agent #3
Evaluates promotional activity and pricing impact on traffic.

CUBES: Promotions, Pricing, Product

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

PROMO_PROMPT = """ You are a retail promotions and pricing analyst performing root cause analysis.

AVAILABLE CUBES:
- Promotions: promo_count, avg_discount_pct, products_on_promo (measures)
  Dimensions: promo_mapping_id, promo_id, promo_name, promo_type, start_date, end_date,discount_pct, product_id

- Pricing: avg_regular_price, avg_selling_price, max_regular_price, min_selling_price, total_price_records(measures)
  Dimensions: product_id, location_id, effective_start_dt, effective_end_dt

- Product: product_count(measures)
  Dimensions:product_id, product_name, brand_name, sku_id, department_name, category_name, subcategory_name, status_cd



USER QUESTION: {user_query}
ENTITIES: {entities}

STRICT RULES: 
- Only use the exact measure/dimension names listed above. Copy-paste them exactly.
- DO NOT invent measure names - only use what's listed.
- Never user filters with "operator": "beforeDate" or "values": ["now"] - this causes "invalid date" errors

DATE HANDLING (MANDATORY FORMAT):
Use timeDimensions with dateRange string. Example:
{{
    "measures": ["Promotions.promo_count"], "timeDimensions": [{{"dimension": "Promotions.start_date","dateRange":"Last 30 days"}}]
    
}}
Valid dateRange values: "Last 7 days", "Last 30 days" , "Last 90 days", "Last year", "This month", "This year"



YOUR TASK:
1. Check active promotions and discount levels
2. Look at pricing (regular vs selling price)
3. Check products on promo
Generate 2-4 Cube.js queries as a JSON array.


"""

PROMO_ANALYSIS_PROMPT = """ You are a promotions analyst. Based on the data below, 
provide your finding for the root cause analysis.

USER QUESTION :{user_query}
DATA FROM QUERIES:
{query_results}

Respond in this JSON format:
{{
    "summary":"1-2 sentence summary of promo/pricing finding",
    "severity":"high|medium|low|none",
    "metrics":{{
              "current_promos":0,
              "prior_promos":0,
              "promo_lift": 0,
              "price_changes":0
                
                }},
    "evidence": ["specific data point 1", "specific data point 2"]

}}

"""


async def promo_analyst_node(state: ChatState) -> dict:
    print("Running: Promo Analyst Agent....")
    user_query = state["user_query"]
    entities = state.get("entities",{})

    query_response = await llm.ainvoke([
        {"role":"system", "content":PROMO_PROMPT.format(
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
            # print("QUERY",q)
            raw = await query_cubejs(q)
            data = format_cubejs_response(raw)
            print("RESULT DATA", data[:5])
            results.append({"query_index":i, "data":data[:30]})
        except Exception as e:
            results.append({"query_index":i, "error":str(e)})

    analysis_response = await llm.ainvoke([
        {
            "role":"system",
            "content": PROMO_ANALYSIS_PROMPT.format(
                user_query = user_query,
                query_results = json.dumps(results, indent = 2)
            )
        },
        {
            "role":"user",
            "content": "Provide your promo/pricing analysis finding."
        }])
    
   
    try:
        finding = json.loads(analysis_response.content)

    except json.JSONDecodeError:
        finding = {"summary": "Unable to analyse promo data", "severity":"none","metrics":{}, "evidence":[]}
         

    return {
        "findings": [ AgentFinding(
            agent = "promo_pricing_analyst",
            summary = finding.get("summary",""),
            severity = finding.get("severity", "none"),
            metrics = finding.get("metrics",{}),
            evidence = finding.get("evidence",[])
        )

        ]
    }