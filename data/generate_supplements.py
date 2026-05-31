"""
Generates two supplement CSV files for Supabase:
  1. products.csv   — 81 products with category, unit_cost, unit_price, supplier
  2. locations.csv  — city → Marco's location mapping

Run: python3 data/generate_supplements.py
"""

import csv
import os

OUT = os.path.dirname(__file__)

# ── products.csv ──────────────────────────────────────────────────────────────
# Fields: product_name, category, unit_cost_usd, unit_price_usd, supplier, unit
PRODUCTS = [
    # Produce
    ("Apple",           "Produce",    0.30,  0.89,  "US Foods",       "each"),
    ("Banana",          "Produce",    0.15,  0.49,  "US Foods",       "each"),
    ("Carrots",         "Produce",    0.60,  1.99,  "Sysco",          "lb"),
    ("Onions",          "Produce",    0.40,  1.29,  "Sysco",          "lb"),
    ("Orange",          "Produce",    0.35,  0.99,  "US Foods",       "each"),
    ("Potatoes",        "Produce",    0.50,  1.49,  "Sysco",          "lb"),
    ("Spinach",         "Produce",    1.10,  3.49,  "US Foods",       "bag"),
    ("Tomatoes",        "Produce",    0.80,  2.49,  "Sysco",          "lb"),
    # Meat & Seafood
    ("Beef",            "Meat",       5.20, 12.99,  "Sysco",          "lb"),
    ("Chicken",         "Meat",       2.10,  5.99,  "Sysco",          "lb"),
    ("Salmon",          "Seafood",    6.50, 14.99,  "US Foods",       "lb"),
    ("Shrimp",          "Seafood",    7.80, 16.99,  "US Foods",       "lb"),
    ("Tuna",            "Seafood",    3.40,  8.49,  "Gordon FS",      "lb"),
    # Dairy & Eggs
    ("Butter",          "Dairy",      2.20,  4.99,  "Sysco",          "lb"),
    ("Cheese",          "Dairy",      3.10,  6.99,  "Sysco",          "lb"),
    ("Eggs",            "Dairy",      2.40,  4.49,  "Gordon FS",      "dozen"),
    ("Ice Cream",       "Dairy",      2.80,  5.99,  "Gordon FS",      "pint"),
    ("Milk",            "Dairy",      1.20,  2.99,  "Sysco",          "gallon"),
    ("Yogurt",          "Dairy",      0.90,  2.49,  "US Foods",       "each"),
    # Bakery & Grains
    ("Bread",           "Bakery",     1.30,  3.49,  "Gordon FS",      "loaf"),
    ("Cereal",          "Bakery",     2.10,  4.99,  "US Foods",       "box"),
    ("Cereal Bars",     "Bakery",     1.80,  4.29,  "US Foods",       "box"),
    ("Pancake Mix",     "Bakery",     1.50,  3.79,  "Sysco",          "box"),
    ("Pasta",           "Bakery",     0.80,  2.29,  "Sysco",          "lb"),
    ("Rice",            "Bakery",     0.60,  1.89,  "Sysco",          "lb"),
    # Pantry
    ("BBQ Sauce",       "Pantry",     1.10,  3.49,  "Gordon FS",      "bottle"),
    ("Canned Soup",     "Pantry",     0.90,  2.49,  "US Foods",       "can"),
    ("Coffee",          "Pantry",     4.20,  9.99,  "Gordon FS",      "bag"),
    ("Honey",           "Pantry",     2.80,  6.99,  "US Foods",       "jar"),
    ("Jam",             "Pantry",     1.40,  3.99,  "Gordon FS",      "jar"),
    ("Ketchup",         "Pantry",     0.80,  2.49,  "Sysco",          "bottle"),
    ("Mayonnaise",      "Pantry",     1.20,  3.29,  "Sysco",          "jar"),
    ("Mustard",         "Pantry",     0.70,  2.19,  "Sysco",          "bottle"),
    ("Olive Oil",       "Pantry",     4.50,  9.99,  "US Foods",       "bottle"),
    ("Pancake Mix",     "Pantry",     1.50,  3.79,  "Sysco",          "box"),
    ("Peanut Butter",   "Pantry",     1.60,  3.99,  "Gordon FS",      "jar"),
    ("Pickles",         "Pantry",     1.00,  2.99,  "Gordon FS",      "jar"),
    ("Syrup",           "Pantry",     2.10,  4.99,  "US Foods",       "bottle"),
    ("Tea",             "Pantry",     2.40,  5.99,  "US Foods",       "box"),
    ("Vinegar",         "Pantry",     0.80,  2.29,  "Sysco",          "bottle"),
    # Beverages
    ("Soda",            "Beverage",   0.40,  1.49,  "Gordon FS",      "can"),
    ("Water",           "Beverage",   0.20,  0.99,  "Sysco",          "bottle"),
    # Snacks
    ("Chips",           "Snacks",     0.90,  2.99,  "Gordon FS",      "bag"),
    # Personal Care
    ("Deodorant",       "Personal Care", 1.80, 4.99, "US Foods",      "each"),
    ("Feminine Hygiene Products", "Personal Care", 2.50, 6.99, "US Foods", "pack"),
    ("Hair Gel",        "Personal Care", 1.50, 4.49, "US Foods",      "each"),
    ("Hand Sanitizer",  "Personal Care", 1.20, 3.49, "Gordon FS",     "each"),
    ("Razors",          "Personal Care", 2.80, 7.99, "US Foods",      "pack"),
    ("Shampoo",         "Personal Care", 1.90, 5.49, "US Foods",      "bottle"),
    ("Shaving Cream",   "Personal Care", 1.40, 3.99, "Gordon FS",     "each"),
    ("Shower Gel",      "Personal Care", 1.60, 4.29, "US Foods",      "bottle"),
    ("Soap",            "Personal Care", 0.60, 1.99, "Sysco",         "bar"),
    ("Toothbrush",      "Personal Care", 0.80, 2.99, "US Foods",      "each"),
    ("Toothpaste",      "Personal Care", 1.10, 3.49, "US Foods",      "each"),
    # Baby
    ("Baby Wipes",      "Baby",       2.10,  5.99,  "US Foods",       "pack"),
    ("Diapers",         "Baby",       8.50, 22.99,  "US Foods",       "pack"),
    # Household Consumables
    ("Air Freshener",   "Household",  1.30,  3.99,  "Gordon FS",      "each"),
    ("Cleaning Spray",  "Household",  1.10,  3.29,  "Gordon FS",      "each"),
    ("Dish Soap",       "Household",  0.90,  2.79,  "Gordon FS",      "bottle"),
    ("Laundry Detergent","Household", 4.20,  9.99,  "US Foods",       "box"),
    ("Paper Towels",    "Household",  2.80,  6.99,  "Sysco",          "roll"),
    ("Sponges",         "Household",  0.80,  2.49,  "Sysco",          "pack"),
    ("Tissues",         "Household",  1.20,  2.99,  "Sysco",          "box"),
    ("Toilet Paper",    "Household",  3.10,  7.49,  "Sysco",          "pack"),
    ("Trash Bags",      "Household",  2.40,  5.99,  "Sysco",          "box"),
    # Cleaning Equipment
    ("Broom",           "Cleaning Equipment", 4.50, 12.99, "Gordon FS", "each"),
    ("Cleaning Rags",   "Cleaning Equipment", 1.20,  3.49, "Gordon FS", "pack"),
    ("Dustpan",         "Cleaning Equipment", 2.80,  7.99, "Gordon FS", "each"),
    ("Mop",             "Cleaning Equipment", 5.20, 14.99, "Gordon FS", "each"),
    # Hardware / Home
    ("Bath Towels",     "Home",       4.20, 12.99,  "Gordon FS",      "each"),
    ("Dishware",        "Home",       8.50, 24.99,  "Gordon FS",      "set"),
    ("Extension Cords", "Hardware",   3.80, 11.99,  "Gordon FS",      "each"),
    ("Garden Hose",     "Hardware",  12.00, 34.99,  "Gordon FS",      "each"),
    ("Insect Repellent","Seasonal",   2.10,  5.99,  "US Foods",       "each"),
    ("Iron",            "Appliance", 14.00, 39.99,  "Gordon FS",      "each"),
    ("Ironing Board",   "Appliance", 18.00, 49.99,  "Gordon FS",      "each"),
    ("Lawn Mower",      "Seasonal",  95.00,249.99,  "Gordon FS",      "each"),
    ("Light Bulbs",     "Hardware",   1.50,  4.99,  "Gordon FS",      "pack"),
    ("Plant Fertilizer","Seasonal",   3.20,  8.99,  "Gordon FS",      "bag"),
    ("Power Strips",    "Hardware",   4.50, 12.99,  "Gordon FS",      "each"),
    ("Trash Cans",      "Home",       6.80, 19.99,  "Gordon FS",      "each"),
    ("Vacuum Cleaner",  "Appliance", 45.00,129.99,  "Gordon FS",      "each"),
]

# Deduplicate (Pancake Mix appears twice)
seen = set()
PRODUCTS_DEDUPED = []
for p in PRODUCTS:
    if p[0] not in seen:
        seen.add(p[0])
        PRODUCTS_DEDUPED.append(p)

products_path = os.path.join(OUT, "products.csv")
with open(products_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["product_name", "category", "unit_cost_usd", "unit_price_usd", "supplier", "unit"])
    writer.writerows(PRODUCTS_DEDUPED)
print(f"Written {len(PRODUCTS_DEDUPED)} products → {products_path}")

# ── locations.csv ─────────────────────────────────────────────────────────────
LOCATIONS = [
    ("LOC001", "Marco's — Back Bay",     "Boston",        "MA", "Supermarket"),
    ("LOC002", "Marco's — South End",    "Boston",        "MA", "Supermarket"),
    ("LOC003", "Marco's — Cambridge",    "Cambridge",     "MA", "Specialty Store"),
    ("LOC004", "Marco's — Los Angeles",  "Los Angeles",   "CA", "Supermarket"),
    ("LOC005", "Marco's — San Francisco","San Francisco",  "CA", "Specialty Store"),
    ("LOC006", "Marco's — Chicago",      "Chicago",       "IL", "Warehouse Club"),
    ("LOC007", "Marco's — Houston",      "Houston",       "TX", "Supermarket"),
    ("LOC008", "Marco's — Phoenix",      "Phoenix",       "AZ", "Convenience Store"),
    ("LOC009", "Marco's — Seattle",      "Seattle",       "WA", "Specialty Store"),
    ("LOC010", "Marco's — Miami",        "Miami",         "FL", "Department Store"),
]

# The dataset has these cities: Los Angeles, San Francisco, Chicago, Houston,
# Phoenix, Seattle, Miami, New York, Dallas, Boston — map them all
CITY_TO_LOCATION = {
    "Los Angeles":   "LOC004",
    "San Francisco": "LOC005",
    "Chicago":       "LOC006",
    "Houston":       "LOC007",
    "Phoenix":       "LOC008",
    "Seattle":       "LOC009",
    "Miami":         "LOC010",
    "Boston":        "LOC001",
    # fallback for any other cities in data
}

locations_path = os.path.join(OUT, "locations.csv")
with open(locations_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["location_id", "location_name", "city", "state", "store_type"])
    writer.writerows(LOCATIONS)
print(f"Written {len(LOCATIONS)} locations → {locations_path}")

city_map_path = os.path.join(OUT, "city_to_location.csv")
with open(city_map_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["city", "location_id"])
    for city, loc_id in CITY_TO_LOCATION.items():
        writer.writerow([city, loc_id])
print(f"Written city→location map → {city_map_path}")
