import os
import anthropic

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

def run_scenario_agent(monitoring_output, risk_output):
    prompt = f"""
You are a supply chain scenario planning agent.

Based on the disruption and risk data below, generate EXACTLY 3 response options.

Return STRICT JSON as a list of objects with:
- option_name
- description
- estimated_cost (integer USD)
- estimated_delay_days (integer)

Disruption:
{monitoring_output}

Risk:
{risk_output}
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.content[0].text