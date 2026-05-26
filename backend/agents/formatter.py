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
DATA QUALITY SUMMARY: {data_quality_summary}
ROOT CAUSES: (ranked):
{root_causes}

ANALYST FINDINGS: 
{findings}

FORMAT RULES: 

1. Start with a brief executive summary (2 - 3 sentences)
2. List any agents had data_quality "none", add a "Data Gaps" section FIRST listing which domains had missing data
3. List root causes ranked by importance:
    - For each: cause_name, severity, confidence, key evidence, recommendation
    - If confidence is "low", explicitly note: "(low confidence - limited data)"
4. Use markdown formatting: bold headers, bullet points, numbered lists 
5. End with a "Recommended Actions" section with prioritized steps
6. Keep it concise but comprehensive - max 400 words
7. Use data-driven language with specific numbers from the evidence 
8. NEVEr present a cause as certain if its evidence came from a agent with data_quality "none"
"""

async def formatter_node(state: ChatState) -> dict:
    print("Running: Formatter Agent....")
    intent = state.get("intent","")

    if intent == "kpi":
        return {}

    if intent in ("greeting","off_topic","unclear"):
        return {}
    
    root_causes = state.get("root_causes", [])
    findings = state.get("findings",[])

    if not root_causes and not findings:
        return {
    "response": "I wasn't able to find enough data to perform a root cause analysis. Could you provide more details about the store and time period?"}

    quality_lines = []
    agents_with_no_data = []
    agents_with_data = []
    for f in findings:
        agent = f.get("agent", "unknown")
        quality = f.get("data_quality", "unknown")
        succeeded = f.get("queries_succeeded",0)
        failed = f.get("queries_failed",0)
        if quality == "none":
            quality_lines.append(f"{agent}: NO DATA ({failed} queries failed)")
            agents_with_no_data.append(agent)
        elif quality == "partial":
            quality_lines.append(f"{agent}: PARTIAL ({succeeded} ok, {failed} failed)")
        else:
            quality_lines.append(f"{agent}: Good ({succeeded} queries returned data)")
    
    data_quality_summary = "\n".join(quality_lines) if quality_lines else "No quality info available"

        
    disclaimer = ""
    
    if len(agents_with_no_data) >= 4:
        disclaimer =(
            "## Limited Data Availability \n \n"
            f"**{len(agents_with_no_data)} out of 6** analyst agent could not retrieve data" 
            "for requested period. The anlysis below is based on limited evidence "
            "and should be treated with low confidence. \n\n"
            f"**Data available from:** {', '.join(agents_with_data) if agents_with_data else 'None'}\n\n"
            f"**No data from:** {', '.join(agents_with_no_data)}\n\n"
        )

    response = await llm.ainvoke([
        {
            "role": "system",
            "content": RCA_FORMAT_PROMPT.format(
                user_query  = state["user_query"],
                data_quality_summary = data_quality_summary,
                root_causes = json.dumps(root_causes, indent = 2, default = str),
                findings = json.dumps(findings, indent = 2, default = str),
            )},

        {
            "role": "user",
            "content": "Format the root cause analysis report."
        },
    ])

    return {"response": disclaimer + response.content}