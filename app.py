import streamlit as st
import json
import re

from agents.monitoring_agent import run_monitoring_agent
from agents.risk_agent import run_risk_agent
from agents.scenario_agent import run_scenario_agent
from agents.financial_agent import run_financial_agent

st.title("Supply Chain Disruption Manager")

# --- EXECUTIVE CONTROLS ---
st.sidebar.header("Decision Controls")

delay_cost_per_day = st.sidebar.slider(
    "Delay Cost per Day ($)",
    min_value=1000,
    max_value=50000,
    value=10000,
    step=1000
)

decision_strategy = st.sidebar.selectbox(
    "Decision Strategy",
    ["Minimize Cost Impact", "Minimize Delay", "Balanced"]
)

event = st.text_input("Enter disruption event:")


# --- EXPLANATION FUNCTION ---
def generate_explanation(best_option):
    return f"""
The system selected '{best_option.get('option_name')}' because it optimizes the chosen decision strategy.

This option results in:
- Total Impact: ${best_option.get('total_impact', 0):,}
- Delay Cost: ${best_option.get('delay_cost', 0):,}

It provides the best trade-off compared to alternatives.
"""


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

            # --- APPLY DELAY COST FROM SLIDER ---
            for opt in options:
                delay_days = opt.get("estimated_delay_days", 0)
                opt["delay_cost"] = delay_days * delay_cost_per_day
                opt["total_impact"] = opt.get("estimated_cost", 0) + opt["delay_cost"]

            # --- FINANCIAL VIEW ---
            st.subheader("Financial Comparison Table")
            st.table(options)

            # --- DECISION LOGIC BASED ON STRATEGY ---
            if decision_strategy == "Minimize Cost Impact":
                best_option = min(
                    options,
                    key=lambda x: x.get("total_impact", 999999999)
                )

            elif decision_strategy == "Minimize Delay":
                best_option = min(
                    options,
                    key=lambda x: x.get("estimated_delay_days", 999)
                )

            else:  # Balanced
                best_option = min(
                    options,
                    key=lambda x: (
                        x.get("total_impact", 999999999) * 0.7 +
                        x.get("estimated_delay_days", 999) * 0.3 * delay_cost_per_day
                    )
                )

            # --- DISPLAY DECISION ---
            st.subheader("Recommended Decision")

            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Option:** {best_option.get('option_name', 'N/A')}")
                st.write(f"**Total Impact:** ${best_option.get('total_impact', 0):,}")
                st.write(f"**Delay Cost:** ${best_option.get('delay_cost', 0):,}")
                st.write(f"**Delay:** {best_option.get('estimated_delay_days', 0)} days")

            with col2:
                confidence = "High" if best_option.get("total_impact", 0) < 50000 else "Medium"
                st.metric("Confidence Level", confidence)

            # --- EXPLANATION ---
            st.subheader("Decision Rationale")
            st.write(generate_explanation(best_option))

            # --- HUMAN OVERRIDE ---
            st.subheader("Manual Override")

            option_names = [opt.get("option_name") for opt in options]

            override = st.selectbox(
                "Select an alternative decision (optional):",
                ["No Override"] + option_names
            )

            if override != "No Override":
                selected = next(
                    (opt for opt in options if opt.get("option_name") == override),
                    None
                )

                if selected:
                    st.warning("Manual override applied")
                    st.write(f"**Selected Option:** {selected.get('option_name')}")
                    st.write(f"**Total Impact:** ${selected.get('total_impact', 0):,}")

        except Exception as e:
            st.error(f"Pipeline failed: {e}")
            st.write("Raw scenario output:", scenario_result)

    else:
        st.warning("Please enter an event.")