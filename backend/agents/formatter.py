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

RCA_FORMAT_PROMPT = """Format these root causes into a brief report.

USER QUESTION : {user_query}

ROOT CAUSES:
{root_causes}

RULES:
- Use the exact numbers from the evidence fields - do not paraphrase
- Use "may", "potentially", "possible" - never definitive langauge
- Do NOT add causes that aren't in the ROOT CAUSES list
- Do NOT mention promotions, pricing, or any domain not in the root causes
- Keep it under 200 words
- For each cause: state the finding, the evidence number, and a recommendation
"""

def _build_code_header(findings: list, root_causes: list)-> str:
    """
    Builds the response header entirely in Python code.
    This section is immune to LLM hallucination.
    """
    lines = []
    lines.append("# Data Availability\n")
    for f in findings:
        agent = f.get("agent", "unknown")
        quality = f.get("data_quality", "none")
        succeeded = f.get("queries_succeeded",0)
        failed = f.get("queries_failed",0)
        label = agent.replace("_", " ").title()
        if quality == "none":
            lines.append(f"**{label}**: NO data retrieved ({failed} queries failed)")
        elif quality == "partial":
            lines.append(f"{label}: Partial data ({succeeded} ok, {failed} failed)")
        else:
            lines.append(f"{label}: Data available ({succeeded} queries succeeded)")
    
    lines.append("\n## Actual Metrics Retrieved\n")
    has_metrics = False
    for f in findings: 
        if f.get("data_quality") == "none":
            continue
        agent = f.get("agent","unknown").replace("_"," ").title()
        metrics = f.get("metrics",{})
        evidence = f.get("evidence", [])
        
        if metrics:
            for key, val in metrics.items():
                if val is not None and val != 0 and val != "0":
                    lines.append(f"- **{key}**: {val} * (from) {agent}")
                    has_metrics = True
        if evidence :
            for e in evidence:
                if e and "non" not in e.lower()[:10] and "none" not in e.lower()[:10]:
                    lines.append(f"- {e} *(from {agent})*")
                    has_metrics = True
    if not has_metrics:
        lines.append("- No specific metrics were retrieved from any agent.")

    if root_causes:
        confidence = root_causes[0].get("confidence", "low") if root_causes else "low"
        lines.append(f"\n** Overall Confidence: {confidence.upper()} **\n")

    lines.append("\n--\n")
    return "\n".join(lines)

async def formatter_node(state: ChatState) -> dict:
    print("Running: Formatter Agent....")
    intent = state.get("intent","")

    if intent == "kpi":
        return {}

    if intent in ("greeting","off_topic","unclear"):
        return {}
    
    root_causes = state.get("root_causes", [])
    findings = state.get("findings",[])

    if state.get("response") and not root_causes:
        return {}
    
    
    if not root_causes and not findings:
        return {
    "response": "I wasn't able to find enough data to perform a root cause analysis. Could you provide more details about the store and time period?"}

    code_header = _build_code_header(findings,root_causes)
    if not root_causes:
        return {"response": code_header + "\nNo root causes could be identified from the available data."}


    response = await llm.ainvoke([
        {
            "role": "system",
            "content": RCA_FORMAT_PROMPT.format(
                user_query  = state["user_query"],
                root_causes = json.dumps(root_causes, indent = 2, default = str),
                
            )},

        {
            "role": "user",
            "content": "Format the root cause analysis.",
        },
    ])

    return {"response": code_header + response.content}