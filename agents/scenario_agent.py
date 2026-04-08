from anthropic import Anthropic
import os

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def run_scenario_agent(monitoring_input, risk_input):
    prompt = f"""
Generate 3 supply chain response options.

Each must represent:
1. Lowest cost
2. Fastest resolution
3. Balanced tradeoff

Return ONLY JSON list:
[
  {{
    "option_name": "...",
    "estimated_cost": number,
    "estimated_delay_days": number
  }}
]
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text