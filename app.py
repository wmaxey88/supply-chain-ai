import streamlit as st
from agents.monitoring_agent import run_monitoring_agent

st.title("Supply Chain Disruption Manager")

event = st.text_input("Enter disruption event:")

if st.button("Run Simulation"):
    if event:
        result = run_monitoring_agent(event)
        
        st.subheader("Monitoring Agent Output")
        st.code(result, language="json")
    else:
        st.warning("Please enter an event.")
