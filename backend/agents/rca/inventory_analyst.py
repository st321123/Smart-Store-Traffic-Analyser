"""
Inventory & Supply Analyst - RCA Domain Agent #4
Identifies stockouts, supply delays, and inventory risks.

CUBES: Inventory, InventoryRisk, PurchaseOrders, Shipments, Supplier
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

INVENTORY_PROMPT = """ You are a retail inventory and supply chain analyst performing root cause analysis.
AVAILABLE CUBES:
- Inventory: total_on_hand, total_reserved, total_damaged, available_stock, avg_on_hand, snapshot_count(measures)
  Dimensions: location_id, product_id, snapshot_date

- InventoryRisk:total_risk_flags, distinct_products_at_risk, distinct_locations_at_risk, avg_risk_quantity(measures)
  Dimensions: location_sk, product_id, risk_indicator, risk_level, trigger_date,current_quantity, recommended_action, escalation_status

- PurchaseOrders:total_po_amount, po_count, total_ordered_qty, total_received_qty,total_line_amount(measures)
  Dimensions:po_id, supplier_id, location_id, po_date, expected_delivery_date, po_status, product_id

- Shipments:total_shipped_qty, total_received_qty, total_shipment_cost, total_line_amount,total_weight, avg_line_unit_cost, shipment_count(measures)
  Dimensions:shipment_id, supplier_id, shipment_status, carrier_name, shipped_date, expected_delivery_date, delivered_date, product_id, sku_id
- Supplier: supplier_count(measures)
  Dimensions:supplier_id, supplier_name, supplier_type, contact_name, country_code, city, status_cd

USER QUESTION: {user_query}
ENTITIES: {entities}

STRICT RULES: 
- Only use the exact measure/dimension names listed above. Copy-paste them exactly.
- DO NOT invent measure names - only use what's listed.
- Never user filters with "operator": "beforeDate" or "values": ["now"] - this causes "invalid date" errors

DATE HANDLING (MANDATORY FORMAT):
Use timeDimensions with dateRange string. Example:
{{
    "measures": ["Inventory.total_on_hand"], "timeDimensions": [{{"dimension": "Inventory.snapshot_date","dateRange":"Last 30 days"}}]
    
}}
Valid dateRange values: "Last 7 days", "Last 30 days" , "Last 90 days", "Last year", "This month", "This year"


YOUR TASK:
1. Check for stockouts (low_on_hand)
2. Identify risk flags by risk_level
3. Check PO status and delivery dates
4. Look at shipment status
Generate 2-4 Cube.js queries as a JSON array.


"""

INVENTORY_ANALYSIS_PROMPT = """ You are a inventory analyst. Based on the data below, 
provide your finding for the root cause analysis.
USER QUESTION :{user_query}
DATA FROM QUERIES:
{query_results}

Respond in this JSON format:
{{
    "summary":"1-2 sentence summary of inventory/supply finding",
    "severity":"high|medium|low|none",
    "metrics":{{
              "oos_sku_count":0,
              "delayed_shipments":0,
              "fill_rate": 0,
              "risk_flags":0
                
                }},
    "evidence": ["specific data point 1", "specific data point 2"]

}}

"""


async def inventory_analyst_node(state: ChatState) -> dict:
    print("Running: Inventory Analyst Agent....")
    user_query = state["user_query"]
    entities = state.get("entities",{})

    query_response = await llm.ainvoke([
        {"role":"system", "content":INVENTORY_PROMPT.format(
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
            # print("query",q)
            raw = await query_cubejs(q)
            data = format_cubejs_response(raw)
            print("RESULT DATA", data[:5]) 
            results.append({"query_index":i, "data":data[:30]})
        except Exception as e:
            results.append({"query_index":i, "error":str(e)})

    analysis_response = await llm.ainvoke([
        {
            "role":"system",
            "content": INVENTORY_ANALYSIS_PROMPT.format(
                user_query = user_query,
                query_results = json.dumps(results, indent = 2)
            )
        },
        {
            "role":"user",
            "content": "Provide your inventory analysis finding."
        }])
    
   
    try:
        finding = json.loads(analysis_response.content)

    except json.JSONDecodeError:
        finding = {"summary": "Unable to analyse inventory data", "severity":"none","metrics":{}, "evidence":[]}
         

    return {
        "findings": [ AgentFinding(
            agent = "inventory_supply_analyst",
            summary = finding.get("summary",""),
            severity = finding.get("severity", "none"),
            metrics = finding.get("metrics",{}),
            evidence = finding.get("evidence",[])
        )

        ]
    }