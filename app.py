import streamlit as st
from agents.monitoring_agent import run_monitoring_agent
from agents.risk_agent import run_risk_agent

st.title("Supply Chain Disruption Manager")

event = st.text_input("Enter disruption event:")

if st.button("Run Simulation"):
    if event:
        # Step 1: Monitoring Agent
        monitoring_result = run_monitoring_agent(event)

        st.subheader("Monitoring Agent Output")
        st.code(monitoring_result, language="json")

        # Step 2: Risk Agent
        risk_result = run_risk_agent(monitoring_result)

        st.subheader("Risk Agent Output")
        st.code(risk_result, language="json")

    else:
        st.warning("Please enter an event.")
