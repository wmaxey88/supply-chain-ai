def run_risk_agent(monitoring_input):
    prompt = f"""
Assess risk.

Return JSON:
{{
  "risk_score": 0-100,
  "estimated_delay_days": number,
  "confidence": "low|medium|high"
}}
Ensure alignment:
- high severity → high risk
"""

    return call_model(prompt)