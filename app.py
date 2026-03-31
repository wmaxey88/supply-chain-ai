import streamlit as st
import json
import re

from agents.monitoring_agent import run_monitoring_agent
from agents.risk_agent import run_risk_agent
from agents.scenario_agent import run_scenario_agent
from agents.financial_agent import run_financial_agent

st.title("Supply Chain Disruption Manager")

event = st.text_input("Enter disruption event:")

if st.button("Run Simulation"):
    if event:
        try:
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

            # --- CLEAN + PARSE SCENARIOS ---
            cleaned = re.sub(r"```json|```", "", scenario_result).strip()
            options = json.loads(cleaned)

            if not isinstance(options, list):
                raise ValueError("Scenario output is not a list")

            st.subheader("Scenario Options Table")
            st.table(options)

            # Step 5: Financial Impact
            financial_result = run_financial_agent(options)

            st.subheader("Financial Impact Analysis")
            st.code(financial_result, language="json")

            # --- CLEAN + PARSE FINANCIAL OUTPUT ---
            cleaned_fin = re.sub(r"```json|```", "", financial_result).strip()
            financial_options = json.loads(cleaned_fin)

            if not isinstance(financial_options, list):
                raise ValueError("Financial output is not a list")

            st.subheader("Financial Comparison Table")
            st.table(financial_options)

            # --- FINAL DECISION (FINANCIAL OPTIMIZATION) ---
            best_option = min(
                financial_options,
                key=lambda x: x.get("total_impact", 999999999)
            )

            st.subheader("Recommended Decision (Cost Optimized)")
            st.write(f"**Option:** {best_option.get('option_name', 'N/A')}")
            st.write(f"**Total Impact:** ${best_option.get('total_impact', 0):,}")
            st.write(f"**Delay Cost:** ${best_option.get('delay_cost', 0):,}")

        except Exception as e:
            st.error(f"Pipeline failed: {e}")
            st.write("Scenario Raw Output:", scenario_result)

    else:
        st.warning("Please enter an event.")