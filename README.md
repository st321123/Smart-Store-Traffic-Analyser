# Retail Traffic Root Cause Analyzer

AI-powered analytics system that enables **natural language queries to analyze retail foot traffic trends and store performance**.  
The system uses a **multi-agent LLM architecture** to generate analytical queries, retrieve data, and produce human-readable insights explaining traffic patterns and potential root causes.

---

## Tech Stack

- Python
- LangGraph
- LangChain
- Azure OpenAI
- Cube.js
- MySQL / PostgreSQL
- Pydantic~
- Next.js

---

## Overview

Retail teams often struggle to quickly understand **why store traffic changes across locations, time periods, or promotions**.

This project solves that problem by allowing users to **ask questions in natural language**, such as:

- Why did store traffic drop last weekend?
- Which stores had the highest footfall growth?
- What factors affected traffic in a specific region?
- How did weather impact store visits?

The system translates these questions into **analytical queries**, retrieves the required data, and generates **clear explanations and insights** with root cause identification.

---

## Architecture

The system uses a **multi-agent pipeline built with LangGraph** consisting of 19 specialized agents working in parallel for root cause analysis.

### Core Agents

| Agent | Responsibility |
|-------|----------------|
| **Query Understanding Agent** | Interprets natural language, extracts entities (store, time period, metric) |
| **Intent Classification Agent** | Determines if query is simple KPI or requires root cause analysis |
| **Semantic Layer Query Agent** | Generates and executes Cube.js queries |
| **Time Series Builder Agent** | Creates aligned time-series dataset for analysis |
| **Traffic Trend Analysis Agent** | Detects anomalies and calculates week-over-week changes |
| **Factor Investigation Agents (10)** | Analyze weather, promotions, pricing, inventory, sales, products, customers, returns, operations, external events |
| **Correlation Engine Agent** | Calculates correlations between traffic and all factors |
| **Root Cause Detection Agent** | Ranks drivers and identifies primary/secondary causes |
| **GenAI Explanation Agent** | Generates human-readable business insights with recommendations |


---

## Key Features

- Natural language interface for retail analytics
- Multi-agent LLM architecture (19 specialized agents)
- Metadata-driven query planning with Cube.js
- **Root cause analysis** across 10 dimensions
- **Parallel agent execution** for fast insights
- **Correlation analysis** to identify strongest drivers
- **GenAI explanations** with actionable recommendations
- Support for 14 retail KPIs (traffic, sales, conversion, inventory, promotions)

---

## Data Model

The system integrates **16 tables** across key retail domains:

| Domain | Tables |
|--------|--------|
| Traffic | store_traffic_counts |
| Sales | sales_daily_summary, pos_line_items |
| Promotions | promo_header, promo_item_mapping |
| Pricing | price_master |
| Inventory | inventory_snapshot, inventory_risk_flags, inventory_balance_ledger |
| Product | product_master, product_hierarchy |
| Customer | customer_master |
| Returns | return_header |
| Store | location_master, store_external_events |
| Time | calendar_dim |

All tables are exposed through **Cube.js semantic layer** for consistent metric definitions.

---

## Workflow

1. User asks a question about store traffic
2. **Query Understanding Agent** extracts entities and intent
3. **Intent Classification Agent** routes to KPI or RCA path
4. **Semantic Layer Query Agent** generates Cube.js queries
5. Queries execute against MySQL/PostgreSQL
6. **Time Series Builder Agent** creates aligned dataset
7. **10 Factor Investigation Agents** run in parallel
8. **Correlation Engine Agent** identifies strongest relationships
9. **Root Cause Detection Agent** ranks potential drivers
10. **GenAI Explanation Agent** generates human-readable insights

---

## Example Query

**User Input**

> Why did foot traffic drop in Store A last week?

**System Output**

```
Store traffic decreased by 18% last week compared to the previous week.

The primary driver was heavy rainfall during the weekend which significantly
reduced customer visits. Rainfall of 2.5 inches over Saturday and Sunday
coincided with a 40% reduction in foot traffic during those hours.

Additionally, a promotional campaign that was driving foot traffic ended on
Friday. The "Summer Sale" promotion had been boosting traffic by 15% while
active; its conclusion contributed to the overall decline.

As a result, store sales also declined by 12% with 245 fewer transactions
compared to the previous week.

💡 Recommendation: Consider extending promotional campaigns during unfavorable
   weather periods to maintain traffic momentum.
```

---

## Project Structure

```
retail-traffic-analyzer/
├── agents/
│   ├── query_understanding.py
│   ├── intent_classification.py
│   ├── semantic_layer_query.py
│   ├── time_series_builder.py
│   ├── traffic_trend_analysis.py
│   ├── factor_agents/
│   │   ├── weather_agent.py
│   │   ├── promotion_agent.py
│   │   ├── pricing_agent.py
│   │   ├── inventory_agent.py
│   │   ├── sales_agent.py
│   │   ├── product_agent.py
│   │   ├── customer_agent.py
│   │   ├── returns_agent.py
│   │   ├── store_operations_agent.py
│   │   └── external_events_agent.py
│   ├── correlation_engine.py
│   ├── root_cause_detection.py
│   └── genai_explanation.py
├── cubes/
│   └── cube_schemas/
├── models/
│   └── kpi_definitions.py
├── utils/
├── config.py
├── main.py
└── README.md
```

---

## Environment Variables

```env
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_KEY=your_key
AZURE_OPENAI_DEPLOYMENT=your_deployment
CUBEJS_API_URL=your_cube_url
CUBEJS_API_TOKEN=your_cube_token
DATABASE_URL=mysql://user:pass@host:3306/db
```

---

## Installation

```bash
# Clone repository
git clone https://github.com/yourusername/retail-traffic-analyzer.git
cd retail-traffic-analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials

# Run the application
python main.py
```

---

## Supported KPIs

| KPI | Description |
|-----|-------------|
| Total Store Traffic | Sum of unique visitors |
| Daily/Weekly Store Traffic | Traffic aggregated by day or week |
| Traffic Growth Rate | Percentage change vs previous period |
| Total Sales | Sum of net sales |
| Total Transactions | Count of completed transactions |
| Conversion Rate | Transactions / Unique visitors |
| Average Basket Value | Net sales / Transactions |
| Sales Per Visitor | Net sales / Unique visitors |
| Promotion Traffic Impact | Traffic during active promotions |
| Promotion Sales Impact | Sales during active promotions |
| Stockout Rate | Percentage of products out of stock |
| Inventory Availability | Percentage of products in stock |
| Traffic During Weather Events | Traffic when weather events occur |
| Traffic During Local Events | Traffic during festivals, rallies, etc. |

---

## Future Improvements

- Automated anomaly detection and alerts
- Visual dashboards for insights
- Integration with additional retail data sources
- Real-time traffic monitoring
- Traffic forecasting models
- Mobile app for store managers

---
