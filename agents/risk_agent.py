import os
import anthropic

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

def run_risk_agent(monitoring_output):
    prompt = f"""
You are a supply chain risk assessment agent.

Based on the following disruption data, return STRICT JSON with EXACTLY:

- risk_score (0-100 integer)
- estimated_delay_days (integer)
- confidence (low, medium, high)

Disruption Data:
{monitoring_output}
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.content[0].text