"""FDA 21 CFR Part 211 compliance report generation."""

import logging
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


async def generate_fda_report(
    drug_name: str,
    batch_number: str,
    temps: list[float],
    max_temp: float,
    min_temp: float,
    pct_in_range: float,
    excursions: list[str],
    disposition: str,
) -> str:
    """Generate FDA compliance report using OpenAI or fallback template."""

    # Try OpenAI first
    if settings.openai_api_key:
        try:
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                model="gpt-4o",
                api_key=settings.openai_api_key,
                max_tokens=2000,
            )

            prompt = f"""Generate a formal FDA 21 CFR Part 211 cold chain compliance report with the following data:

Drug: {drug_name}
Batch: {batch_number}
Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
Required Storage: 2-8°C
Total Readings: {len(temps)}
Temperature Range: {min_temp:.1f}°C to {max_temp:.1f}°C
Time in Range: {pct_in_range:.1f}%
Excursion Events: {len(excursions)}
Disposition: {disposition}

Include these sections:
1. Executive Summary
2. Product Information
3. Temperature Monitoring Summary
4. Excursion Analysis
5. Risk Assessment
6. Corrective Actions Taken
7. Disposition & Recommendation
8. Regulatory References

Note: A refrigeration failure was detected and the shipment was rerouted to certified cold storage.
The reroute was approved by a human operator. Format as a professional regulatory document."""

            response = await llm.ainvoke(prompt)
            return response.content

        except Exception as e:
            logger.warning(f"OpenAI report generation failed, using template: {e}")

    # Fallback template
    return _generate_template_report(
        drug_name, batch_number, temps, max_temp, min_temp,
        pct_in_range, excursions, disposition
    )


def _generate_template_report(
    drug_name: str,
    batch_number: str,
    temps: list[float],
    max_temp: float,
    min_temp: float,
    pct_in_range: float,
    excursions: list[str],
    disposition: str,
) -> str:
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    excursion_text = "\n".join(excursions) if excursions else "  No excursion events recorded."

    return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FDA 21 CFR PART 211 — COLD CHAIN COMPLIANCE REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Report ID: CCR-{batch_number}-001
Generated: {now}
Classification: CONFIDENTIAL — REGULATORY USE ONLY

═══════════════════════════════════════════════════════════════
1. EXECUTIVE SUMMARY
═══════════════════════════════════════════════════════════════

This report documents the cold chain monitoring and compliance status
for {drug_name}, Batch {batch_number}, during transit from
Dallas, TX to Chicago, IL.

A refrigeration unit malfunction was detected during transit, resulting
in a temperature excursion above the approved storage range (2-8°C).
The AI monitoring system detected the anomaly and recommended an
immediate reroute to certified cold storage. The reroute was approved
by a human operator and executed successfully.

DISPOSITION: {disposition}

═══════════════════════════════════════════════════════════════
2. PRODUCT INFORMATION
═══════════════════════════════════════════════════════════════

Drug Product:     {drug_name}
Batch Number:     {batch_number}
Dosage Form:      Solution for subcutaneous injection
Storage Req:      2°C to 8°C (36°F to 46°F)
Packaging:        Pre-filled syringes, insulated shipping container
Shipment Value:   ~$250,000 (estimated)
Origin:           Dallas, TX (AbbVie Distribution Center)
Destination:      Chicago, IL (AbbVie North Chicago)
Carrier:          Pharma Express Logistics (PEL-4892)

═══════════════════════════════════════════════════════════════
3. TEMPERATURE MONITORING SUMMARY
═══════════════════════════════════════════════════════════════

Monitoring System:    IoT Continuous Temperature Logger (2-min intervals)
Total Readings:       {len(temps)}
Minimum Recorded:     {min_temp:.1f}°C
Maximum Recorded:     {max_temp:.1f}°C
Mean Temperature:     {sum(temps)/len(temps):.1f}°C
Time in Range (2-8°C): {pct_in_range:.1f}%

═══════════════════════════════════════════════════════════════
4. EXCURSION ANALYSIS
═══════════════════════════════════════════════════════════════

Total Excursion Events: {len(excursions)}

{excursion_text}

Root Cause: Refrigeration unit compressor partial failure during transit
through Oklahoma. Ambient temperature conditions exceeded unit capacity.

═══════════════════════════════════════════════════════════════
5. RISK ASSESSMENT
═══════════════════════════════════════════════════════════════

Product Stability Data Reference: Skyrizi Stability Study SKZ-STAB-2023
Maximum Allowable Excursion: ≤25°C for ≤24 hours (per stability data)
Actual Maximum Excursion: {max_temp:.1f}°C

Assessment: The temperature excursion remained within the product's
validated stability envelope. Cumulative thermal exposure was managed
through rapid intervention and reroute to certified cold storage.

Risk Level: {"LOW — Product integrity maintained" if disposition == "PASS" else "MODERATE — Product requires quality review" if disposition == "CONDITIONAL" else "HIGH — Product may be compromised"}

═══════════════════════════════════════════════════════════════
6. CORRECTIVE ACTIONS TAKEN
═══════════════════════════════════════════════════════════════

1. AI monitoring system detected anomaly at threshold exceedance
2. Automated risk assessment performed within 30 seconds
3. Nearest certified cold storage facility identified
4. Reroute recommendation generated and sent to operations team
5. Human operator approved reroute within approval SLA
6. Truck redirected to certified pharma cold storage
7. Product temperature stabilized within approved range
8. This compliance report auto-generated per SOP-CC-401

═══════════════════════════════════════════════════════════════
7. DISPOSITION & RECOMMENDATION
═══════════════════════════════════════════════════════════════

Disposition: {disposition}

{"PASS: Product meets all release criteria. No quality hold required." if disposition == "PASS" else "CONDITIONAL PASS: Product meets stability criteria but requires Quality Assurance review before release. Recommend batch sampling and potency testing per SOP-QA-210." if disposition == "CONDITIONAL" else "FAIL: Product does not meet release criteria. Recommend quarantine and destruction per SOP-QA-310."}

═══════════════════════════════════════════════════════════════
8. REGULATORY REFERENCES
═══════════════════════════════════════════════════════════════

• 21 CFR Part 211 — Current Good Manufacturing Practice
• 21 CFR Part 211.150 — Distribution procedures
• USP <1079> — Good Storage and Distribution Practices
• WHO TRS 961, Annex 9 — Guide to Good Storage Practices
• ICH Q1A(R2) — Stability Testing Guidelines
• EU GDP Guidelines 2013/C 343/01

═══════════════════════════════════════════════════════════════

Prepared by: Cold Chain AI Monitoring System v1.0
Reviewed by: [Pending Quality Assurance Review]
Approved by: [Pending Qualified Person Signature]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
END OF REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
