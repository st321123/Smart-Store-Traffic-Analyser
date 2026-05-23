# This is the first agent that runs for every user query. It has 2 jobs:
    # Classify intent - What does user want?
    # Extract entities - What specifcs did they mention?



"""
Supervisor Agent -  the entry point for evey user query
Classifies intent, extract entities, and routes to the correct path.

FLOW: User query -> Supervisor -> routes to KPI Agent or RCA Agents
"""

import json 
from langchain_openai import AzureChatOpenAI
from agents.state import ChatState
import os 

llm = AzureChatOpenAI(
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key = os.getenv("AZURE_OPENAI_API_KEY"),
    api_version = os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature = 0)

SUPERVISOR_PROMT = """You are a retail analytics assistant supervisor.

Your job is to:
    1. Classify the user's intent.
    2. Extract relevant entities from the query.

INTENT CLASSIFICATION:
- "greeting": -> user is saying hi, hello, good morning, etc.
- "kpi": user -> wants a number, metric, comparison, trend, ranking.
    This includes ANY question about: sales, traffic, revenue, inventory, promotions, returns, payments, customers,
    feedback, ratings, events, stores, products, shipments.
    Examples: -> "What is total sales?", "Top 5 products"< "Sales trend for March", "How many returns".

- "rca": -> user wants to understand WHY something happened or want root cause analysis.
    Examples: -> "Why did traffic drop?", "What caused sales decline", "Analyze the drop"
- "off_topic: -> question is not related to store analytics
- "unclear": -> not enough into understand what user wants

IMPORTANT : When in doubt between "kpi" and "unclear" always choose "kpi".
ENTITY EXTRACTION: 
Extract any of these if mentioned:
- store_id: store or location ID (e.g., "LOC_001", "Store 1 ")
- date_range: time period (e.g. "March 2024", "last_week", "Q1")
- metric: what metric they care about (e.g. "sales", "traffic", "revenue")
- region: geographic area (e.g. "South", "Chennai")
- product: product or category (e.g. "Electronics", "Nike")


RESPOND IN THIS EXACT JSON FORMAT:
{
    "intent": "greeting|kpi|rca|off_topic|unclear",
    "entities: {
            "store_id": null,
            "date_range": null,
            "metric": null,
            "region": null,
            "product": null
    },
    "greeting_response":" only if intent is greeting, write a friendly response"

}

 """


# supervisor_node : LangGraph node function
# Takes teh current state, classifies intent, extracts entities, 
# and writes them back to state. The graph then routes bases on the 
# intent.


async def supervisor_node(state: ChatState)->dict:
    print("Running: Supervisor Agent....")
    user_query = state["user_query"]

    response = await llm.ainvoke([
        {"role":"system","content": SUPERVISOR_PROMT},
        {"role":"user", "content": user_query}
    ])

    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        result = {"intent":"unclear", "entities":{}}

    intent = result.get("intent","unclear")

    if intent == "greeting":
        return {
            "intent":"greeting",
            "entities":{},
            "response": result.get("greeting_response","Hello! I can help you with store analytics. Ask me about sales, traffic, inventory, or why something changed"),
    
        }
    
    if intent == "off_topic":
         return {
            "intent":"off_topic",
            "entities":{},
            "response": "I'm a store analytics assistant. I can help with sales, traffic, inventory, promotions, and root cause analysis. Please ask me something realted to store performance.",

    
        }

    return {
        "intent": intent,
        "entities": result.get("entities",{}),
    }