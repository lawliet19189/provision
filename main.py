import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

REPORT_PATH = Path(__file__).parent / "data" / "intelligence" / "weekly_report.json"


def load_report():
    if not REPORT_PATH.exists():
        raise HTTPException(status_code=404, detail="No report generated yet.")
    with open(REPORT_PATH) as f:
        return json.load(f)


# ── Report API ────────────────────────────────────────────────────────────────

@app.get("/api/report")
def get_report():
    return load_report()


@app.get("/api/report/summary")
def get_summary():
    """Structured summary for dashboards and cards."""
    r = load_report()
    es = r["executive_summary"]
    return {
        "week": r["week"],
        "generated_at": r["generated_at"],
        "headline": es["headline"],
        "marco_tldr": r["marco_tldr"],
        "metrics": es["metrics"],
        "actions": r["operator_action_items"],
        "anomalies": r["anomalies_and_alerts"]["items"],
        "top_margin_winners": r["margin_insights"]["high_margin_winners_to_grow"],
        "margin_leaks": r["margin_insights"]["margin_leaks_cost_inflation"],
        "order_highlights": r["ordering_insights"]["buy_more"][:5],
        "locations": r["location_performance"]["named_stores"],
        "promotion_leak": r["margin_insights"]["promotion_leak"],
    }


@app.get("/api/report/voice")
def get_voice():
    """
    ElevenLabs conversational AI tool endpoint.
    Returns a concise, speech-friendly briefing Marco can ask questions about.
    """
    r = load_report()
    es = r["executive_summary"]
    m = es["metrics"]
    actions = r["operator_action_items"]
    anomalies = r["anomalies_and_alerts"]["items"]
    leaks = r["margin_insights"]["margin_leaks_cost_inflation"]
    ordering = r["ordering_insights"]

    top_actions = "\n".join(
        f"{a['priority']}. {a['action']}" for a in actions[:3]
    )
    anomaly_text = "\n".join(
        f"- {a['product']}: {a['type']} {a['change_pct']:+.1f}% — {a['detail'][:120]}"
        for a in anomalies
    )
    leak_text = "\n".join(
        f"- {l['product']}: {l['margin_pct']:.1f}% margin — {l['fix'][:100]}"
        for l in leaks[:3]
    )

    briefing = f"""
PROVISION WEEKLY BRIEFING — {r['week']}

HEADLINE: {es['headline']}

KEY NUMBERS:
- Transactions: {m['transactions_this_week']:,} (vs {m['transactions_prior_week']:,} last week, {m['wow_transaction_change_pct']:+.1f}%)
- Estimated Revenue: ${m['revenue_proxy_usd']:,.0f}
- Gross Margin: {m['blended_gross_margin_pct']:.1f}%
- Next PO estimate: ${m['next_po_estimated_cost_usd']:,.0f}

TOP PRIORITIES:
{top_actions}

ANOMALIES:
{anomaly_text}

MARGIN LEAKS TO FIX:
{leak_text}

ORDERING:
{ordering['summary']}

BOTTOM LINE: {r['marco_tldr']}
""".strip()

    return {
        "briefing": briefing,
        "marco_tldr": r["marco_tldr"],
        "week": r["week"],
        "metrics": m,
        "top_actions": [{"priority": a["priority"], "action": a["action"], "why": a["why"]} for a in actions],
        "anomalies": [{"product": a["product"], "type": a["type"], "change_pct": a["change_pct"], "detail": a["detail"]} for a in anomalies],
        "margin_leaks": [{"product": l["product"], "margin_pct": l["margin_pct"], "fix": l["fix"]} for l in leaks],
        "order_summary": {
            "estimated_cost": ordering["next_po_estimated_cost_usd"],
            "line_count": ordering["order_line_count"],
            "top_buys": [{"product": b["product"], "wow_pct_change": b["wow_pct_change"], "urgency": b["urgency"]} for b in ordering["buy_more"][:5]],
        },
    }


# ── Legacy endpoints (kept for compatibility) ─────────────────────────────────

@app.get("/api/ordering")
def get_ordering():
    r = load_report()
    o = r["ordering_insights"]
    return {
        "summary": o["summary"],
        "total_estimated_cost": f"${o['next_po_estimated_cost_usd']:,.2f}",
        "items_to_order": [
            {"item": b["product"], "recommended_qty": b["recommended_qty"],
             "reason": b["rationale"], "urgency": b["urgency"]}
            for b in o["buy_more"]
        ],
        "price_flags": [
            {"item": h["product"], "concern": h["action"], "action": h["action"]}
            for h in o.get("hold_or_trim", [])[:3]
        ],
    }


@app.get("/api/margins")
def get_margins():
    r = load_report()
    mg = r["margin_insights"]
    return {
        "week_summary": mg["summary"],
        "blended_margin_pct": mg["blended_gross_margin_pct"],
        "items_under_pressure": [
            {"dish": l["product"], "current_margin": f"{l['margin_pct']:.1f}%",
             "cause": l["fix"], "category": l["category"]}
            for l in mg["margin_leaks_cost_inflation"]
        ],
        "top_performers": [
            {"dish": w.get("product") or w.get("category"),
             "margin": f"{w.get('margin_pct') or w.get('blended_margin_pct')}%"}
            for w in mg["high_margin_winners_to_grow"][:4]
        ],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


# ── Dashboard (served last so API routes take priority) ───────────────────────

@app.get("/", response_class=HTMLResponse)
def dashboard():
    html_path = Path(__file__).parent / "static" / "index.html"
    if not html_path.exists():
        return HTMLResponse("<h1>Dashboard not built yet.</h1>", status_code=200)
    return HTMLResponse(html_path.read_text())
