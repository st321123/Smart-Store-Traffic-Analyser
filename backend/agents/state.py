# state.py file is for type check 


"""
Shared state that gets passed between all agents in the LangGraph pipeline.
Every agent reads from this state and writes back to it.
"""

from typing import TypedDict, Annotated
from operator import add





# -----------------------------------------------------------------------------------
# AgentFinding: Each RCA domain agent produces one of these.
# It contains the agent's analysis summary, severity and evidence.
# -----------------------------------------------------------------------------------

class AgentFinding(TypedDict):

    agent: str
    summary: str
    severity: str # "high","medium, "Low","none"
    metrics: dict
    evidence: list[str]



# -----------------------------------------------------------------------------------
# RankedCauses: The Synthesizer produces a ranked list of these after analyzing
#  all agent findings.
# -----------------------------------------------------------------------------------



class RankedCause(TypedDict):
    rank:int
    cause:str
    category:str # "traffic", "sales","inventory",
    severity: str
    confidence:str # "high","medium", "low"
    evidence:list[str]
    recommendation: str



# -----------------------------------------------------------------------------------
# ChatState: The main state object passed through the entire LangGraph pipeline. Every
# agent reads and writes to this.
# Flow:
#     User query comes in  -> Supervisor files intent + entities
#         -> KPI Agent or RCA Agents fill findings.
#         -> Synthesizer fills root_causes (RCA only)
#         -> Response is generated
# -----------------------------------------------------------------------------------

class ChatState(TypedDict):
    user_query: str
    intent: str
    entities: str
    cube_metadata:str
    findings: Annotated[list[AgentFinding],add]
    root_causes: list[RankedCause]
    response: str