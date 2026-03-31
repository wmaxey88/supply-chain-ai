# Autonomous Supply Chain Disruption Manager

A multi-agent AI system that detects, analyzes, and recommends responses
to supply chain disruptions in real time.

------------------------------------------------------------------------

## Overview

This project demonstrates an agentic AI architecture where multiple
specialized agents collaborate to:

-   Detect disruption events
-   Assess operational risk
-   Generate response strategies
-   Quantify financial impact
-   Recommend optimal decisions

The system includes a human-in-the-loop override, enabling executive
control over AI-driven recommendations.

------------------------------------------------------------------------

## Key Features

-   Multi-agent orchestration (Monitoring, Risk, Scenario)
-   Structured inter-agent communication (JSON-based)
-   Financial impact modeling
-   Strategy-based decision logic (Cost, Delay, Balanced)
-   Interactive UI with Streamlit
-   Human override and explainability layer

------------------------------------------------------------------------

## Architecture

User Input\
↓\
Monitoring Agent\
↓\
Risk Agent\
↓\
Scenario Agent\
↓\
Financial Modeling Layer\
↓\
Decision Engine\
↓\
Human Override

------------------------------------------------------------------------

## Tech Stack

-   Python\
-   Streamlit (UI & hosting)\
-   Anthropic API (Claude models)\
-   Pandas (data handling)

------------------------------------------------------------------------

## How It Works

1.  User inputs a disruption event\
2.  Monitoring agent classifies the event\
3.  Risk agent estimates severity and delay\
4.  Scenario agent generates response options\
5.  Financial model calculates cost impact\
6.  Decision engine selects optimal strategy\
7.  User can override the recommendation

------------------------------------------------------------------------

## Example Use Case

Input:\
Typhoon near Shanghai port causing shipment delays

The system evaluates: - Waiting vs rerouting vs air freight\
- Cost vs delay trade-offs\
- Financial impact of each option

------------------------------------------------------------------------

## Setup (Local Development)

pip install -r requirements.txt\
streamlit run app.py

------------------------------------------------------------------------

## Deployment

This app is deployed using Streamlit Community Cloud and can be accessed
via a public URL.

------------------------------------------------------------------------

## Security

-   API keys are stored securely using environment variables\
-   Streamlit Secrets are used for cloud deployment\
-   No credentials are exposed to users

------------------------------------------------------------------------

## License

This project is licensed under the MIT License.
