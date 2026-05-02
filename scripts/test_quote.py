import asyncio
from agent.quote import analyze_supplier_quote

async def main():
    tests = [
        # Good deal — below historical low
        ("tomato", 2.40, 1000, "Pak Ali"),
        # At FAMA — borderline
        ("tomato", 2.75, 500, "Pak Rahman"),
        # Above FAMA — should negotiate/pass
        ("cili", 4.50, 300, "Ah Seng"),
        # Great deal on cili
        ("cili", 3.80, 400, "Uncle Lim"),
    ]
    for commodity, price, qty, supplier in tests:
        print(f"\n{'='*60}")
        print(f"QUOTE: {supplier} → {commodity} @ RM{price}/kg, {qty}kg")
        r = await analyze_supplier_quote(commodity, price, qty, supplier)
        print(f"Decision: {r['decision']}")
        print(f"vs FAMA: {r['vs_fama_pct']}%  vs hist_low: {r['vs_historical_low_pct']}%")
        print(f"Margin at avg sell: {r['margin_at_avg_sell_pct']}%")
        print(f"Sell healthy @ RM{r['sell_price_healthy_rm']}/kg")
        print(f"Capital needed: RM{r['capital_needed_rm']:,}")
        print(f"Potential profit: RM{r['potential_profit_rm']}")
        print(f"Observation: {r['natural_observation']}")

asyncio.run(main())
