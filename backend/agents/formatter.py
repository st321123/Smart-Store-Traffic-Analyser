"""
Response Formatter - Agent #10

Formats the final response for both KPI and RCA paths.

KPI path: Takes the KPI agent's answer and polishes it.
RCA path: Takes ranked root causes and creates a structured report.
"""
import json 
import os 
from langchain_openai import AzureChatOpenAI
from agents.state import ChatState

llm = AzureChatOpenAI(
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key = os.getenv("AZURE_OPENAI_API_KEY"),
    api_version = os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature = 0
)

RCA_FORMAT_PROMPT = """ You are a retail analytics. Format the root cause
analysis results into a clear, professional response for the user.

USER QUESTION : {user_query}

ROOT CAUSES: (ranked):
{root_causes}

ANALYST FINDINGS: 
{findings}

FORMAT RULES: 

1. Start with a brief executive summary (2 - 3 sentences)
2. List root causes ranked by importance:
    - For each: cause name, severity, confidence, key evidence , recommendation
3. Use markdown formatting: bold headers bullet points, numbered lists
4. End with a "Recommended Actions" section with prioritized steps
5. Keep it concise but comprehensive - max 400 words
6. Use data-driven langauge with specific numbers form the evidence.
"""

async def formatter_node(state: ChatState) -> dict:
    intent = state.get("intent","")

    if intent == "kpi":
        return {}

    if intent in ("greeting","off_topic","uncler"):
        return {}
    
    root_causes = state.get("root_causes", [])
    findings = state.get("findings",[])

    if not root_causes and not findings:
        return {
    "response": "I wasn't able to find enough data to perform a root cause analysis. Could you provide more details about the store and time period?"
}
        
    

    response = await llm.ainvoke([
        {
            "role": "system",
            "content": RCA_FORMAT_PROMPT.format(
                user_query  = state["user_query"],
                root_causes = json.dumps(root_causes, indent = 2, default = str),
                findings = json.dumps(findings, indent = 2, default = str),
            )},

        {
            "role": "user",
            "content": "Format the root cause analysis report."
        },
    ])

    return {"response": response.content}