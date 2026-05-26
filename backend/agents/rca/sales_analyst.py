"""
Sales Analyst - RCA Domain Agent #2
Analyzes sales performance, conversion rates, basket size , returns.

CUBES: SalesDaily, POSTransactions, POSLineItems, Returns, Payments

"""


import json 
import os 
from langchain_openai import AzureChatOpenAI
from agents.state import ChatState
from tools.cubejs_client import query_cubejs, format_cubejs_response
from agents.rca.guardrails import compute_data_quality, build_safe_finding

llm = AzureChatOpenAI(
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key = os.getenv("AZURE_OPENAI_API_KEY"),
    api_version = os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature = 0
)

SALES_PROMPT = """ You are a retail sales analyst performing root cause analysis.

AVAILABLE CUBES:
- SalesDaily : total_sales, total_transactions, total_units_sold, avg_daily_sales(measures)
  Dimensions: location_id, sales_date

- POSTransactions: total_subtotal, total_discount, total_tax, total_amount, total_items,transaction_count, avg_transaction_value(measures)
  Dimensions: store_id, transaction_datetime, business_date, register_id, cashier_id, transaction_type, payment_method, status_cd

- POSLineItems: total_quantity, total_revenue, total_extended_price, total_discount, total_tax, avg_unit_price, avg_selling_price,line_count(measure)
  Dimensions:location_id, product_id, sku_id, barcode, product_description, created_dt, promo_id, uom_cd

- Returns: return_count, total_refund, avg_refund(measures)
  Dimensions: created_dt, return_reason_cd, return_channel_cd, return_status_cd, receiving_location_id

- Payments: total_payment, payment_count,avg_payment(measures)
  Dimensions: payment_method, payment_provider, payment_status, payment_datetime
  

USER QUESTION: {user_query}
ENTITIES: {entities}

STRICT RULES: 
- Only use the exact measure/dimension names listed above. Copy-paste them exactly.
- DO NOT invent measure names - only use what's listed.
- Never user filters with "operator": "beforeDate" or "values": ["now"] - this causes "invalid date" errors

DATE HANDLING (MANDATORY FORMAT):
Use timeDimensions with dateRange string. Example:
{{
    "measures": ["SalesDaily.total_sales"], "timeDimensions": [{{"dimension": "SalesDaily.sales_date","dateRange":"Last 30 days"}}]
    
}}
Valid dateRange values: "Last 7 days", "Last 30 days" , "Last 90 days", "Last year", "This month", "This year"


YOUR TASK:
1. Analyze sales volume and revenue trends
2. Check transaction counts and average values
3. Look at return rates
4. Identify payment method distribution

Generate 2-4 Cube.js queries as a JSON array.


"""

SALES_ANALYSIS_PROMPT = """ You are a sales analyst. Based on the data below, 
provide your finding for the root cause analysis.

USER QUESTION :{user_query}
DATA FROM QUERIES:
{query_results}

Respond in this JSON format:
{{
    "summary":"1-2 sentence summary of sales finding",
    "severity":"high|medium|low|none",
    "metrics":{{
              "conversion_rate":0,
              "avg_basket_size":0,
              "revenue_change_pct": 0,
              "return_rate":0
                
                }},
    "evidence": ["specific data point 1", "specific data point 2"]

}}

"""


async def sales_analyst_node(state: ChatState) -> dict:
    print("Running: Sales Analyst Agent....")
    user_query = state["user_query"]
    entities = state.get("entities",{})

    query_response = await llm.ainvoke([
        {"role":"system", "content":SALES_PROMPT.format(
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
    quality, succeeded, failed = compute_data_quality(results)
    print(f" Sales data quality : {quality} {succeeded}, {failed}")

    if quality == "none":
        return {"findings": [ build_safe_finding("sales_analyst",{}, quality, succeeded, failed)]}
    analysis_response = await llm.ainvoke([
        {
            "role":"system",
            "content": SALES_ANALYSIS_PROMPT.format(
                user_query = user_query,
                query_results = json.dumps(results, indent = 2)
            )
        },
        {
            "role":"user",
            "content": "Provide your sales analysis finding."
        }])
    
   
    try:
        finding = json.loads(analysis_response.content)

    except json.JSONDecodeError:
        finding = {"summary": "Unable to analyse sales data", "severity":"none","metrics":{}, "evidence":[]}
         

    return {
        "findings": [ build_safe_finding("sales_analyst",finding,quality,succeeded, failed)]}