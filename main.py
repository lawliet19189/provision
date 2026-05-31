from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ORDERING_DATA = {
    "operator": "Marco — Boston locations",
    "items_to_order": [
        {
            "item": "Chicken breast, boneless",
            "recommended_qty": "4 cases (40lb each)",
            "reason": "Running low — big weekend ahead, local marathon Saturday",
            "current_stock": "1.5 cases",
        },
        {
            "item": "Olive oil, extra virgin",
            "recommended_qty": "6 units (4L tins)",
            "reason": "Below par across all 3 locations",
        },
    ],
    "price_flags": [
        {
            "item": "Beef tenderloin",
            "you_are_paying": "$18.40/lb",
            "market_rate": "$15.90/lb",
            "potential_saving": "$312 this order",
            "action": "Consider switching to Gordon Food Service",
        }
    ],
    "total_estimate": "$4,820",
    "vs_last_week": "-$520",
}

MARGIN_DATA = {
    "week_summary": "Revenue up 8% vs last week. Two dishes under pressure.",
    "items_under_pressure": [
        {
            "dish": "Branzino",
            "current_margin": "51%",
            "previous_margin": "67%",
            "cause": "Sea bass cost jumped 19% on November 14th",
            "recommendation": "Raise price by $2, or substitute with halibut",
        }
    ],
    "top_performers": [
        {"dish": "Mushroom risotto", "margin": "74%"},
        {"dish": "Margherita pizza", "margin": "71%"},
    ],
}


@app.get("/api/ordering")
def get_ordering():
    return ORDERING_DATA


@app.get("/api/margins")
def get_margins():
    return MARGIN_DATA


@app.get("/health")
def health():
    return {"status": "ok"}
