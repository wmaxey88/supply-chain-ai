def run_monitoring_agent(event):
    prompt = f"""
Analyze disruption.

Return JSON:
{{
  "disruption_type": "...",
  "severity": "low|medium|high",
  "likely_impact": "short description"
}}
"""

    return call_model(prompt)