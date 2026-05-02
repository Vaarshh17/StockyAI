"""
agent/finance.py — Trader Financial Profile & Loan Eligibility Engine.

Turns 30-90 days of trading data into a creditworthiness signal.
Every metric comes from tables that already exist — no new data sources needed.
"""
import logging
import math
from datetime import date

logger = logging.getLogger(__name__)

# Agrobank AgroCash-i benchmark thresholds
MIN_DATA_DAYS = 14
MIN_WEEKLY_REVENUE_RM = 500.0
MIN_SCORE = 60
MAX_LOAN_RM = 15000.0
MIN_LOAN_RM = 1000.0


async def calculate_financial_profile(user_id: int) -> dict:
    """
    Compute creditworthiness from transaction history.
    Scoring breakdown (total 100 pts):
      Revenue stability  — 30 pts (CoV of weekly revenue)
      Data depth         — 20 pts (linear scale 14 → 90 days)
      Collection rate    — 25 pts (% receivables paid)
      Overdue rate       — 15 pts (inverse: 0% overdue = 15)
      Cash flow speed    — 10 pts (avg days to collect, decay 7 → 30)
    """
    from db.queries import db_calc_financial_data
    data = await db_calc_financial_data()

    avg_weekly_revenue  = data["avg_weekly_revenue_rm"]
    weekly_revenues     = data["weekly_revenues"]
    total_data_days     = data["total_data_days"]
    collection_rate     = data["receivables_collection_rate_pct"]
    overdue_rate        = data["overdue_rate_pct"]
    avg_days_to_collect = data["avg_days_to_collect"]
    total_outstanding   = data["total_outstanding_rm"]
    total_savings       = data["total_savings_rm"]
    savings_30d         = data["total_savings_30d_rm"]

    # ── 1. Revenue stability (30 pts) — CoV-based ─────────────────
    rev_score = 0
    if len(weekly_revenues) >= 2:
        mean = sum(weekly_revenues) / len(weekly_revenues)
        if mean > 0:
            variance = sum((x - mean) ** 2 for x in weekly_revenues) / len(weekly_revenues)
            cov = math.sqrt(variance) / mean
            if cov < 0.15:
                rev_score = 30
            elif cov < 0.25:
                rev_score = 22
            elif cov < 0.40:
                rev_score = 15
            elif cov < 0.60:
                rev_score = 8
            else:
                rev_score = 3
    elif avg_weekly_revenue > 0:
        rev_score = 8  # partial credit for single-week data

    # ── 2. Data depth (20 pts) — linear 14 → 90 days ──────────────
    if total_data_days >= 90:
        depth_score = 20
    elif total_data_days >= 14:
        depth_score = round((total_data_days - 14) / (90 - 14) * 20)
    else:
        depth_score = 0

    # ── 3. Collection rate (25 pts) — linear ──────────────────────
    collection_score = round(collection_rate / 100 * 25)

    # ── 4. Overdue rate (15 pts) — inverse linear ─────────────────
    overdue_score = round(max(0.0, 1.0 - overdue_rate / 100) * 15)

    # ── 5. Cash flow speed (10 pts) — decay 7 → 30 days ──────────
    if avg_days_to_collect <= 7:
        cashflow_score = 10
    elif avg_days_to_collect <= 30:
        cashflow_score = round((30 - avg_days_to_collect) / (30 - 7) * 10)
    else:
        cashflow_score = 0

    total_score = max(0, min(100, rev_score + depth_score + collection_score + overdue_score + cashflow_score))

    # ── Eligibility & loan amount ──────────────────────────────────
    eligible = (
        total_score >= MIN_SCORE
        and total_data_days >= MIN_DATA_DAYS
        and avg_weekly_revenue >= MIN_WEEKLY_REVENUE_RM
    )
    if eligible:
        raw = avg_weekly_revenue * 2
        loan_amount = round(max(MIN_LOAN_RM, min(MAX_LOAN_RM, raw)) / 500) * 500
    else:
        loan_amount = 0.0

    return {
        "user_id": user_id,
        "computed_at": date.today().isoformat(),
        "total_data_days": total_data_days,
        "avg_weekly_revenue_rm": round(avg_weekly_revenue, 2),
        "total_savings_rm": round(total_savings, 2),
        "total_savings_30d_rm": round(savings_30d, 2),
        "receivables_collection_rate_pct": round(collection_rate, 1),
        "overdue_rate_pct": round(overdue_rate, 1),
        "avg_days_to_collect": round(avg_days_to_collect, 1),
        "total_outstanding_rm": round(total_outstanding, 2),
        "creditworthiness_score": total_score,
        "score_breakdown": {
            "revenue_stability": rev_score,
            "data_depth": depth_score,
            "collection_rate": collection_score,
            "overdue_rate": overdue_score,
            "cashflow_speed": cashflow_score,
        },
        "eligible_for_loan": eligible,
        "loan_amount_rm": loan_amount,
    }


def format_profile_message(profile: dict, name: str = "Peniaga") -> str:
    """Full financial profile card — used by /trigger_finance and 'profil saya' queries."""
    score = profile["creditworthiness_score"]

    if score >= 75:
        score_label = "🟢 Cemerlang"
    elif score >= 60:
        score_label = "🟡 Baik"
    elif score >= 40:
        score_label = "🟠 Sederhana"
    else:
        score_label = "🔴 Perlu Tingkatkan"

    savings_30d = profile.get("total_savings_30d_rm", 0)
    bd = profile.get("score_breakdown", {})

    lines = [
        f"📊 *Profil Kewangan Stocky — {name}*",
        "",
        f"📅 Rekod perniagaan: *{profile['total_data_days']} hari*",
        f"💰 Pendapatan min./minggu: *RM{profile['avg_weekly_revenue_rm']:,.0f}*",
        f"💚 Jimat dari FAMA (30 hari): *RM{savings_30d:,.0f}*",
        f"✅ Kadar kutip hutang: *{profile['receivables_collection_rate_pct']:.0f}%*",
        f"⏱️  Masa kutip bayaran: *{profile['avg_days_to_collect']:.0f} hari*",
        f"💸 Baki hutang tertunggak: *RM{profile['total_outstanding_rm']:,.0f}*",
        "",
        f"🏦 *Skor Kreditworthiness: {score}/100 — {score_label}*",
        f"   Kestabilan pendapatan: {bd.get('revenue_stability', 0)}/30",
        f"   Kedalaman rekod: {bd.get('data_depth', 0)}/20",
        f"   Kadar kutipan: {bd.get('collection_rate', 0)}/25",
        f"   Kadar tunggakan: {bd.get('overdue_rate', 0)}/15",
        f"   Kelajuan kutipan: {bd.get('cashflow_speed', 0)}/10",
    ]

    if profile["eligible_for_loan"]:
        lines += [
            "",
            f"✨ *Tahniah! Awak layak untuk:*",
            f"💳 Modal kerja *RM{profile['loan_amount_rm']:,.0f}* (AgroCash-i, Agrobank)",
            f"📅 Bayar balik: 30–90 hari",
            "",
            "Taip *'mohon pinjaman'* untuk Stocky sediakan pakej permohonan.",
        ]
    else:
        gaps = _eligibility_gaps(profile)
        if gaps:
            lines += ["", "📈 *Untuk layak, awak perlu:*"] + [f"   • {g}" for g in gaps]

    return "\n".join(lines)


def format_loan_offer_message(profile: dict, name: str = "Peniaga") -> str:
    """Proactive offer message — sent by the weekly scheduler job."""
    savings_30d = profile.get("total_savings_30d_rm", 0)
    col_rate = profile["receivables_collection_rate_pct"]

    return (
        f"🏦 *Tawaran Modal Kerja — {name}*\n\n"
        f"Berdasarkan *{profile['total_data_days']} hari* rekod perniagaan awak:\n\n"
        f"💚 Stocky telah jimat *RM{savings_30d:,.0f}* untuk awak bulan ini\n"
        f"💰 Jualan purata *RM{profile['avg_weekly_revenue_rm']:,.0f}*/minggu\n"
        f"✅ *{col_rate:.0f}%* pembeli bayar tepat masa\n\n"
        f"Awak layak untuk:\n"
        f"💳 *RM{profile['loan_amount_rm']:,.0f}* — Modal Kerja AgroCash-i (Agrobank)\n"
        f"📅 Bayar balik dalam 30–90 hari\n"
        f"📊 Skor kewangan awak: *{profile['creditworthiness_score']}/100*\n\n"
        f"_Data ini dihasilkan dari rekod sebenar perniagaan awak — bukan anggaran._\n\n"
        f"Taip *'tunjuk profil saya'* untuk butiran lengkap."
    )


def format_savings_footer(savings_30d_rm: float) -> str:
    """One-line footer appended to the morning brief."""
    if savings_30d_rm < 10:
        return ""
    return f"\n\n💚 _Stocky telah jimat RM{savings_30d_rm:,.0f} untuk awak bulan ini._"


def format_loan_application_package(profile: dict, name: str = "Peniaga", amount_rm: float = None) -> str:
    """
    Full Digital Niaga / Agrobank application package.
    Presented when user says 'apply loan' or 'mohon pinjaman' after a capital check.
    Based on Borong–Agrobank Digital Niaga Program (RM300M pool).
    """
    loan_amount = amount_rm or profile.get("loan_amount_rm", 0)
    score = profile["creditworthiness_score"]
    weekly_rev = profile["avg_weekly_revenue_rm"]
    data_days = profile["total_data_days"]
    col_rate = profile["receivables_collection_rate_pct"]
    savings = profile.get("total_savings_30d_rm", 0)

    lines = [
        "🏦 *PAKEJ PERMOHONAN MODAL KERJA*",
        "_Program: Digital Niaga — Agrobank (RM300 juta pool untuk PKS)_",
        "",
        f"👤 Nama: *{name}*",
        f"📊 Skor Kewangan Stocky: *{score}/100*",
        f"💰 Pendapatan Min./Minggu: *RM{weekly_rev:,.0f}*",
        f"📅 Rekod Perniagaan: *{data_days} hari*",
        f"✅ Kadar Bayaran Tepat Masa: *{col_rate:.0f}%*",
        f"💚 Jimat dari FAMA (30 hari): *RM{savings:,.0f}*",
        "",
        f"💳 *Jumlah Dipohon: RM{loan_amount:,.0f}*",
        "   Produk: AgroCash-i (Modal Kerja Tanpa Cagaran)",
        "   Bayar Balik: 30–90 hari",
        "   Keputusan: 3–5 hari bekerja",
        "",
        "📋 *Cara Mohon (Digital — Tiada Kunjungan Cawangan):*",
        "1️⃣  Buka: market.borong.com/my/partnership",
        "2️⃣  Daftar Digital Niaga Program",
        "3️⃣  Kongsi data perniagaan (consent-based) dengan Agrobank",
        "4️⃣  Agrobank nilai berdasarkan data transaksi awak",
        "",
        "📞 *Hubungi Agrobank terus:*",
        "   Tel: 1-300-88-2476",
        "   Web: www.agrobank.com.my",
        "",
        "_Data ini dihasilkan terus dari rekod perniagaan sebenar awak._",
        "_Tiada dokumen manual diperlukan untuk penilaian awal._",
    ]
    return "\n".join(lines)


def _eligibility_gaps(profile: dict) -> list[str]:
    gaps = []
    if profile["total_data_days"] < MIN_DATA_DAYS:
        needed = MIN_DATA_DAYS - profile["total_data_days"]
        gaps.append(f"Log lagi {needed} hari data perniagaan")
    if profile["avg_weekly_revenue_rm"] < MIN_WEEKLY_REVENUE_RM:
        gaps.append(f"Pendapatan mingguan perlu ≥ RM{MIN_WEEKLY_REVENUE_RM:.0f}")
    if profile["creditworthiness_score"] < MIN_SCORE:
        if profile["receivables_collection_rate_pct"] < 70:
            gaps.append("Tingkatkan kadar kutipan hutang pembeli")
        if profile["overdue_rate_pct"] > 30:
            gaps.append("Kurangkan hutang yang tertunggak")
    return gaps
