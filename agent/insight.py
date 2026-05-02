"""
agent/insight.py — Lightweight per-commodity cross-signal analysis.

Called during any commodity-specific query so the main agent can respond
like a business partner, not a data lookup. No extra GLM call — pure Python
computation over existing DB data, then the main loop weaves it into language.

Contrast with agent/instinct.py (full 14-day cross-commodity GLM analysis,
only for morning brief and weekly digest).
"""
import logging
from datetime import date

logger = logging.getLogger(__name__)


async def get_commodity_insight(commodity: str) -> dict:
    """
    Pull cross-signals for one commodity and return a pre-formed natural observation.

    The caller (main agent loop) uses `natural_observation` to weave into its response
    — not as a separate bullet, but as the framing that makes it feel like a business partner.

    Signals checked:
    - Velocity this week vs 2-week baseline (trend acceleration/deceleration)
    - Days to stockout at current sell rate
    - Expiry risk (batches within 3 days)
    - Supplier price trend vs FAMA benchmark
    - Cross-signal flags (rising supply price + fast sales = squeeze; slow sales + expiry = urgent)
    """
    try:
        from db.queries import db_get_inventory, db_get_velocity, db_get_price_trend, db_compare_prices

        inventory    = await db_get_inventory(commodity)
        velocity_7d  = await db_get_velocity(commodity, days=7)
        velocity_14d = await db_get_velocity(commodity, days=14)
        price_trend  = await db_get_price_trend(commodity, days=14)
        prices       = await db_compare_prices(commodity)

        # ── Velocity signal ───────────────────────────────────────────
        avg_7d  = velocity_7d["avg_daily_kg"]
        avg_14d = velocity_14d["avg_daily_kg"]
        has_velocity_data = avg_7d > 0 or avg_14d > 0
        if avg_7d > 0 and avg_14d > 0:
            vel_change_pct = round((avg_7d - avg_14d) / avg_14d * 100, 1)
        else:
            vel_change_pct = 0.0  # insufficient data — avoid misleading -100%

        # ── Stockout timing ───────────────────────────────────────────
        total_stock = sum(item["quantity_kg"] for item in inventory)
        days_to_stockout = round(total_stock / avg_7d, 1) if avg_7d > 0 else None

        # ── Spoilage risk ─────────────────────────────────────────────
        at_risk = [i for i in inventory if i["days_remaining"] <= 3 and i["quantity_kg"] > 20]
        min_days_remaining = min((i["days_remaining"] for i in inventory), default=None)

        # ── Supplier price signal ─────────────────────────────────────
        trend_dir   = price_trend["trend"] if price_trend else "stabil"
        trend_pct   = abs(price_trend["pct_change"]) if price_trend else 0
        fama_price  = prices.get("fama_benchmark")
        cheapest    = prices.get("cheapest")

        # ── Cross-signal flags ────────────────────────────────────────
        flags = []
        if vel_change_pct > 25 and trend_dir == "naik" and trend_pct > 5:
            flags.append("demand_surge_AND_rising_supply_cost")
        if vel_change_pct > 25 and days_to_stockout and days_to_stockout < 3:
            flags.append("fast_sales_AND_imminent_stockout")
        if vel_change_pct < -25 and at_risk:
            flags.append("slow_sales_AND_expiry_risk")
        if trend_dir == "turun" and trend_pct > 5 and total_stock < avg_7d * 3:
            flags.append("falling_supply_price_AND_low_stock")

        # ── Pre-formed natural observation ────────────────────────────
        obs = _build_observation(
            commodity, vel_change_pct, days_to_stockout, at_risk,
            min_days_remaining, trend_dir, trend_pct, fama_price, cheapest, flags
        )

        return {
            "commodity":            commodity,
            "total_stock_kg":       round(total_stock, 1),
            "avg_daily_sales_kg":   round(avg_7d, 1),
            "velocity_change_pct":  vel_change_pct if has_velocity_data else None,
            "days_to_stockout":     days_to_stockout,
            "expiry_risk":          bool(at_risk),
            "min_days_remaining":   min_days_remaining,
            "supplier_price_trend": trend_dir,
            "price_change_pct":     trend_pct,
            "fama_benchmark_rm":    fama_price,
            "cheapest_supplier":    cheapest,
            "cross_signal_flags":   flags,
            "natural_observation":  obs,
        }

    except Exception as e:
        logger.error(f"Commodity insight failed for {commodity}: {e}")
        return {
            "commodity": commodity,
            "natural_observation": "",
            "error": str(e),
        }


def _build_observation(
    commodity, vel_change_pct, days_to_stockout, at_risk,
    min_days_remaining, trend_dir, trend_pct, fama_price, cheapest, flags
) -> str:
    """
    Rule-based pre-formed observation in natural Malay.
    The main GLM uses this as context — not to paste verbatim, but to inform its framing.
    """
    parts = []
    c = commodity.title()

    # Velocity story
    if vel_change_pct > 30:
        parts.append(f"{c} jual {vel_change_pct:.0f}% lebih laju dari biasa minggu ni")
    elif vel_change_pct < -30:
        parts.append(f"{c} jual {abs(vel_change_pct):.0f}% lebih perlahan dari biasa")
    elif vel_change_pct > 15:
        parts.append(f"Permintaan {c} meningkat sedikit minggu ni")

    # Stockout timing
    if days_to_stockout is not None:
        if days_to_stockout < 1.5:
            parts.append(f"stok hampir habis — tinggal bawah {days_to_stockout:.1f} hari")
        elif days_to_stockout < 3:
            parts.append(f"stok akan habis dalam {days_to_stockout:.1f} hari pada kadar ini")

    # Expiry risk
    if at_risk:
        if min_days_remaining is not None and min_days_remaining <= 0:
            parts.append(f"ada batch {c} yang dah tamat tempoh — perlu jual segera")
        else:
            parts.append(f"ada {len(at_risk)} batch yang akan rosak dalam {min_days_remaining} hari")

    # Supplier price trend
    if trend_dir == "naik" and trend_pct > 5:
        parts.append(f"harga pembekal naik {trend_pct:.0f}% dalam 2 minggu")
    elif trend_dir == "turun" and trend_pct > 5:
        parts.append(f"harga pembekal turun {trend_pct:.0f}% — peluang beli lebih")

    # FAMA vs cheapest
    if cheapest and fama_price:
        diff_pct = round((cheapest["price_per_kg"] - fama_price) / fama_price * 100, 1)
        if diff_pct < -8:
            parts.append(f"{cheapest['name']} bagi harga {abs(diff_pct):.0f}% bawah FAMA — lagi murah dari pasaran")
        elif diff_pct > 8:
            parts.append(f"semua pembekal harga di atas FAMA — pertimbang tunda beli jika boleh")

    # Cross-signal conclusion
    if "demand_surge_AND_rising_supply_cost" in flags:
        parts.append("kos akan naik lagi — lock in stok sekarang sebelum raya atau cuaca panas")
    elif "slow_sales_AND_expiry_risk" in flags:
        parts.append("jual dengan harga diskaun sekarang daripada rosak — kerugian lebih besar")
    elif "falling_supply_price_AND_low_stock" in flags:
        parts.append("masa sesuai untuk tambah stok — harga rendah dan inventori hampir kosong")

    if not parts:
        return ""

    return ". ".join(parts) + "."
