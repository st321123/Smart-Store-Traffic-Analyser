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

SUPERVISOR_PROMT = """You are something """
async def supervisor_node(state: ChatState)->dict:
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

    if intent == "greeeting":
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