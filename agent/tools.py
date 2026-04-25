"""
agent/tools.py — Tool schemas + dispatcher for Stocky AI.

These tools are passed to ilmu-glm-5.1 (Z.ai / YTL AI Labs) via the ILMU API.
The model decides which tools to call and in what order.

Design rules:
  - Each tool description is a CONTRACT — it must tell the model exactly when to call it.
  - Dispatcher filters args to known params only — prevents TypeErrors if model hallucinates fields.
  - No nested LLM calls inside tool handlers. Instinct is post-processing in core.py, not a tool.

Owner: Person 1
"""
import logging
from db.queries import (
    db_get_inventory, db_update_inventory, db_log_sell, db_compare_prices,
    db_get_credit, db_log_credit, db_mark_credit_paid,
    db_get_weekly_digest, db_get_velocity,
)
from services.weather import get_forecast

logger = logging.getLogger(__name__)

# ── Tool Schemas (passed to ilmu-glm-5.1) ─────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_inventory",
            "description": (
                "Get current stock levels and days remaining before expiry. "
                "ALWAYS call before any inventory-related advice, buy recommendation, or spoilage check."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "commodity": {
                        "type": "string",
                        "description": "Commodity name e.g. 'tomato', 'cili', 'bayam'. Omit to get all stock."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_inventory",
            "description": (
                "Record new stock received from a supplier delivery. "
                "Call when user says they received goods, bought stock, or a delivery arrived."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "commodity":       {"type": "string", "description": "e.g. 'tomato', 'cili'"},
                    "quantity_kg":     {"type": "number", "description": "In kg. 1 tan = 1000kg."},
                    "price_per_kg":    {"type": "number", "description": "Cost paid per kg (optional)"},
                    "supplier_name":   {"type": "string", "description": "e.g. 'Pak Ali' (optional)"},
                    "shelf_life_days": {"type": "integer", "description": "Days until expiry. Default 7 for vegetables."}
                },
                "required": ["commodity", "quantity_kg"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "log_sell",
            "description": (
                "Record a sale and deduct stock automatically (FIFO). "
                "Call when user says they sold goods to a buyer. Do NOT call for credit sales — use log_credit instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "commodity":    {"type": "string"},
                    "quantity_kg":  {"type": "number", "description": "Amount sold in kg."},
                    "price_per_kg": {"type": "number", "description": "Selling price per kg (optional)"},
                    "buyer_name":   {"type": "string", "description": "Buyer name (optional)"}
                },
                "required": ["commodity", "quantity_kg"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_supplier_prices",
            "description": (
                "Compare all known supplier quotes for a commodity against the FAMA government benchmark price. "
                "ALWAYS call before recommending a supplier or advising on buying price. "
                "Returns each supplier's price, % vs FAMA, and the cheapest option."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "commodity":          {"type": "string"},
                    "quantity_needed_kg": {"type": "number", "description": "How much the user wants to buy (optional)"}
                },
                "required": ["commodity"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_outstanding_credit",
            "description": (
                "Get all unpaid receivables (credit sales where buyer hasn't paid yet). "
                "Call when discussing cash flow, overdue payments, or when user asks who owes money."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "buyer_name": {
                        "type": "string",
                        "description": "Filter by specific buyer name. Omit to see all outstanding credit."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "log_credit",
            "description": (
                "Record a credit sale — buyer takes goods now and pays later. "
                "Call when user says a buyer took goods on credit, hutang, or will pay later."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "buyer_name": {"type": "string"},
                    "amount_rm":  {"type": "number", "description": "Total RM amount owed"},
                    "commodity":  {"type": "string", "description": "What was sold on credit (optional)"},
                    "due_date":   {"type": "string", "description": "Payment due date ISO format YYYY-MM-DD (optional, defaults to 7 days)"}
                },
                "required": ["buyer_name", "amount_rm"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mark_credit_paid",
            "description": (
                "Mark a buyer's outstanding credit as paid/settled. "
                "Call when user says a buyer has paid, settled, or cleared their debt."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "buyer_name": {"type": "string", "description": "Name of buyer who paid"},
                    "amount_rm":  {"type": "number", "description": "Amount paid in RM. Omit to clear ALL outstanding for this buyer."}
                },
                "required": ["buyer_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather_forecast",
            "description": (
                "Get 5-day weather forecast for the user's city. "
                "ALWAYS call before spoilage advice or buy recommendations — rain slows sales and accelerates spoilage. "
                "Use the city from the user's profile. If unknown, use Kuala Lumpur."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Malaysian city: 'Kuala Lumpur', 'Shah Alam', 'Klang', 'Petaling Jaya', 'Seremban'. Use user's profile city."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_velocity",
            "description": (
                "Get average daily sales rate for a commodity (kg/day). "
                "Use to detect if a commodity is selling faster or slower than usual, "
                "or to estimate days until stockout."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "commodity": {"type": "string"},
                    "days":      {"type": "integer", "description": "Look-back window in days. Default 7. Use 14 for trend comparison."}
                },
                "required": ["commodity"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weekly_digest",
            "description": (
                "Get a 7-day business summary: total revenue, revenue by commodity, "
                "best and worst performers, and total outstanding credit. "
                "Use for weekly digest or when user asks for a business overview."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
]

# ── Dispatcher ────────────────────────────────────────────────────────────────

async def execute_tool(name: str, args: dict) -> dict:
    """
    Route a tool call from the model to the correct function.
    Args are filtered to known parameters to prevent TypeErrors
    if the model passes unexpected fields.
    """
    logger.info(f"Tool: {name}({args})")
    try:
        if name == "get_inventory":
            known = {k: v for k, v in args.items() if k in ("commodity",)}
            return await db_get_inventory(**known)

        elif name == "update_inventory":
            known = {k: v for k, v in args.items()
                     if k in ("commodity", "quantity_kg", "price_per_kg", "supplier_name", "shelf_life_days")}
            return await db_update_inventory(**known)

        elif name == "log_sell":
            known = {k: v for k, v in args.items()
                     if k in ("commodity", "quantity_kg", "price_per_kg", "buyer_name")}
            return await db_log_sell(**known)

        elif name == "compare_supplier_prices":
            known = {k: v for k, v in args.items()
                     if k in ("commodity", "quantity_needed_kg")}
            return await db_compare_prices(**known)

        elif name == "get_outstanding_credit":
            known = {k: v for k, v in args.items() if k in ("buyer_name",)}
            return await db_get_credit(**known)

        elif name == "log_credit":
            known = {k: v for k, v in args.items()
                     if k in ("buyer_name", "amount_rm", "commodity", "due_date")}
            return await db_log_credit(**known)

        elif name == "mark_credit_paid":
            known = {k: v for k, v in args.items()
                     if k in ("buyer_name", "amount_rm")}
            return await db_mark_credit_paid(**known)

        elif name == "get_weather_forecast":
            city = args.get("city", "Kuala Lumpur")
            forecast = await get_forecast(city)
            return {"city": city, "forecast": forecast}

        elif name == "get_velocity":
            commodity = args["commodity"]
            days = int(args.get("days", 7))
            return await db_get_velocity(commodity, days=days)

        elif name == "get_weekly_digest":
            return await db_get_weekly_digest()

        else:
            logger.warning(f"Unknown tool called: {name}")
            return {"error": f"Unknown tool: {name}"}

    except Exception as e:
        logger.error(f"Tool '{name}' failed: {e}", exc_info=True)
        return {"error": str(e), "tool": name}
