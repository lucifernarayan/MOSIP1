"""
documentation_agent.py
----------------------
Documentation Agent — LLM driven. Final synthesis.

Consumes the complete MOSIPState (all previous agent outputs) and
synthesizes a structured executive intelligence report.

Produces:
  - Executive Summary (3 sentences, decision-maker level)
  - Risk Intelligence section
  - Compliance Intelligence section
  - Sustainability Intelligence section
  - Mitigation Intelligence section
  - Forecast Intelligence section
  - One-line MOSIP verdict
"""

from datetime import datetime
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from backend.config import GROQ_API_KEY, GROQ_MODEL
from knowledge_layer.agents.state import MOSIPState


def _build_report_prompt(state: MOSIPState) -> str:
    satellite   = state.get("satellite_data", {})
    orbital     = state.get("orbital_data", {})
    risk        = state.get("risk_data", {})
    orbital_an  = state.get("orbital_analysis", {})
    collision   = state.get("collision_analysis", {})
    compliance  = state.get("compliance_analysis", {})
    sustain     = state.get("sustainability_analysis", {})
    forecast    = state.get("forecast", {})
    mitigation  = state.get("mitigation_analysis", {})

    top_rec = mitigation.get("primary_recommendation", "No recommendation generated")
    all_recs = mitigation.get("recommendations", [])
    recs_text = "\n".join(
        f"  {i+1}. {r.get('action', '')} ({r.get('timeframe', '')})"
        for i, r in enumerate(all_recs[:3])
    )

    violations = compliance.get("failed_requirements", [])
    violations_text = "\n".join(f"  - {v}" for v in violations[:3]) or "  None"

    forecast_5  = forecast.get("projections", {}).get("5yr", {})
    forecast_25 = forecast.get("projections", {}).get("25yr", {})

    return f"""
You are MOSIP's Documentation Agent. Synthesize the following multi-agent intelligence into a structured report.

=== SATELLITE ===
Name: {satellite.get("object_name", "Unknown")} | NORAD: {satellite.get("norad_id", "N/A")}
Orbit: {orbital.get("orbit_type", "UNKNOWN")} @ {orbital.get("altitude_km", "N/A")} km
Period: {orbital.get("period_minutes", "N/A")} min | Inclination: {orbital.get("inclination", "N/A")}°

=== RISK INTELLIGENCE ===
Score: {risk.get("risk_score", "N/A")}/100 ({risk.get("risk_level", "UNKNOWN")})
Collision component: {risk.get("collision_risk", "N/A")} | Debris: {risk.get("debris_risk", "N/A")} | Altitude: {risk.get("altitude_risk", "N/A")}
Primary drivers: {", ".join(risk.get("risk_drivers", [])[:3])}
Congestion: {orbital_an.get("congestion_level", "N/A")} ({orbital_an.get("neighbor_count_100km", "N/A")} objects in shell)
Orbital lifetime: {orbital_an.get("orbital_lifetime_estimate", "N/A")}

=== COMPLIANCE INTELLIGENCE ===
Score: {compliance.get("compliance_score", "N/A")}/100 ({compliance.get("compliance_level", "UNKNOWN")})
Violations:
{violations_text}
Summary: {compliance.get("compliance_summary", "N/A")}

=== SUSTAINABILITY INTELLIGENCE ===
Index: {sustain.get("sustainability_index", "N/A")}/100 ({sustain.get("sustainability_level", "UNKNOWN")})
Footprint: {sustain.get("orbital_footprint_score", "N/A")}/40 | Burden: {sustain.get("environmental_burden", "N/A")}/40
{sustain.get("narrative", "")}

=== FORECAST INTELLIGENCE ===
5yr: Risk score → {forecast_5.get("projected_risk_score", "N/A")} | Shell growth: +{forecast_5.get("shell_growth_pct", "N/A")}%
25yr: Risk score → {forecast_25.get("projected_risk_score", "N/A")} | Col. prob: {forecast_25.get("projected_collision_prob_per_yr", "N/A")}
Kessler risk: {forecast.get("kessler_syndrome_risk", "N/A")}

=== MITIGATION INTELLIGENCE ===
Urgency: {mitigation.get("urgency", "N/A")}
Primary: {top_rec}
Top actions:
{recs_text}

---
Write a professional MOSIP Intelligence Report with the following exact structure (use markdown headers):

# MOSIP Intelligence Report — [Satellite Name]
**Generated:** [current date/time]

## Executive Summary
[3 concise sentences for a decision-maker. State the key finding, the biggest risk, and the most critical action.]

## 🛰️ Risk Intelligence
[2-3 sentences covering risk score, primary drivers, and congestion context]

## ⚖️ Compliance Intelligence
[2-3 sentences: compliance score, key violations, regulatory gap]

## 🌍 Sustainability Intelligence
[2-3 sentences: sustainability index, orbital burden, long-term impact]

## 🔭 Forecast Intelligence
[2-3 sentences: 5-year and 25-year outlook, inflection points]

## 🛠️ Mitigation Intelligence
[2-3 sentences: urgency, primary recommendation, expected improvement]

## MOSIP Verdict
**[ONE sentence verdict on what the operator must do, written as a direct command]**
"""


def run_documentation_agent(state: MOSIPState) -> dict:
    """
    Documentation Agent node.
    Adds 'report' and finalises 'agent_timeline'.
    """
    satellite = state.get("satellite_data", {})
    sat_name  = satellite.get("object_name", "Unknown")

    try:
        llm = ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL,
                       temperature=0.4, max_tokens=1500)

        prompt = _build_report_prompt(state)
        messages = [
            SystemMessage(content=(
                "You are MOSIP's Documentation Agent — a world-class space intelligence analyst. "
                "Write precise, professional reports with clear findings and actionable conclusions. "
                "Use the exact markdown structure provided."
            )),
            HumanMessage(content=prompt),
        ]

        response = llm.invoke(messages)
        report = response.content.strip()

    except Exception as e:
        # Fallback structured report
        risk        = state.get("risk_data", {})
        compliance  = state.get("compliance_analysis", {})
        mitigation  = state.get("mitigation_analysis", {})

        report = f"""# MOSIP Intelligence Report — {sat_name}
**Generated:** {datetime.utcnow().isoformat()} UTC

## Executive Summary
{sat_name} is a {state.get("orbital_data", {}).get("orbit_type", "UNKNOWN")} satellite with risk score {risk.get("risk_score", "N/A")}/100. Compliance level is {compliance.get("compliance_level", "UNKNOWN")}. Immediate review of disposal plan is recommended.

## Risk Intelligence
Risk score: {risk.get("risk_score", "N/A")}/100 ({risk.get("risk_level", "UNKNOWN")}). Primary drivers: {", ".join(risk.get("risk_drivers", [])[:3])}.

## Compliance Intelligence
Compliance score: {compliance.get("compliance_score", "N/A")}/100. {compliance.get("compliance_summary", "Assessment incomplete.")}

## Sustainability Intelligence
{state.get("sustainability_analysis", {}).get("narrative", "Assessment incomplete.")}

## Forecast Intelligence
{state.get("forecast", {}).get("interpretation", "Forecast incomplete.")}

## Mitigation Intelligence
Urgency: {mitigation.get("urgency", "UNKNOWN")}. {mitigation.get("mitigation_summary", "Review recommended.")}

## MOSIP Verdict
**Operator must immediately initiate disposal compliance review and implement recommended mitigation actions.**

*Note: LLM report generation failed: {str(e)[:100]}*
"""

    timeline_entry = {
        "agent":     "Documentation Agent",
        "status":    "complete",
        "timestamp": datetime.utcnow().isoformat(),
        "summary":   f"Full intelligence report generated for {sat_name}",
    }

    return {
        "report":         report,
        "agent_timeline": state.get("agent_timeline", []) + [timeline_entry],
    }
