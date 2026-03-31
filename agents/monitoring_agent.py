import os
import anthropic

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

def run_monitoring_agent(event_text):
    prompt = f"""
    You are a supply chain monitoring agent.

    Analyze the following event and return:
    - disruption_type
    - severity (low, medium, high)
    - likely_impact (short description)

    Event:
    {event_text}

    Return JSON only.
    """

    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=300,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.content[0].text