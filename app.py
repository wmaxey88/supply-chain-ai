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

event = st.text_input("Enter disruption event:")

# --- RUN SIMULATION BUTTON ---
if st.button("Run Simulation"):
    if event:
        try:
            st.session_state["run_data"] = {}

            # Step 1: Monitoring
            monitoring_result = run_monitoring_agent(event)
            st.session_state["run_data"]["monitoring"] = monitoring_result

            # Step 2: Risk
            risk_result = run_risk_agent(monitoring_result)
            st.session_state["run_data"]["risk"] = risk_result

            # Step 3: Scenario
            scenario_result = run_scenario_agent(monitoring_result, risk_result)
            st.session_state["run_data"]["scenario_raw"] = scenario_result

            cleaned = re.sub(r"```json|```", "", scenario_result).strip()
            options = json.loads(cleaned)

            if not isinstance(options, list):
                raise ValueError("Scenario output is not a list")

            st.session_state["run_data"]["options"] = options

        except Exception as e:
            st.error(f"Pipeline failed: {e}")

    else:
        st.warning("Please enter an event.")

# --- DISPLAY RESULTS (PERSISTENT) ---
if "run_data" in st.session_state:

    data = st.session_state["run_data"]

    monitoring_result = data["monitoring"]
    risk_result = data["risk"]
    options = data["options"]

    # --- SHOW RAW AGENT OUTPUTS ---
    st.subheader("Monitoring Agent Output")
    st.code(monitoring_result, language="json")

    st.subheader("Risk Agent Output")
    st.code(risk_result, language="json")

    # --- APPLY FINANCIAL CALCULATIONS ---
    for opt in options:
        delay_days = opt.get("estimated_delay_days", 0)
        opt["delay_cost"] = delay_days * delay_cost_per_day
        opt["total_impact"] = opt.get("estimated_cost", 0) + opt["delay_cost"]

    # --- CLEAN TABLE DISPLAY ---
    df = pd.DataFrame(options)

    display_df = df.copy()
    display_df["estimated_cost"] = display_df["estimated_cost"].map("${:,.0f}".format)
    display_df["delay_cost"] = display_df["delay_cost"].map("${:,.0f}".format)
    display_df["total_impact"] = display_df["total_impact"].map("${:,.0f}".format)

    st.subheader("Scenario + Financial Comparison")
    st.dataframe(display_df, use_container_width=True)

    # --- DECISION LOGIC ---
    if decision_strategy == "Minimize Cost Impact":
        best_option = min(options, key=lambda x: x["total_impact"])

    elif decision_strategy == "Minimize Delay":
        best_option = min(options, key=lambda x: x["estimated_delay_days"])

    else:  # Balanced
        best_option = min(
            options,
            key=lambda x: (
                x["total_impact"] * 0.7 +
                x["estimated_delay_days"] * 0.3 * delay_cost_per_day
            )
        )

    # --- DISPLAY DECISION ---
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
        f"The system selected '{best_option['option_name']}' because it best satisfies the "
        f"'{decision_strategy}' strategy while minimizing financial and operational impact."
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