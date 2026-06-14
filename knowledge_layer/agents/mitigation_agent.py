"""
mitigation_agent.py
-------------------
Mitigation Agent — LLM driven.

Consumes the full MOSIPState context (risk, compliance, forecast, sustainability)
to produce concrete, actionable mitigation recommendations.

Outputs:
  - Primary recommendation (deorbit / orbit raise / relocation / ADR)
  - Ranked list of specific actions
  - Expected improvement if actions taken
  - Cost/complexity assessment
  - Urgency classification

Answers:
  - What should be done?
  - What is the most impactful single action?
  - How urgent is intervention?
"""

from datetime import datetime
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from backend.config import GROQ_API_KEY, GROQ_MODEL
from knowledge_layer.agents.state import MOSIPState


def _urgency(risk_level: str, compliance_level: str) -> str:
    if risk_level == "CRITICAL" or compliance_level == "NON_COMPLIANT":
        return "IMMEDIATE"
    if risk_level == "HIGH" or compliance_level == "PARTIAL":
        return "NEAR_TERM"
    if risk_level == "MEDIUM":
        return "PLANNED"
    return "ROUTINE"


def _build_mitigation_prompt(state: MOSIPState) -> str:
    satellite   = state.get("satellite_data", {})
    orbital     = state.get("orbital_data", {})
    risk        = state.get("risk_data", {})
    compliance  = state.get("compliance_analysis", {})
    forecast    = state.get("forecast", {})
    sustain     = state.get("sustainability_analysis", {})

    violations  = compliance.get("failed_requirements", [])
    violations_text = "\n".join(f"  - {v}" for v in violations) if violations else "  None identified"

    forecast_25 = forecast.get("projections", {}).get("25yr", {})

    return f"""
You are MOSIP's Mitigation Agent — a space operations and debris mitigation expert.

SATELLITE:
- Name: {satellite.get("object_name", "Unknown")} (NORAD: {satellite.get("norad_id", "N/A")})
- Orbit: {orbital.get("orbit_type", "UNKNOWN")} @ {orbital.get("altitude_km", "N/A")} km
- Inclination: {orbital.get("inclination", "N/A")}°

RISK ASSESSMENT:
- Score: {risk.get("risk_score", "N/A")}/100 ({risk.get("risk_level", "UNKNOWN")})
- Primary drivers: {", ".join(risk.get("risk_drivers", [])[:3])}

COMPLIANCE VIOLATIONS:
{violations_text}

SUSTAINABILITY:
- Sustainability Index: {sustain.get("sustainability_index", "N/A")}/100
- Level: {sustain.get("sustainability_level", "UNKNOWN")}
- Orbital lifetime: {sustain.get("orbital_lifetime", "Unknown")}

FORECAST (25 years):
- Projected risk score: {forecast_25.get("projected_risk_score", "N/A")}
- Shell growth: {forecast_25.get("shell_growth_pct", "N/A")}%
- Collision probability: {forecast_25.get("projected_collision_prob_per_yr", "N/A")}

Generate specific mitigation recommendations as valid JSON:
{{
    "urgency": "<IMMEDIATE|NEAR_TERM|PLANNED|ROUTINE>",
    "primary_recommendation": "<single most impactful action>",
    "recommendations": [
        {{
            "action": "<specific action>",
            "rationale": "<why this action>",
            "expected_improvement": "<what metric improves and by how much>",
            "complexity": "<LOW|MEDIUM|HIGH>",
            "timeframe": "<e.g., 0-6 months, 1-2 years>"
        }}
    ],
    "deorbit_options": {{
        "natural_decay": "<yes/no and estimated years>",
        "propulsive_deorbit": "<feasibility and timeline>",
        "adr_candidate": "<yes/no with justification>"
    }},
    "expected_risk_reduction": "<percentage or points reduction if recommendations followed>",
    "mitigation_summary": "<2-3 sentences on overall mitigation strategy>"
}}
Provide 3-5 specific recommendations. Prioritize by impact.
"""


def run_mitigation_agent(state: MOSIPState) -> dict:
    """
    Mitigation Agent node.
    Adds 'mitigation_analysis', 'recommendations', appends to 'agent_timeline'.
    """
    risk       = state.get("risk_data", {})
    compliance = state.get("compliance_analysis", {})

    urgency = _urgency(
        risk.get("risk_level", "UNKNOWN"),
        compliance.get("compliance_level", "UNKNOWN"),
    )

    try:
        llm = ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL,
                       temperature=0.2, max_tokens=1200)

        prompt = _build_mitigation_prompt(state)
        messages = [
            SystemMessage(content=(
                "You are a space operations and debris mitigation expert. "
                "Always respond with valid JSON only. No markdown, no text outside JSON."
            )),
            HumanMessage(content=prompt),
        ]

        response = llm.invoke(messages)
        raw_text = response.content.strip()

        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        raw_text = raw_text.strip()

        import json
        mitigation = json.loads(raw_text)

    except Exception as e:
        orbit_type = state.get("orbital_data", {}).get("orbit_type", "UNKNOWN")
        mitigation = {
            "urgency":                urgency,
            "primary_recommendation": f"Initiate post-mission disposal plan for {orbit_type} satellite",
            "recommendations": [
                {
                    "action":               "File post-mission disposal plan with regulatory authority",
                    "rationale":            "Mandatory under IADC 25-year rule",
                    "expected_improvement": "Compliance score improvement",
                    "complexity":           "LOW",
                    "timeframe":            "0-3 months",
                },
                {
                    "action":               "Perform passivation (deplete batteries and propellant)",
                    "rationale":            "Reduces explosion risk and debris generation",
                    "expected_improvement": "Reduces debris risk component",
                    "complexity":           "MEDIUM",
                    "timeframe":            "End of mission",
                },
            ],
            "deorbit_options": {
                "natural_decay":      "Depends on altitude — check lifetime estimate",
                "propulsive_deorbit": "Preferred if propulsion available",
                "adr_candidate":      "Evaluate if satellite is non-functional",
            },
            "expected_risk_reduction": "10-20% with full compliance",
            "mitigation_summary":      f"Standard {orbit_type} disposal protocol recommended. LLM error: {str(e)[:100]}",
            "llm_error":               str(e),
        }

    # Extract flat recommendation list for state
    rec_list = [
        r.get("action", "") for r in mitigation.get("recommendations", [])
        if r.get("action")
    ]

    timeline_entry = {
        "agent":     "Mitigation Agent",
        "status":    "complete",
        "timestamp": datetime.utcnow().isoformat(),
        "summary": (
            f"Urgency: {mitigation.get('urgency', urgency)} | "
            f"Primary: {mitigation.get('primary_recommendation', '')[:60]}..."
        ),
    }

    return {
        "mitigation_analysis": mitigation,
        "recommendations":     rec_list,
        "agent_timeline": state.get("agent_timeline", []) + [timeline_entry],
    }
