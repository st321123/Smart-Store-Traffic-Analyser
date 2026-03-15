# Retail Traffic Root Cause Analyzer

AI-powered analytics system that enables **natural language queries to analyze retail foot traffic trends and store performance**.  
The system uses a **multi-agent LLM architecture** to generate analytical queries, retrieve data, and produce human-readable insights explaining traffic patterns and potential root causes.

---

# Tech Stack

- Python
- LangGraph
- LangChain
- Azure OpenAI
- Cube.js
- MySQL
- Pydantic
- Next.js

---

# Overview

Retail teams often struggle to quickly understand **why store traffic changes across locations, time periods, or promotions**.

This project solves that problem by allowing users to **ask questions in natural language**, such as:

- Why did store traffic drop last weekend?
- Which stores had the highest footfall growth?
- What factors affected traffic in a specific region?

The system translates these questions into **analytical queries**, retrieves the required data, and generates **clear explanations and insights**.

---

# Architecture

The system uses a **multi-agent pipeline built with LangGraph**.

### Agents

**1. Planner Agent**
- Understands the user query
- Breaks the problem into analytical steps

**2. Query Builder Agent**
- Uses Cube.js semantic metadata
- Generates structured analytical queries

**3. Reasoner Agent**
- Interprets query results
- Identifies patterns and possible root causes

**4. Summary Agent**
- Converts analytical findings into **human-readable insights**

---

# Key Features

- Natural language interface for retail analytics
- Multi-agent LLM architecture
- Metadata-driven query planning
- Integration with Cube.js semantic layer
- Root cause explanations for traffic trends
- Human-readable analytical insights

---

# Workflow

1. User asks a question about store traffic.
2. The **Planner Agent** analyzes the query.
3. The **Query Builder Agent** generates analytical queries.
4. Queries are executed using **Cube.js and MySQL**.
5. The **Reasoner Agent** analyzes the results.
6. The **Summary Agent** generates insights explaining the trends.

---

# Example Query

**User Input**

> Why did foot traffic drop in Store A last week?

**System Output**

- Traffic dropped by **18% compared to the previous week**
- Weekend traffic declined significantly
- A competing store opened nearby during the same period
- Promotional campaign ended on Friday

---

# Future Improvements

- Automated anomaly detection
- Visual dashboards for insights
- Integration with additional retail data sources
- Real-time traffic monitoring
