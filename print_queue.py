import os
import requests
from datetime import datetime, timezone
from flask import Blueprint, jsonify

print_queue_bp = Blueprint('print_queue', __name__)

SHOPIFY_STORE = "y4n8mm-1g.myshopify.com"
SHOPIFY_TOKEN = os.environ.get("SHOPIFY_ACCESS_TOKEN")

COLOUR_KEYWORDS = {
    "Terracotta": ["terracotta"],
    "Olive Green": ["olive"],
    "Black": ["black"],
    "Mustard Yellow": ["mustard", "yellow"],
    "Beige": ["beige"],
}

def get_colour(variant_title):
    if not variant_title:
        return "Unknown"
    vt = variant_title.lower()
    for colour, keywords in COLOUR_KEYWORDS.items():
        if any(k in vt for k in keywords):
            return colour
    return variant_title

def days_waiting(created_at_str):
    created = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    return (now - created).days

@print_queue_bp.route("/print-queue", methods=["GET"])
def print_queue():
    url = f"https://{SHOPIFY_STORE}/admin/api/2024-01/orders.json"
    params = {
        "status": "open",
        "fulfillment_status": "unfulfilled",
        "limit": 100,
        "fields": "id,name,created_at,line_items"
    }
    headers = {"X-Shopify-Access-Token": SHOPIFY_TOKEN}

    resp = requests.get(url, params=params, headers=headers)
    orders = resp.json().get("orders", [])

    # Group by colour
    groups = {}
    overdue = []
    multi_colour = []

    for order in orders:
        order_colours = []
        for item in order.get("line_items", []):
            if "clock" in item.get("title", "").lower() or "perch" in item.get("title", "").lower():
                colour = get_colour(item.get("variant_title", ""))
                qty = item.get("quantity", 1)
                for _ in range(qty):
                    order_colours.append(colour)
                    if colour not in groups:
                        groups[colour] = []
                    groups[colour].append({
                        "order_name": order["name"],
                        "days": days_waiting(order["created_at"])
                    })

        if len(set(order_colours)) > 1:
            multi_colour.append(f"{order['name']} ({' + '.join(set(order_colours))})")

        if days_waiting(order["created_at"]) >= 10:
            overdue.append(order["name"])

    # Build message
    # Sort all orders oldest first
    all_orders = []
    for colour, items in groups.items():
        for item in items:
            all_orders.append({
                "colour": colour,
                "order_name": item["order_name"],
                "days": item["days"]
            })
    
    all_orders.sort(key=lambda x: x["days"], reverse=True)

    # Top 11 priority
    top11 = all_orders[:11]
    remaining = all_orders[11:]

    # Group top 11 by colour
    top_groups = {}
    for item in top11:
        c = item["colour"]
        if c not in top_groups:
            top_groups[c] = []
        top_groups[c].append(item["order_name"])

    # Group remaining by colour
    remain_groups = {}
    for item in remaining:
        c = item["colour"]
        remain_groups[c] = remain_groups.get(c, 0) + 1

    colour_icons = {
        "Terracotta": "🟠",
        "Olive Green": "🟢",
        "Black": "⚫",
        "Mustard Yellow": "🟡",
        "Beige": "🔵",
    }

    today = datetime.now().strftime("%-d %b")
    lines = [f"🕐 Layerlabs Print Queue — {today}"]
    total = len(all_orders)
    lines.append(f"📦 Total pending: {total} clocks\n")

    lines.append(f"🖨️ Print TODAY — top 11 (pick your best 9):")
    for colour, order_names in top_groups.items():
        icon = colour_icons.get(colour, "🔲")
        lines.append(f"{icon} {colour} x{len(order_names)} — {', '.join(order_names)}")

    if remaining:
        lines.append(f"\n⏳ Remaining queue ({len(remaining)} units):")
        for colour, count in remain_groups.items():
            icon = colour_icons.get(colour, "🔲")
            lines.append(f"{icon} {colour} — {count} more")

    if overdue:
        lines.append(f"\n⚠️ Overdue (10d+): {', '.join(overdue)}")

    if multi_colour:
        lines.append(f"\n📌 Ship together (multi-colour):")
        for m in multi_colour:
            lines.append(f"   {m}")

    return {"message": "\n".join(lines)}