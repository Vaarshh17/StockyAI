# Stocky AI — Demo Script (UM Hackathon Finals)

**Date of demo:** 2026-05-02  
**Persona:** Pak Zulkifli, 52, tomato & cili wholesaler, Chow Kit wet market, KL  
**Format:** Hybrid — 3 pre-recorded clips + 7 live typed interactions on Telegram

---

## Seeded Data Reference (what the judges will see in background)

| Commodity | Stock | Days Left (expiry) | Velocity | Stockout in |
|-----------|-------|--------------------|----------|-------------|
| Tomato    | 800 kg | 3 days             | ~400 kg/day | **2 days** |
| Cili      | 180 kg | 7 days             | ~60 kg/day  | **3 days** |
| Bayam     | 920 kg | **1 day** ⚠️      | ~90 kg/day  | 10 days    |
| Kangkung  | 240 kg | **1 day** ⚠️      | ~80 kg/day  | 3 days     |
| Timun     | 350 kg | 5 days             | ~100 kg/day | 3.5 days   |

**Credit outstanding:**
- Kedai Pak Hamid: RM 1,400 — **overdue 1 day**
- Restoran Maju: RM 2,200 — due in 4 days
- Kedai Uncle Wong: RM 600 — due in 6 days

**Financial profile:** ~RM 15,500/week revenue, 60 days data, score ~78/100 → **eligible RM 15,000 loan**

**Upcoming festival:** Hari Raya Aidiladha — 2026-06-07 (**36 days away**)

---

## PRE-RECORDED CLIPS (record these before the pitch)

### Clip 1 — Morning Brief (3:30 AM auto-trigger)
```
Command: /trigger_brief morning
```
**What it shows:** Stocky fires without being asked — proactive partner.  
Expected output includes: bayam expiry warning, kangkung expiry warning, overdue credit alert (Pak Hamid), weather + buy recommendation for tomato, savings footer "💚 Stocky jimatkan RM X bulan ini."

**Narration script:** *"Every morning at 3:30 AM, before Pak Zulkifli even gets to the market, Stocky has already checked his stock, his credit, the weather, and built him a plan for the day."*

---

### Clip 2 — Weekly Digest + Instinct (Monday auto-trigger)
```
Command: /trigger_brief digest
```
**What it shows:** 7-day revenue breakdown, Stocky's Instinct cross-signal finding, dashboard link.  
Expected output: revenue by commodity, instinct observation (e.g. "bayam selling 40% slower than tomato but occupying same shelf life — review your bayam buy volume"), dashboard link.

**Narration script:** *"Monday morning, Stocky sends a business review — not just numbers, but one insight the trader probably hasn't noticed."*

---

### Clip 3 — Spoilage Check (8 AM conditional trigger)
```
Command: /trigger_brief spoilage
```
**What it shows:** Only fires if stock at risk within 48 hours. With bayam at 1 day remaining.  
Expected output: "⚠️ Bayam 920kg — expires TOMORROW. Rain forecast Wednesday. Jual hari ini, offer at discount if needed."

**Narration script:** *"Stocky doesn't spam. It only fires when something needs your attention — and it tells you what to do, not just what's wrong."*

---

## LIVE SCENES (type these during the pitch)

### Scene 1 — Forwarded Supplier Quote → Buy Decision → Capital Check (90 sec)

**Setup:** "Pak Zulkifli just got a WhatsApp from Pak Ali. He forwards it straight to Stocky."

**Forward this message into the bot** (or type):
```
[forward from Pak Ali]
Tomato available 1 tan (1000kg) @ RM2.40/kg. Stok fresh, ready hantar esok.
```

**Expected response — Stocky calls `analyze_supplier_quote`:**
```
✅ TOMATO @ RM2.40/kg — BELI

📊 Perbandingan Harga:
• Harga terendah awak beli sebelum ni: RM2.55/kg
• FAMA benchmark minggu ni: RM2.75/kg
• Harga ini: 13% BAWAH FAMA — harga terbaik dalam 2 bulan

💰 Analisa Untung (jual @ RM3.20/kg purata):
• Margin: ~33%
• Untung per kg: RM0.80
• Untung total (1,000kg): RM800

🛒 Harga Jual Disyorkan: RM2.88/kg (margin 20%)

Modal yang perlu: RM2,400. Awak ada modal ni sekarang?
```

**Talking point:** *"He didn't have to open a spreadsheet. He didn't have to remember what he paid last week. Stocky pulled his 60-day history, compared against FAMA, calculated margin — and gave him a BUY decision in 3 seconds."*

**Then type:** `takda, modal tak cukup sekarang`

**Expected response — Stocky calls `get_financial_profile`:**
```
Stocky nampak awak layak untuk modal kerja RM15,000 dari Agrobank.

🏦 PAKEJ PERMOHONAN MODAL KERJA
Program: Digital Niaga — Agrobank (RM300 juta pool untuk PKS)

Pak Zulkifli | Skor: 78/100 | RM15,526/minggu | 60 hari rekod
Kadar bayaran tepat masa: 67%

💳 Jumlah: RM2,500 (atau sehingga RM15,000)
AgroCash-i — tiada cagaran | Bayar balik 30–90 hari

📋 Cara Mohon (Tiada Kunjungan Cawangan):
1️⃣ market.borong.com/my/partnership
2️⃣ Daftar Digital Niaga Program
3️⃣ Agrobank nilai dari data transaksi awak terus
Keputusan: 3–5 hari bekerja

Atau order 500kg dulu (RM1,200) — tengok velocity, top up esok.
```

**Talking point:** *"He doesn't have the cash. Stocky knows his transaction history — 60 days of real data. It says: you qualify for RM15,000. Here's the exact steps to apply digitally, no branch visit. That's embedded finance in a Telegram chat."*

---

### Scene 2 — Stock Situation Check (30 sec)

**Setup:** "Let me show you the live bot — I'll be Pak Zulkifli right now."

**Type in Telegram:**
```
good morning stocky. apa yang perlu aku buat hari ni?
```

**Expected response:**
- Calls `get_inventory` → bayam 1 day, kangkung 1 day flagged
- Calls `get_outstanding_credit` → Pak Hamid overdue mentioned
- Morning summary: what to sell today, who to call about payment

**Talking point:** *"He asked a simple question — Stocky read his entire stock, found two items expiring tomorrow, and spotted an overdue payment without being asked."*

---

### Scene 2 — Commodity Insight + Buy Decision (45 sec)

**Type in Telegram:**
```
tomato macam mana? patut beli lagi tak?
```

**Expected response:**
1. Calls `get_commodity_insight("tomato")` → velocity 400kg/day, stockout in 2 days
2. Calls `compare_supplier_prices("tomato")` → Pak Ali RM2.55/kg, FAMA RM2.75 (-7.3%)
3. Calls `get_weather_forecast()` → check rain risk

**Expected output (approx):**
```
🔮 Tomato jual ~400kg/hari minggu ni — stok tinggal 2 hari saja.
Pak Ali offer RM2.55/kg, 7% bawah FAMA. Lock in before weekend.

🟢 Pak Ali | RM2.55/kg | -7.3% vs FAMA | Beli sehingga 1,000kg
🔴 Ah Seng | RM2.90/kg | +5.5% vs FAMA | Skip

🛒 Cadangan: Hubungi Pak Ali hari ni, order 800-1,000kg.
```

**Talking point:** *"This is not just data extraction — it read velocity, shelf life, weather and supplier prices together, then gave ONE actionable decision. That's a business partner."*

**Optional:** Ask Stocky to draft the message to Pak Ali:
```
draft message to Pak Ali in Malay to order 1000kg tomato
```
Expected: `DRAFT_MESSAGE::Pak Ali::malay::Assalamualaikum Pak Ali, boleh sediakan 1,000kg tomato hari ni? ...`

---

### Scene 3 — Festival Demand Intelligence (30 sec)

**Type in Telegram:**
```
raya haji berapa hari lagi? cili cukup tak?
```

**Expected response:**
1. Calls `search_market_news("raya haji aidiladha", "festival")` → Aidiladha 36 days away
2. Calls `get_commodity_insight("cili")` → 180kg, 60kg/day, stockout in 3 days
3. Cross-references: "cili habis dalam 3 hari, but you need stock for Raya Haji in 36 days"

**Expected output (approx):**
```
🗓️ Hari Raya Aidiladha — 7 Jun 2026, dalam 36 hari.
Permintaan cili, tomato, timun akan naik 2 minggu sebelum raya.

⚠️ Tapi cili awak tinggal 180kg — habis dalam 3 hari pada kadar sekarang.
Order sekarang. Pak Ali offer RM4.00/kg (FAMA RM4.10, -2.4%).

🛒 Cadangan: Order 400kg cili hari ni, restock lagi seminggu sebelum Raya Haji.
```

**Talking point:** *"It knew Raya Haji demand profile, compared it with current velocity, and told him not just the festival date — but that his stock runs out 33 days before the festival. That's anticipation."*

---

### Scene 4 — Market News Search (30 sec)

**Type in Telegram:**
```
ada berita banjir atau supply problem yang affect tomato sekarang?
```

**Expected response:**
1. Calls `search_market_news("banjir tomato supply Malaysia", "news")` → DuckDuckGo live results
2. Summarises relevance to current stock and buy decision

**Expected output (approx):**
```
📰 Carian: "banjir tomato supply Malaysia 2026"

[If results found:]
Dijumpai berita berkaitan — [snippet]. Ini mungkin affect harga minggu depan.
Dengan stok tinggal 2 hari, lock in harga Pak Ali sekarang sebelum harga naik.

[If no results:]
Tiada gangguan bekalan besar dijumpai setakat ini.
Cadangan: pantau FAMA dan Bernama jika harga Pak Ali naik minggu depan.
```

**Talking point:** *"Stocky searches live news — floods, supply disruptions, price spikes — and filters it down to: does this affect YOUR stock and YOUR buy decision today. Not a news feed, a business signal."*

---

### Scene 5 — Credit Management + Draft Message (45 sec)

**Type in Telegram:**
```
siapa yang masih hutang aku? dah overdue ke?
```

**Expected response:**
1. Calls `get_outstanding_credit()` → 3 open receivables
2. Highlights Pak Hamid (overdue 1 day, RM1,400)

**Expected output (approx):**
```
💸 Kedai Pak Hamid | RM1,400 | ⚠️ Overdue 1 hari (bayam)
💸 Restoran Maju   | RM2,200 | Due dalam 4 hari (tomato)
💸 Kedai Uncle Wong| RM600   | Due dalam 6 hari (cili)

Total outstanding: RM4,200. Draft reminder untuk Pak Hamid?
```

**Then type:**
```
yes, draft reminder for Pak Hamid in Malay
```

Expected:
```
DRAFT_MESSAGE::Kedai Pak Hamid::malay::Assalamualaikum Pak Hamid, sekadar mengingatkan pembayaran RM1,400 untuk bayam sudah lewat 1 hari. Boleh settle hari ni? Terima kasih.
```

**Talking point:** *"Stocky never sends anything without approval. It drafts the right message in the right language — Pak Hamid speaks Malay, so it drafts in Malay — and waits for Pak Zulkifli to press send. The wholesaler stays in control."*

---

### Scene 6 — Financial Profile + Loan Offer + Dashboard (45 sec)

**Type in Telegram:**
```
profil saya macam mana? layak pinjaman tak?
```

**Expected response:**
1. Calls `get_financial_profile()` → computes creditworthiness from 60 days of data

**Expected output (approx):**
```
🏦 PROFIL KEWANGAN — Pak Zulkifli

Skor Kredit: 78/100 ✅ Layak

📊 Revenue Mingguan Purata: RM15,526
💚 Jimat vs FAMA (30 hari): RM1,240
📈 Kadar Kutipan Hutang: 66.7%
⏱️ Masa Kutip Purata: 6 hari

✅ TAWARAN MODAL KERJA: RM 15,000
Program: AgroCash-i / Agrobank
Tiada cagaran. Keputusan dalam 3 hari bekerja.

Nak apply? Taip "mohon pinjaman" dan Stocky sediakan surat rujukan.

📈 Dashboard penuh awak: https://stocky-ai-dashboard.lovable.app/
```

**Talking point:** *"No bank visit. No paperwork. Stocky built a credit profile from 60 days of real trading data — revenue, collection rate, supplier savings — and told him he qualifies for RM15,000 today. This is financial inclusion for people who've never had a formal credit history."*

**Show dashboard link live:** Open https://stocky-ai-dashboard.lovable.app/ on screen.

---

## Demo Flow Summary (total ~5 min)

| # | Type | What it shows | Time |
|---|------|---------------|------|
| Clip 1 | Pre-recorded | Proactive morning brief — no prompt needed | 30s |
| Clip 2 | Pre-recorded | Weekly digest + Instinct cross-signal | 20s |
| Clip 3 | Pre-recorded | Conditional spoilage alert | 20s |
| Scene 1 | **Live** | **Forwarded supplier quote → buy decision → capital check → loan application** | 90s |
| Scene 2 | Live | Stock overview + proactive credit flag | 30s |
| Scene 3 | Live | Commodity insight + supplier buy decision | 45s |
| Scene 4 | Live | Festival demand + cili velocity cross-signal | 30s |
| Scene 5 | Live | Live news search (DuckDuckGo) | 30s |
| Scene 6 | Live | Credit tracking + draft reminder message | 45s |
| Scene 7 | Live | Financial profile + loan eligibility + dashboard | 45s |

---

## Key Messages for Each Judge Question

**"How is this different from a chatbot?"**  
→ Stocky acts before you ask. The morning brief fires at 3:30 AM. Spoilage alerts fire when risk is detected. Velocity alerts fire when something changes. A chatbot waits — Stocky watches.

**"What happens if the user doesn't log data?"**  
→ Stocky works from what it has and says so: "I don't have supplier price history yet — log a delivery and I'll start tracking." It never invents numbers.

**"How does the financial profile work?"**  
→ Every buy and sell logged in Stocky builds a transaction history. After 30+ days, the engine computes revenue stability, collection rate, supplier savings and FAMA comparison, and generates a creditworthiness score. No bank needs to visit the trader.

**"Is the data secure?"**  
→ Each trader has their own profile. No data is shared between users. Stocky drafts messages but never sends — the trader controls all communications.

**"What's the business model?"**  
→ Free for traders. Revenue from financial institutions (Agrobank) paying per qualified referral. Stocky creates the financial data that makes micro-lending viable.

---

## If Something Goes Wrong

| Issue | Recovery |
|-------|---------|
| Bot slow / LLM timeout | Show pre-recorded clips, explain "live demo dependency on ILMU API" |
| No DuckDuckGo results in Scene 4 | Show the graceful fallback message — *"this is intentional: if news isn't found, Stocky tells you to check FAMA directly"* |
| Festival returns wrong result | Type "raya haji" or "aidiladha" specifically to trigger Aidiladha (not "raya" which might match past Aidilfitri) |
| Financial score lower than expected | A lower score is still valid — use it to demo the "what to improve" path |
