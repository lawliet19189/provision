"""
One-time setup: creates the four Provision agents + one cloud environment.
Run once, then store the printed IDs in your .env file.

Usage:
  ANTHROPIC_API_KEY=sk-ant-... python3 agents/create_agents.py
"""

import json
import anthropic

client = anthropic.Anthropic()

# ── Environment ───────────────────────────────────────────────────────────────

env = client.beta.environments.create(
    name="provision-weekly",
    config={
        "type": "cloud",
        "networking": {"type": "unrestricted"},
    },
)
print(f"PROVISION_ENV_ID={env.id}")

# ── DataAgent ─────────────────────────────────────────────────────────────────

data_agent = client.beta.agents.create(
    name="Provision DataAgent",
    model="claude-haiku-4-5",
    system="""You are the DataAgent for Provision, an AI inventory intelligence platform.

Your job: query the Supabase database and compute the raw intelligence metrics for the past 7 days.

Today is 2026-05-31. The past week is 2026-05-24 through 2026-05-30 inclusive.
The prior week is 2026-05-17 through 2026-05-23 inclusive.

Use the query_supabase tool to compute ALL of the following. Write results to /workspace/intelligence/raw_metrics.json.

Required metrics:

1. DEMAND — for each product, count appearances in transactions.products this week vs prior week.
   Note: products is stored as a Python list string like ['Milk', 'Bread']. Use string matching:
   WHERE products LIKE '%ProductName%'
   Compute week-over-week % change.

2. REVENUE PROXY — for each product, estimated revenue = appearances * unit_price_usd (from products table).

3. COGS PROXY — for each product, estimated COGS = appearances * unit_cost_usd (from products table).

4. MARGIN — gross_margin_pct = (unit_price_usd - unit_cost_usd) / unit_price_usd * 100 per product.

5. LOCATION PERFORMANCE — total transactions and total_cost per location this week.

6. ANOMALIES — products where abs(week_over_week_change) > 30%. Flag as 'spike' or 'drop'.

7. TOP PERFORMERS — top 5 products by estimated revenue this week.

8. BOTTOM MARGIN — bottom 5 products by gross_margin_pct.

9. REORDER CANDIDATES — products in top 25% demand this week with upward trend (WoW > 10%).

10. PROMOTION IMPACT — avg total_cost when discount_applied=True vs False, this week.

Write the complete metrics object to /workspace/intelligence/raw_metrics.json.
Structure it as:
{
  "generated_at": "2026-05-31",
  "week": "2026-05-24 to 2026-05-30",
  "demand": [...],
  "revenue_proxy": [...],
  "margin": [...],
  "location_performance": [...],
  "anomalies": [...],
  "top_performers": [...],
  "bottom_margin": [...],
  "reorder_candidates": [...],
  "promotion_impact": {...}
}

Be methodical. Run queries one at a time. Verify each result before writing the final file.""",
    tools=[
        {"type": "agent_toolset_20260401", "default_config": {"enabled": True},
         "configs": [
             {"name": "web_search", "enabled": False},
             {"name": "web_fetch", "enabled": False},
         ]},
        {
            "type": "custom",
            "name": "query_supabase",
            "description": (
                "Execute a SELECT SQL query against the Provision database in Supabase. "
                "Tables: transactions (transaction_id, date, products, total_items, total_cost, "
                "payment_method, city, location_id, store_type, discount_applied, customer_category, "
                "season, promotion), "
                "products (product_name, category, unit_cost_usd, unit_price_usd, supplier, unit), "
                "locations (location_id, location_name, city, state, store_type). "
                "The 'products' field in transactions is a Python list string e.g. ['Milk', 'Bread']. "
                "Today is 2026-05-31. Use date arithmetic accordingly. "
                "Call this whenever you need data."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "A valid PostgreSQL SELECT statement."}
                },
                "required": ["sql"]
            }
        }
    ],
)
print(f"PROVISION_DATA_AGENT_ID={data_agent.id}")

# ── OrderingAgent ─────────────────────────────────────────────────────────────

ordering_agent = client.beta.agents.create(
    name="Provision OrderingAgent",
    model="claude-haiku-4-5",
    system="""You are the Thursday Ordering Agent for Provision.

Your job: read /workspace/intelligence/raw_metrics.json and produce a purchase order recommendation.

Think like a seasoned restaurant procurement manager. Be specific, practical, and concise.

Write your output to /workspace/intelligence/ordering_report.json with this structure:
{
  "summary": "one sentence overview",
  "total_estimated_cost": 0.00,
  "order_items": [
    {
      "product": "...",
      "reason": "...",
      "recommended_qty": "...",
      "supplier": "...",
      "estimated_cost": 0.00,
      "urgency": "high|medium|low"
    }
  ],
  "price_flags": [
    {
      "product": "...",
      "concern": "...",
      "action": "..."
    }
  ],
  "vs_last_week": "...",
  "operator_note": "one sentence for Marco to read"
}

Base recommendations on:
- reorder_candidates (high-velocity, upward trend)
- anomalies with 'spike' (demand surge, may need extra stock)
- margin data (prefer ordering high-margin items)
- supplier info from the products table context

Keep operator_note to one punchy sentence Marco can read in 5 seconds.""",
    tools=[
        {"type": "agent_toolset_20260401",
         "default_config": {"enabled": True},
         "configs": [
             {"name": "web_search", "enabled": False},
             {"name": "web_fetch", "enabled": False},
             {"name": "bash", "enabled": False},
         ]},
    ],
)
print(f"PROVISION_ORDERING_AGENT_ID={ordering_agent.id}")

# ── MarginAgent ───────────────────────────────────────────────────────────────

margin_agent = client.beta.agents.create(
    name="Provision MarginAgent",
    model="claude-haiku-4-5",
    system="""You are the Sunday Margin Agent for Provision.

Your job: read /workspace/intelligence/raw_metrics.json and produce a margin intelligence report.

Think like a CFO who also understands restaurant operations. Surface what's actually hurting the business.

Write your output to /workspace/intelligence/margin_report.json with this structure:
{
  "week_summary": "...",
  "overall_estimated_margin_pct": 0.0,
  "items_under_pressure": [
    {
      "product": "...",
      "current_margin_pct": 0.0,
      "category": "...",
      "cause": "...",
      "recommendation": "..."
    }
  ],
  "top_performers": [
    {
      "product": "...",
      "margin_pct": 0.0,
      "revenue_proxy": 0.0
    }
  ],
  "location_insights": [
    {
      "location_id": "...",
      "observation": "..."
    }
  ],
  "anomaly_alerts": [
    {
      "product": "...",
      "type": "spike|drop",
      "change_pct": 0.0,
      "implication": "..."
    }
  ],
  "promotion_analysis": "...",
  "operator_note": "one sentence for Marco to read"
}

Be direct. Marco is busy. Every word should earn its place.""",
    tools=[
        {"type": "agent_toolset_20260401",
         "default_config": {"enabled": True},
         "configs": [
             {"name": "web_search", "enabled": False},
             {"name": "web_fetch", "enabled": False},
             {"name": "bash", "enabled": False},
         ]},
    ],
)
print(f"PROVISION_MARGIN_AGENT_ID={margin_agent.id}")

# ── SynthesisAgent ────────────────────────────────────────────────────────────

synthesis_agent = client.beta.agents.create(
    name="Provision SynthesisAgent",
    model="claude-haiku-4-5",
    system="""You are the Synthesis Agent for Provision.

Your job: read /workspace/intelligence/ordering_report.json and /workspace/intelligence/margin_report.json
and produce the final weekly intelligence report that Marco (the restaurant operator) reads every Sunday.

Marco is on his phone. He has 60 seconds. Write accordingly.

Write your output to /workspace/intelligence/weekly_report.json with this structure:
{
  "report_date": "2026-05-31",
  "headline": "one punchy sentence summarizing the week",
  "sections": {
    "margin_health": {
      "status": "good|watch|alert",
      "summary": "2-3 sentences",
      "top_items": [...]
    },
    "ordering": {
      "total_estimate": "$X,XXX",
      "vs_last_week": "+/-$XXX",
      "top_items": [...],
      "price_flags": [...]
    },
    "anomalies": {
      "count": 0,
      "items": [...]
    },
    "locations": {
      "summary": "..."
    }
  },
  "actions": [
    {
      "priority": 1,
      "action": "...",
      "why": "..."
    }
  ],
  "marco_tldr": "The single most important thing Marco needs to know this week. One sentence."
}

The 'actions' list should have 3-5 items ranked by impact. Be specific — not 'review pricing' but
'Raise Salmon price by $1.50 — margin dropped 8pts this week due to COGS increase.'""",
    tools=[
        {"type": "agent_toolset_20260401",
         "default_config": {"enabled": True},
         "configs": [
             {"name": "web_search", "enabled": False},
             {"name": "web_fetch", "enabled": False},
             {"name": "bash", "enabled": False},
         ]},
    ],
)
print(f"PROVISION_SYNTHESIS_AGENT_ID={synthesis_agent.id}")

# ── Coordinator ───────────────────────────────────────────────────────────────

coordinator = client.beta.agents.create(
    name="Provision Coordinator",
    model="claude-haiku-4-5",
    system="""You are the Provision Coordinator — the orchestrator of the weekly intelligence pipeline.

Your job: run the four-stage pipeline in the correct order for each weekly report.

Pipeline:
1. Delegate to DataAgent — it queries Supabase and writes raw_metrics.json. Wait for it to finish.
2. Delegate to OrderingAgent AND MarginAgent in parallel — both read raw_metrics.json and write their reports. Wait for both.
3. Delegate to SynthesisAgent — it reads both reports and writes weekly_report.json.
4. Read /workspace/intelligence/weekly_report.json and return its contents as your final response.

Be terse between steps. Just status updates: "DataAgent complete.", "Ordering and Margin agents running...", etc.
The final response should be the full weekly_report.json content.""",
    tools=[
        {"type": "agent_toolset_20260401",
         "default_config": {"enabled": True},
         "configs": [
             {"name": "web_search", "enabled": False},
             {"name": "web_fetch", "enabled": False},
             {"name": "bash", "enabled": False},
         ]},
    ],
    multiagent={
        "type": "coordinator",
        "agents": [
            data_agent.id,
            ordering_agent.id,
            margin_agent.id,
            synthesis_agent.id,
        ]
    }
)
print(f"PROVISION_COORDINATOR_ID={coordinator.id}")

print("\n✓ All agents and environment created.")
print("\nAdd these to your .env file and you're ready to run:")
print(f"""
ANTHROPIC_API_KEY=<your-key>
SUPABASE_HOST=aws-1-us-west-2.pooler.supabase.com
SUPABASE_PORT=5432
SUPABASE_DB=postgres
SUPABASE_USER=postgres.msxyacghespfoytxptte
SUPABASE_PASSWORD=ey!6L+RV#Jwk2Bp

PROVISION_ENV_ID={env.id}
PROVISION_DATA_AGENT_ID={data_agent.id}
PROVISION_ORDERING_AGENT_ID={ordering_agent.id}
PROVISION_MARGIN_AGENT_ID={margin_agent.id}
PROVISION_SYNTHESIS_AGENT_ID={synthesis_agent.id}
PROVISION_COORDINATOR_ID={coordinator.id}
""")
