import streamlit as st
import json
import re

from agents.monitoring_agent import run_monitoring_agent
from agents.risk_agent import run_risk_agent
from agents.scenario_agent import run_scenario_agent

st.title("Supply Chain Disruption Manager")

event = st.text_input("Enter disruption event:")

if st.button("Run Simulation"):
    if event:
        # Step 1: Monitoring
        monitoring_result = run_monitoring_agent(event)
        st.subheader("Monitoring Agent Output")
        st.code(monitoring_result, language="json")

        # Step 2: Risk
        risk_result = run_risk_agent(monitoring_result)
        st.subheader("Risk Agent Output")
        st.code(risk_result, language="json")

        # Step 3: Scenario Options
        scenario_result = run_scenario_agent(monitoring_result, risk_result)
        st.subheader("Scenario Options")
        st.code(scenario_result, language="json")
        st.caption("Raw model output (pre-parsing)")

        # Step 4: Decision Logic
        try:
            cleaned = scenario_result.strip()

            # Remove markdown if present
            cleaned = re.sub(r"```json|```", "", cleaned).strip()

            options = json.loads(cleaned)

            # Ensure it's a list
            if not isinstance(options, list):
                raise ValueError("Scenario output is not a list")

            st.subheader("Scenario Options Table")
            st.table(options)

            best_option = min(
                options,
                key=lambda x: x.get("estimated_cost", 999999) +
                              (x.get("estimated_delay_days", 999) * 10000)
            )

            st.subheader("Recommended Decision")
            st.write(f"**Option:** {best_option.get('option_name', 'N/A')}")
            st.write(f"**Description:** {best_option.get('description', 'N/A')}")
            st.write(f"**Cost:** ${best_option.get('estimated_cost', 0):,}")
            st.write(f"**Delay:** {best_option.get('estimated_delay_days', 0)} days")

        except Exception as e:
            st.error(f"Decision logic failed: {e}")
            st.write("Raw output:", scenario_result)

    else:
        st.warning("Please enter an event.")
