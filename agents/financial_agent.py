import os
import anthropic

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

def run_financial_agent(options):
    prompt = f"""
You are a supply chain financial analyst.

Given the following response options, calculate business impact.

Return STRICT JSON as a list of objects with:
- option_name
- total_estimated_cost (integer)
- delay_cost (integer)
- total_impact (integer)

Assume:
- Delay cost = $10,000 per day

Options:
{options}
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