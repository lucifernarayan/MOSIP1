"""
compliance_agent.py
-------------------
Compliance Agent — LLM + Qdrant RAG.

This is MOSIP's strongest agent.

Steps:
  1. Pull retrieved regulations from state (already in MOSIPState.regulations)
  2. Build a structured prompt with satellite profile + regulation texts
  3. Call Groq LLM to grade compliance, identify violations, assign score
  4. Return structured compliance assessment

Answers:
  - Which regulations apply to this satellite?
  - Is the object compliant?
  - Which specific requirements are violated?
  - What is the compliance score?
"""

from datetime import datetime
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from backend.config import GROQ_API_KEY, GROQ_MODEL
from knowledge_layer.agents.state import MOSIPState


def _build_compliance_prompt(state: MOSIPState) -> str:
    """Build context-rich prompt for LLM compliance grading."""
    satellite   = state.get("satellite_data", {})
    orbital     = state.get("orbital_data", {})
    risk        = state.get("risk_data", {})
    regulations = state.get("regulations", [])

    sat_name    = satellite.get("object_name", "Unknown")
    norad_id    = satellite.get("norad_id", "N/A")
    orbit_type  = orbital.get("orbit_type", "UNKNOWN")
    altitude    = orbital.get("altitude_km", "N/A")
    inclination = orbital.get("inclination", "N/A")
    eccentricity= orbital.get("eccentricity", "N/A")
    risk_score  = risk.get("risk_score", "N/A")
    risk_level  = risk.get("risk_level", "UNKNOWN")
    lifetime    = state.get("orbital_analysis", {}).get("orbital_lifetime_estimate", "Unknown")

    # Format retrieved regulation chunks
    reg_text = ""
    for i, reg in enumerate(regulations[:8], 1):
        reg_text += f"\n--- Regulation {i} | {reg.get('source', '')} — {reg.get('document', '')} (Similarity: {reg.get('score', 0):.3f}) ---\n"
        reg_text += reg.get("text", "")[:800] + "\n"

    return f"""
You are MOSIP's Compliance Agent — a satellite regulatory compliance expert.

SATELLITE PROFILE:
- Name: {sat_name} (NORAD ID: {norad_id})
- Orbit Type: {orbit_type}
- Altitude: {altitude} km
- Inclination: {inclination}°
- Eccentricity: {eccentricity}
- Risk Score: {risk_score}/100 ({risk_level})
- Estimated Orbital Lifetime: {lifetime}

RETRIEVED REGULATORY CONTEXT (from ESA, IADC, NASA guidelines):
{reg_text}

COMPLIANCE ASSESSMENT TASK:
Analyze this satellite against the retrieved regulations and provide a structured compliance assessment.

Your response MUST be valid JSON with exactly this structure:
{{
    "compliance_score": <0-100 integer>,
    "compliance_level": "<COMPLIANT|PARTIAL|NON_COMPLIANT|UNKNOWN>",
    "applicable_regulations": [
        "<brief regulation name and requirement>"
    ],
    "passed_requirements": [
        "<requirement that is met, with brief explanation>"
    ],
    "failed_requirements": [
        "<requirement that is violated, with brief explanation>"
    ],
    "critical_violations": [
        "<any violation that requires immediate attention>"
    ],
    "compliance_summary": "<2-3 sentence plain English summary of compliance status>",
    "regulatory_sources": ["<source1>", "<source2>"]
}}

Base your assessment strictly on the retrieved regulations above. For LEO satellites, key checks are:
- 25-year post-mission deorbit rule
- Casualty risk limit (< 1 in 10,000 for debris reentry)
- Passivation requirements (battery/propellant depletion)
- Collision avoidance maneuver capability
For GEO: graveyard orbit disposal requirement.
"""


def run_compliance_agent(state: MOSIPState) -> dict:
    """
    Compliance Agent node.
    Adds 'compliance_analysis' and appends to 'agent_timeline'.
    """
    try:
        llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model=GROQ_MODEL,
            temperature=0.1,
            max_tokens=1500,
        )

        prompt = _build_compliance_prompt(state)
        messages = [
            SystemMessage(content=(
                "You are a space regulatory compliance expert. "
                "Always respond with valid JSON only. No markdown, no explanation outside JSON."
            )),
            HumanMessage(content=prompt),
        ]

        response = llm.invoke(messages)
        raw_text = response.content.strip()

        # Clean up any markdown code fences
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        raw_text = raw_text.strip()

        import json
        analysis = json.loads(raw_text)

    except Exception as e:
        # Fallback: structured response without LLM
        orbit_type = state.get("orbital_data", {}).get("orbit_type", "UNKNOWN")
        lifetime   = state.get("orbital_analysis", {}).get("orbital_lifetime_estimate", "Unknown")
        analysis = {
            "compliance_score":       50,
            "compliance_level":       "UNKNOWN",
            "applicable_regulations": [
                "IADC 25-year post-mission disposal rule",
                "ESA casualty risk limit (<1E-4)",
            ],
            "passed_requirements":    [],
            "failed_requirements":    [
                f"Unable to assess fully — LLM error: {str(e)[:100]}"
            ],
            "critical_violations":    [],
            "compliance_summary":     (
                f"Compliance assessment incomplete due to LLM error. "
                f"Manual review required for {orbit_type} satellite with lifetime: {lifetime}."
            ),
            "regulatory_sources":     ["ESA", "IADC"],
            "llm_error":              str(e),
        }

    score = analysis.get("compliance_score", 50)
    level = analysis.get("compliance_level", "UNKNOWN")

    timeline_entry = {
        "agent":     "Compliance Agent",
        "status":    "complete",
        "timestamp": datetime.utcnow().isoformat(),
        "summary": (
            f"Compliance: {level} ({score}/100) | "
            f"Violations: {len(analysis.get('failed_requirements', []))} | "
            f"Sources: {', '.join(analysis.get('regulatory_sources', []))}"
        ),
    }

    return {
        "compliance_analysis": analysis,
        "agent_timeline": state.get("agent_timeline", []) + [timeline_entry],
    }
