import streamlit as st
import json

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

        # Step 4: Decision Logic
        try:
            options = json.loads(scenario_result)

            # Simple decision rule:
            # minimize (cost + delay * 10000)
            best_option = min(
                options,
                key=lambda x: x["estimated_cost"] + (x["estimated_delay_days"] * 10000)
            )

            st.subheader("Recommended Decision")
            st.success(best_option)

        except Exception as e:
            st.error(f"Decision logic failed: {e}")

    else:
        st.warning("Please enter an event.")
