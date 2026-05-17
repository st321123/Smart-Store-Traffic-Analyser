"""
LangGraph Pipeline - Orchestrates all agent.

Two execution paths :
    KPI: Supervisor -> KPI Agent -> Formatter -> END
    RCA: Supervisor -> [6 analysts in parallel] -> Synthesizer -> Formatter -> END

Also handles: greeting, off_topic, unclear -> direct response from Supervisor
"""


from langgraph.graph import StateGraph, END

from agents.state import ChatState
from agents.supervisor import supervisor_node
from agents.kpi_agent import kpi_node
from agents.synthesizer import synthesizer_node
from agents.formatter import formatter_node
from agents.rca.traffic_analyst import traffic_analyst_node
from agents.rca.sales_analyst import sales_analyst_node
from agents.rca.promo_analyst import promo_analyst_node
from agents.rca.inventory_analyst import inventory_analyst_node
from agents.rca.customer_analyst import customer_analyst_node
from agents.rca.external_analyst import external_analyst_node


# ------------------------------------------------------------------
# ROUTING FUNCTION
# After the Supervisor classifies intent, this function decides
# which path to take in the graph
# ----------------------------------------------------------------- 


def route_after_supervisor(state: ChatState) -> str:
    intent = state.get("intent", "unclear")

    if intent == "kpi":
        return "kpi_agent"
    elif intent == "rca":
        return "rca_analysts"
    else:
        return "formatter"
    

# -----------------------------------------------------------------------

# BUILD THE GRAPH 

# -----------------------------------------------------------------------


def build_graph():
    graph = StateGraph(ChatState)

    # Add all nodes 

    graph.add_node("supervisor",supervisor_node)
    graph.add_node("kpi_agent", kpi_node)
    graph.add_node("traffic_analyst", traffic_analyst_node)
    graph.add_node("sales_analyst",sales_analyst_node)
    graph.add_node("promo_analyst",promo_analyst_node)
    graph.add_node("inventory_analyst",inventory_analyst_node)
    graph.add_node("customer_analyst",customer_analyst_node)
    graph.add_node("external_analyst",external_analyst_node)
    graph.add_node("synthesizer", synthesizer_node)
    graph.add_node("formatter",formatter_node)



    # ------Entry Point-------------
    graph.set_entry_point("supervisor")

    #----- Supervisor routes to KPI, RCA, or direct response -------
    graph.add_conditional_edges("supervisor", route_after_supervisor, {
        "kpi_agent":"kpi_agent",
        "rca_analysts":"traffic_analyst",
        "formatter": "formatter",
    })


    # ---- KPI path --------------------
    graph.add_edge("kpi_agent","formatter")


    # RCA PATH: 6 analysts run sequentially (LangGraph fan-out) ----
    # Traffic -> Sales -> Promo -> Inventory -> Customer -> External -> Synthesizer
    # Each appends its finding to state.findings via the Annotated[List, add] reducer


    graph.add_edge("traffic_analyst","sales_analyst")
    graph.add_edge("sales_analyst","promo_analyst")
    graph.add_edge("promo_analyst","inventory_analyst")
    graph.add_edge("inventory_analyst", "customer_analyst")
    graph.add_edge("customer_analyst","external_analyst")
    graph.add_edge("external_analyst","synthesizer")

    # ----- Synthesizer -> Formatter -> END -------
    graph.add_edge("synthesizer", "formatter")
    graph.add_edge("formatter",END)

    return graph.compile()



# Pre-built compiled graph ready to use
app_graph = build_graph()
