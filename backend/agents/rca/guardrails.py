"""
RCA Guardrails - Shared utilities for all domain agents.

Tracks data quality per agent and prevents hallucination when queries fail or return empty results.

"""

from agents.state import AgentFinding

def _is_empty_value(val)->bool:
    """ Returns True if a value is None, empty,zero or zero-string """
    if val is None:
        return True
    if isinstance(val,str):
        stripped = val.strip()
        if stripped in ("","0","0.0","0.00"):
            return True
        try: 
            return float(stripped) == 0
        except ValueError:
            return False
        
    if isinstance(val,(int,float)):
        return val ==0
    return False

def _has_meaningful_data(row: dict) -> bool:
    """
    Returns True only if at least one value in the row is non-None
    and non-zero (i.e., contains actual business data).
    Dimension values (like location_id, store_id) don't count as evidence
    unless accompained by a real metric.

    """
    for key,val in row.items():
        if _is_empty_value(val):
            continue
        key_lower = key.lower()
        is_id_field = (key_lower.endswith("_id") or key_lower.endswith(".location_sk")
)
        if is_id_field :
            continue
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
            continue
        data = r.get('data')
        if not data or len(data) == 0:
            failed += 1
            continue
        has_real_data = any(_has_meaningful_data(row) for row in data)
        if has_real_data:
            succeeded += 1
        else : 
            failed += 1
    

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