from collections import defaultdict

EVENT_MULTIPLIERS = {
    "College Fest": 0.78,
    "Hackathon": 0.88,
    "Cultural Event": 0.72,
    "Workshop": 0.58,
    "Sports Event": 0.82,
}
MEAL_MULTIPLIERS = {"Breakfast": 0.55, "Lunch": 0.82, "Snacks": 0.68, "Dinner": 0.76, "All-day": 1.05}

def build_forecast(event, vendors, menu):
    attendees = int(event["expected_attendees"])
    event_factor = EVENT_MULTIPLIERS.get(event["event_type"], 0.70)
    meal_factor = MEAL_MULTIPLIERS.get(event["meal_period"], 0.70)
    duration_factor = min(1.35, max(0.75, 0.78 + float(event["duration_hours"]) * 0.045))
    predicted = max(1, round(attendees * event_factor * meal_factor * duration_factor))
    confidence = min(92, max(62, round(70 + min(attendees, 1000) / 100 - abs(duration_factor - 1) * 18)))
    # Split demand by category using simple planning weights.
    weights = {"Meals": 0.48, "Snacks": 0.27, "Healthy": 0.12, "Beverages": 0.13}
    category_plan = {k: round(predicted * v) for k, v in weights.items()}
    vendor_map = {v["id"]: v for v in vendors}
    recommendations = []
    for item in menu:
        qty = category_plan.get(item["category"], 0)
        if qty > 0:
            recommendations.append({
                "vendor_id": item["vendor_id"],
                "vendor_name": vendor_map.get(item["vendor_id"], {}).get("name", "Vendor"),
                "item_id": item["id"],
                "item_name": item["name"],
                "category": item["category"],
                "recommended_qty": max(1, round(qty / max(1, sum(1 for x in menu if x["category"] == item["category"])))),
                "unit_price": item["price"],
            })
    return {
        "event_id": event["id"],
        "event_name": event["name"],
        "expected_attendees": attendees,
        "estimated_meal_demand": predicted,
        "confidence_percent": confidence,
        "assumptions": [
            f"{event_factor:.0%} event participation factor for {event['event_type'].lower()}",
            f"{meal_factor:.0%} meal-period demand factor",
            f"{duration_factor:.2f} duration adjustment for {event['duration_hours']} hours",
            "Planning weights: 48% meals, 27% snacks, 12% healthy options, 13% beverages",
        ],
        "category_plan": category_plan,
        "vendor_recommendations": recommendations,
        "model_note": "Explainable heuristic forecast for prototype planning; not a trained predictive model.",
    }
