"""
RCA Guardrails - Shared utilities for all domain agents.

Tracks data quality per agent and prevents hallucination when queries fail or return empty results.

"""

from agents.state import AgentFinding

def _has_meaningful_data(row: dict) -> bool:
    """
    Return True only if at least one value in the row is non_None
    and non-zero (i.e., contains actual business data).

    """
    for val in row.values():
        if val is None:
            continue
        if isinstance(val,str):
            stripped = val.strip()
            if stripped in ("","0", "0.0","0.00"):
                continue
            return True
        if isinstance(val,(int,float)) and val != 0:
            return True
    return False
def compute_data_quality(results: list[dict]) -> tuple [str, int, int ]:
    """
    Analyzes query results and returns (quality_label, succeeded, failed).

    quality_label:
        "good" = at least half the queries returned non-empty data
        "partial" = some queries worked but most failed/empty
        "none" = all queries failed or returned empty data

    """

    if not results:
        return "none", 0,0
    
    succeeded = 0 
    failed = 0

    for r in results: 
        if "error" in r:
            failed += 1
        elif not r.get("data"):
            failed += 1
        elif len(r["data"]) == 0:
            failed += 1
        else:
            succeeded += 1

    if succeeded == 0:
        return "none", succeeded, failed
    elif succeeded >= len(results)/2:
        return "good", succeeded, failed
    else: 
        return "partial", succeeded, failed
    


def build_safe_finding(
        agent_name: str, 
        finding: dict,
        data_quality: str,
        queries_succeeded: int,
        queries_failed: int
) -> AgentFinding:
    """

    Build an AgentFinding with data quality metadata.
    If data quality is "none", override the summary to be transparent.
    """

    if data_quality == "none":
        return AgentFinding(
            agent = agent_name,
            summary = f"No usable data retrieved - all {queries_failed} queries failed or returned empty results.",
            severity= "none",
            metrics = {},
            evidence = [],
            data_quality = "none",
            queries_succeeded = 0,
            queries_failed = queries_failed,
        )
    
    

    return AgentFinding(
        agent = agent_name,
        summary = finding.get("summary", ""),
        severity= finding.get("severity",""),
        metrics = finding.get("metrics",{}),
        evidence = finding.get("evidence",[]),
        data_quality = data_quality,
        queries_succeeded = queries_succeeded,
        queries_failed = queries_failed,
    )