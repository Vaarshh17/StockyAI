"""
agent/tools.py — Tool schemas + dispatcher for Stocky AI.
Owner: Person 1
"""
import json
import logging
from db.queries import (
    db_get_inventory, db_update_inventory, db_log_sell, db_compare_prices,
    db_get_credit, db_log_credit, db_get_weekly_digest, db_get_velocity,
)
from services.weather import get_forecast

logger = logging.getLogger(__name__)

# ── Tool Schemas (passed to GLM) ──────────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_inventory",
            "description": "Get current stock levels. ALWAYS call before any inventory-related advice.",
            "parameters": {
                "type": "object",
                "properties": {
                    "commodity": {"type": "string", "description": "e.g. 'tomato', 'cili', 'bayam'. Omit for all."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_inventory",
            "description": "Record new stock from a delivery. Call when user mentions receiving goods.",
            "parameters": {
                "type": "object",
                "properties": {
                    "commodity":       {"type": "string"},
                    "quantity_kg":     {"type": "number", "description": "In kg. 1 tan = 1000kg."},
                    "price_per_kg":    {"type": "number"},
                    "supplier_name":   {"type": "string"},
                    "shelf_life_days": {"type": "integer", "description": "Default 7 for vegetables."}
                },
                "required": ["commodity", "quantity_kg"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "log_sell",
            "description": "Record a sale. Call when user mentions selling goods to a buyer. Deducts stock automatically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "commodity":    {"type": "string"},
                    "quantity_kg":  {"type": "number", "description": "Amount sold in kg."},
                    "price_per_kg": {"type": "number"},
                    "buyer_name":   {"type": "string", "description": "Who the goods were sold to. Optional."}
                },
                "required": ["commodity", "quantity_kg"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_supplier_prices",
            "description": "Compare all known suppliers for a commodity vs FAMA benchmark. Use for buy decisions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "commodity":          {"type": "string"},
                    "quantity_needed_kg": {"type": "number"}
                },
                "required": ["commodity"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_outstanding_credit",
            "description": "Get unpaid receivables. Check when discussing credit or cash flow.",
            "parameters": {
                "type": "object",
                "properties": {
                    "buyer_name": {"type": "string", "description": "Filter by buyer. Omit for all."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "log_credit",
            "description": "Record a credit sale — buyer takes goods and pays later.",
            "parameters": {
                "type": "object",
                "properties": {
                    "buyer_name": {"type": "string"},
                    "amount_rm":  {"type": "number"},
                    "commodity":  {"type": "string"},
                    "due_date":   {"type": "string", "description": "ISO date YYYY-MM-DD"}
                },
                "required": ["buyer_name", "amount_rm"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather_forecast",
            "description": "Get 5-day weather forecast. ALWAYS call before spoilage or buy recommendations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "Malaysian city. Default: Kuala Lumpur"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_velocity",
            "description": "Get how fast a commodity is selling (avg kg/day over 7 days).",
            "parameters": {
                "type": "object",
                "properties": {
                    "commodity": {"type": "string"}
                },
                "required": ["commodity"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weekly_digest",
            "description": "7-day business summary: revenue, top commodities, outstanding credit.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_instinct_analysis",
            "description": "Run Stocky's Instinct — cross-signal analysis over 14 days to find one non-obvious pattern. Use ONLY for morning brief or weekly digest generation.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
]

# ── Dispatcher ────────────────────────────────────────────────────────────────

async def execute_tool(name: str, args: dict) -> dict:
    logger.info(f"Tool: {name}({args})")
    try:
        if name == "get_inventory":
            return await db_get_inventory(**args)
        elif name == "update_inventory":
            return await db_update_inventory(**args)
        elif name == "log_sell":
            return await db_log_sell(**args)
        elif name == "compare_supplier_prices":
            return await db_compare_prices(**args)
        elif name == "get_outstanding_credit":
            return await db_get_credit(**args)
        elif name == "log_credit":
            return await db_log_credit(**args)
        elif name == "get_weather_forecast":
            return await get_forecast(args.get("city", "Kuala Lumpur"))
        elif name == "get_velocity":
            return await db_get_velocity(args["commodity"])
        elif name == "get_weekly_digest":
            return await db_get_weekly_digest()
        elif name == "get_instinct_analysis":
            from agent.instinct import get_instinct
            result = await get_instinct()
            return {"instinct": result}
        else:
            return {"error": f"Unknown tool: {name}"}
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}")
        return {"error": str(e)}
