import streamlit as st
import json
import re
import pandas as pd

from agents.monitoring_agent import run_monitoring_agent
from agents.risk_agent import run_risk_agent
from agents.scenario_agent import run_scenario_agent

st.title("Supply Chain Disruption Manager")

# --- SIDEBAR CONTROLS ---
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

show_raw = st.sidebar.checkbox("Show Raw Agent Output (Debug)", value=False)

event = st.text_input(
    "Enter disruption event:",
    value="Typhoon near Shanghai port causing shipment delays"
)

# --- RUN SIMULATION ---
if st.button("Run Simulation"):
    if event:
        try:
            st.session_state["run_data"] = {}

            # Monitoring
            monitoring_result = run_monitoring_agent(event)
            monitoring_clean = json.loads(monitoring_result)

            # Risk
            risk_result = run_risk_agent(monitoring_result)
            risk_clean = json.loads(risk_result)

            # Scenario
            scenario_result = run_scenario_agent(monitoring_result, risk_result)
            cleaned = re.sub(r"```json|```", "", scenario_result).strip()
            options = json.loads(cleaned)

            if not isinstance(options, list):
                raise ValueError("Scenario output is not a list")

            # Store everything
            st.session_state["run_data"] = {
                "monitoring": monitoring_clean,
                "risk": risk_clean,
                "options": options,
                "raw_monitoring": monitoring_result,
                "raw_risk": risk_result,
                "raw_scenario": scenario_result
            }

        except Exception as e:
            st.error(f"Pipeline failed: {e}")

    else:
        st.warning("Please enter an event.")

# --- DISPLAY RESULTS ---
if "run_data" in st.session_state:

    data = st.session_state["run_data"]

    monitoring = data["monitoring"]
    risk = data["risk"]
    options = data["options"]

    # --- CLEAN MONITORING DISPLAY ---
    st.subheader("Disruption Overview")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Disruption Type", monitoring.get("disruption_type", "N/A"))

    with col2:
        st.metric("Severity", monitoring.get("severity", "N/A"))

    with col3:
        st.metric("Confidence", risk.get("confidence", "N/A"))

    st.write(f"**Impact Summary:** {monitoring.get('likely_impact', 'N/A')}")

    # --- CLEAN RISK DISPLAY ---
    st.subheader("Risk Assessment")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Risk Score", risk.get("risk_score", "N/A"))

    with col2:
        st.metric("Estimated Delay", f"{risk.get('estimated_delay_days', 0)} days")

    # --- OPTIONAL RAW OUTPUT ---
    if show_raw:
        st.subheader("Raw Agent Outputs")
        st.code(data["raw_monitoring"], language="json")
        st.code(data["raw_risk"], language="json")
        st.code(data["raw_scenario"], language="json")

    # --- APPLY FINANCIAL CALCULATIONS ---
    for opt in options:
        delay_days = opt.get("estimated_delay_days", 0)
        opt["delay_cost"] = delay_days * delay_cost_per_day
        opt["total_impact"] = opt.get("estimated_cost", 0) + opt["delay_cost"]

    # --- TABLE DISPLAY ---
    df = pd.DataFrame(options)

    display_df = df.copy()
    display_df["estimated_cost"] = display_df["estimated_cost"].map("${:,.0f}".format)
    display_df["delay_cost"] = display_df["delay_cost"].map("${:,.0f}".format)
    display_df["total_impact"] = display_df["total_impact"].map("${:,.0f}".format)

    st.subheader("Response Options Comparison")
    st.dataframe(display_df, use_container_width=True)

    # --- DECISION LOGIC ---
    if decision_strategy == "Minimize Cost Impact":
        best_option = min(options, key=lambda x: x["total_impact"])

    elif decision_strategy == "Minimize Delay":
        best_option = min(options, key=lambda x: x["estimated_delay_days"])

    else:
        best_option = min(
            options,
            key=lambda x: (
                x["total_impact"] * 0.7 +
                x["estimated_delay_days"] * 0.3 * delay_cost_per_day
            )
        )

    # --- DECISION DISPLAY ---
    st.subheader("Recommended Decision")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Option:** {best_option['option_name']}")
        st.write(f"**Total Impact:** ${best_option['total_impact']:,}")
        st.write(f"**Delay:** {best_option['estimated_delay_days']} days")

    with col2:
        confidence = "High" if best_option["total_impact"] < 50000 else "Medium"
        st.metric("Confidence Level", confidence)

    # --- EXPLANATION ---
    st.subheader("Decision Rationale")
    st.write(
        f"The system selected '{best_option['option_name']}' based on the '{decision_strategy}' strategy, "
        f"optimizing financial and operational trade-offs."
    )

    # --- MANUAL OVERRIDE ---
    st.subheader("Manual Override")

    option_names = [opt["option_name"] for opt in options]

    override = st.selectbox(
        "Select an alternative decision:",
        ["No Override"] + option_names
    )

    if override != "No Override":
        selected = next(opt for opt in options if opt["option_name"] == override)

        st.warning("Manual override applied")
        st.write(f"**Selected Option:** {selected['option_name']}")
        st.write(f"**Total Impact:** ${selected['total_impact']:,}")