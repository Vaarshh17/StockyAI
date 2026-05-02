"""
agent/quote.py — Supplier quote analysis engine.

When a wholesaler receives a supplier price (forwarded message or typed quote),
Stocky benchmarks it against:
  - Their own lowest historical buy price (last 60 days)
  - Current FAMA benchmark
  - Their actual average sell price (to compute real margin)

Returns a clear BUY / NEGOTIATE / PASS decision with margin breakdown
and the capital needed — so the next question is always "do you have the money?"
"""
import logging

logger = logging.getLogger(__name__)

# Margin thresholds for wet market wholesale
MARGIN_MINIMUM   = 0.12   # 12% — barely covers handling + transport
MARGIN_HEALTHY   = 0.20   # 20% — good wholesale margin
MARGIN_TARGET    = 0.25   # 25% — ideal


async def analyze_supplier_quote(
    commodity: str,
    quoted_price_rm: float,
    quantity_kg: float = None,
    supplier_name: str = None,
) -> dict:
    """
    Full benchmark analysis for an incoming supplier price quote.

    Returns decision, price comparisons, sell price targets, capital needed,
    and a pre-formed natural observation the agent weaves into its response.
    """
    try:
        from db.queries import db_get_price_history, get_fama_price

        history  = await db_get_price_history(commodity, days=60)
        fama     = await get_fama_price(commodity)

        fama_price       = fama["price_per_kg"] if fama else None
        historical_low   = history["min_buy_price"]
        avg_buy          = history["avg_buy_price"]
        avg_sell         = history["avg_sell_price"]
        last_buy_price   = history["last_buy_price"]
        last_supplier    = history["last_supplier"]

        # ── Price comparisons ─────────────────────────────────────────
        vs_fama_pct = None
        if fama_price:
            vs_fama_pct = round((quoted_price_rm - fama_price) / fama_price * 100, 1)

        vs_hist_low_pct = None
        if historical_low:
            vs_hist_low_pct = round((quoted_price_rm - historical_low) / historical_low * 100, 1)

        vs_last_buy_pct = None
        if last_buy_price:
            vs_last_buy_pct = round((quoted_price_rm - last_buy_price) / last_buy_price * 100, 1)

        # ── Margin analysis ───────────────────────────────────────────
        # Use actual avg sell price if available; else estimate from FAMA × markup
        effective_sell = avg_sell or (fama_price * 1.30 if fama_price else None)

        margin_pct = None
        if effective_sell:
            margin_pct = round((effective_sell - quoted_price_rm) / quoted_price_rm * 100, 1)

        # Suggested sell prices
        sell_breakeven  = round(quoted_price_rm * (1 + MARGIN_MINIMUM), 2)
        sell_healthy    = round(quoted_price_rm * (1 + MARGIN_HEALTHY), 2)
        sell_target     = round(quoted_price_rm * (1 + MARGIN_TARGET), 2)

        # Potential profit per kg and total
        profit_per_kg   = round(effective_sell - quoted_price_rm, 2) if effective_sell else None
        capital_needed  = round(quoted_price_rm * quantity_kg, 2) if quantity_kg else None
        potential_profit = round(profit_per_kg * quantity_kg, 2) if (profit_per_kg and quantity_kg) else None

        # ── Decision logic ────────────────────────────────────────────
        decision = _decide(quoted_price_rm, fama_price, historical_low, avg_buy, margin_pct)

        # ── Natural observation ───────────────────────────────────────
        observation = _build_quote_observation(
            commodity, supplier_name, quoted_price_rm, fama_price, historical_low,
            vs_fama_pct, vs_hist_low_pct, vs_last_buy_pct, last_supplier,
            margin_pct, sell_healthy, capital_needed, decision
        )

        return {
            "commodity":          commodity,
            "quoted_price_rm":    quoted_price_rm,
            "quantity_kg":        quantity_kg,
            "supplier":           supplier_name,

            # Benchmarks
            "fama_benchmark_rm":  fama_price,
            "historical_low_rm":  historical_low,
            "avg_buy_price_rm":   avg_buy,
            "last_buy_price_rm":  last_buy_price,
            "last_supplier":      last_supplier,
            "avg_sell_price_rm":  avg_sell,

            # Comparisons
            "vs_fama_pct":        vs_fama_pct,
            "vs_historical_low_pct": vs_hist_low_pct,
            "vs_last_buy_pct":    vs_last_buy_pct,

            # Margin & profit
            "margin_at_avg_sell_pct": margin_pct,
            "sell_price_breakeven_rm": sell_breakeven,
            "sell_price_healthy_rm":   sell_healthy,
            "sell_price_target_rm":    sell_target,
            "profit_per_kg_rm":        profit_per_kg,
            "capital_needed_rm":       capital_needed,
            "potential_profit_rm":     potential_profit,

            # Verdict
            "decision":           decision,
            "natural_observation": observation,
        }

    except Exception as e:
        logger.error(f"Quote analysis failed for {commodity}: {e}")
        return {
            "commodity":          commodity,
            "quoted_price_rm":    quoted_price_rm,
            "decision":           "UNKNOWN",
            "natural_observation": "",
            "error":              str(e),
        }


def _decide(
    quoted: float,
    fama: float | None,
    hist_low: float | None,
    avg_buy: float | None,
    margin_pct: float | None,
) -> str:
    """
    Four-outcome decision:
      BELI      — price is clearly good, margin is healthy
      BOLEH     — acceptable price, margin is thin but viable
      NEGOTIATE — above FAMA or worse than history, push back
      PASS      — significantly above benchmarks, not worth it
    """
    score = 0  # positive = buy, negative = skip

    if fama:
        if quoted < fama * 0.95:
            score += 2   # more than 5% below FAMA
        elif quoted < fama:
            score += 1   # slightly below FAMA
        elif quoted < fama * 1.05:
            score -= 1   # slightly above FAMA
        else:
            score -= 2   # significantly above FAMA

    if hist_low:
        if quoted <= hist_low * 1.02:
            score += 2   # at or near historical low
        elif quoted <= hist_low * 1.10:
            score += 1   # within 10% of historical low
        elif quoted > hist_low * 1.20:
            score -= 2   # 20%+ above historical low

    if margin_pct is not None:
        if margin_pct >= MARGIN_HEALTHY * 100:
            score += 1
        elif margin_pct < MARGIN_MINIMUM * 100:
            score -= 2   # not enough margin to bother

    if score >= 3:
        return "BELI"
    elif score >= 1:
        return "BOLEH"
    elif score >= -1:
        return "NEGOTIATE"
    else:
        return "PASS"


def _build_quote_observation(
    commodity, supplier_name, quoted_price, fama_price, hist_low,
    vs_fama_pct, vs_hist_low_pct, vs_last_buy_pct, last_supplier,
    margin_pct, sell_healthy, capital_needed, decision
) -> str:
    c = commodity.title()
    parts = []

    # Opening — price vs FAMA
    if vs_fama_pct is not None:
        if vs_fama_pct <= -8:
            parts.append(f"Harga {quoted_price:.2f}/kg untuk {c} — {abs(vs_fama_pct):.0f}% bawah FAMA. Harga ni sangat bagus")
        elif vs_fama_pct <= 0:
            parts.append(f"Harga {quoted_price:.2f}/kg untuk {c} — bawah FAMA sebanyak {abs(vs_fama_pct):.0f}%")
        elif vs_fama_pct <= 8:
            parts.append(f"Harga {quoted_price:.2f}/kg untuk {c} — {vs_fama_pct:.0f}% di atas FAMA. Boleh cuba tawar lagi")
        else:
            parts.append(f"Harga {quoted_price:.2f}/kg untuk {c} — {vs_fama_pct:.0f}% di atas FAMA. Mahal")
    else:
        parts.append(f"Harga {quoted_price:.2f}/kg untuk {c}")

    # vs historical low
    if vs_hist_low_pct is not None:
        if vs_hist_low_pct <= 2:
            parts.append(f"ni antara harga paling rendah yang awak pernah beli dalam 2 bulan ni")
        elif vs_hist_low_pct <= 10:
            parts.append(f"harga terendah awak pernah dapat RM{hist_low:.2f} — sikit lagi je")
        elif vs_hist_low_pct > 15:
            parts.append(f"lebih mahal {vs_hist_low_pct:.0f}% dari harga terendah awak sebelum ni (RM{hist_low:.2f})")

    # vs last supplier (if different)
    if vs_last_buy_pct is not None and last_supplier and supplier_name and last_supplier.lower() != (supplier_name or "").lower():
        if vs_last_buy_pct > 5:
            parts.append(f"kali lepas beli dari {last_supplier} harga lebih rendah")

    # Margin
    if margin_pct is not None:
        if margin_pct >= 25:
            parts.append(f"margin lebih kurang {margin_pct:.0f}% — untung elok")
        elif margin_pct >= 12:
            parts.append(f"margin dalam {margin_pct:.0f}% — boleh lah tapi nipis")
        else:
            parts.append(f"margin hanya {margin_pct:.0f}% — terlalu nipis untuk wholesale, cuba tawar")

    # Sell price suggestion
    if sell_healthy:
        parts.append(f"jual minimum RM{sell_healthy:.2f}/kg untuk untung 20%")

    # Capital needed
    if capital_needed:
        parts.append(f"modal yang perlu: RM{capital_needed:,.0f}")

    return ". ".join(parts) + "."
