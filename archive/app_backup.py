import streamlit as st
import json
import re
import pandas as pd

from agents.monitoring_agent import run_monitoring_agent
from agents.risk_agent import run_risk_agent
from agents.scenario_agent import run_scenario_agent

st.title("Supply Chain Disruption Manager")

# --- SIDEBAR ---
st.sidebar.header("Decision Controls")

delay_cost_per_day = st.sidebar.slider(
    "Delay Cost per Day ($)",
    1000, 50000, 10000, 1000
)

decision_strategy = st.sidebar.selectbox(
    "Decision Strategy",
    ["Minimize Cost Impact", "Minimize Delay", "Balanced"]
)

show_raw = st.sidebar.checkbox("Show Raw Agent Output", value=False)

event = st.text_input(
    "Enter disruption event:",
    value="Typhoon near Shanghai port causing shipment delays"
)

# --- HELPER: CLEAN + PARSE JSON ---
def safe_parse(text):
    try:
        cleaned = re.sub(r"```json|```", "", text).strip()
        return json.loads(cleaned)
    except:
        return None

# --- RUN PIPELINE ---
if st.button("Run Simulation"):
    if event:
        try:
            monitoring_raw = run_monitoring_agent(event)
            monitoring = safe_parse(monitoring_raw)

            if not monitoring:
                raise ValueError("Monitoring agent returned invalid JSON")

            risk_raw = run_risk_agent(monitoring_raw)
            risk = safe_parse(risk_raw)

            if not risk:
                raise ValueError("Risk agent returned invalid JSON")

            scenario_raw = run_scenario_agent(monitoring_raw, risk_raw)
            options = safe_parse(scenario_raw)

            if not isinstance(options, list):
                raise ValueError("Scenario agent output invalid")

            # Save only if EVERYTHING worked
            st.session_state["run_data"] = {
                "monitoring": monitoring,
                "risk": risk,
                "options": options,
                "raw": {
                    "monitoring": monitoring_raw,
                    "risk": risk_raw,
                    "scenario": scenario_raw
                }
            }

        except Exception as e:
            st.error(f"Pipeline failed: {e}")

    else:
        st.warning("Please enter an event.")

# --- DISPLAY ONLY IF VALID ---
if "run_data" in st.session_state and st.session_state["run_data"]:

    data = st.session_state["run_data"]

    monitoring = data.get("monitoring", {})
    risk = data.get("risk", {})
    options = data.get("options", [])

    # --- DISRUPTION OVERVIEW ---
    st.subheader("Disruption Overview")

    col1, col2, col3 = st.columns(3)

    col1.metric("Type", monitoring.get("disruption_type", "N/A"))
    col2.metric("Severity", monitoring.get("severity", "N/A"))
    col3.metric("Confidence", risk.get("confidence", "N/A"))

    st.write(f"**Impact:** {monitoring.get('likely_impact', 'N/A')}")

    # --- RISK ---
    st.subheader("Risk Assessment")

    col1, col2 = st.columns(2)

    col1.metric("Risk Score", risk.get("risk_score", "N/A"))
    col2.metric("Delay", f"{risk.get('estimated_delay_days', 0)} days")

    # --- RAW DEBUG ---
    if show_raw:
        st.subheader("Raw Outputs")
        st.code(data["raw"]["monitoring"])
        st.code(data["raw"]["risk"])
        st.code(data["raw"]["scenario"])

    # --- FINANCIAL CALCS ---
    for opt in options:
        delay = opt.get("estimated_delay_days", 0)
        opt["delay_cost"] = delay * delay_cost_per_day
        opt["total_impact"] = opt.get("estimated_cost", 0) + opt["delay_cost"]

    # --- TABLE ---
    df = pd.DataFrame(options)

    if not df.empty:
        display_df = df.copy()

        display_df["estimated_cost"] = display_df["estimated_cost"].map("${:,.0f}".format)
        display_df["delay_cost"] = display_df["delay_cost"].map("${:,.0f}".format)
        display_df["total_impact"] = display_df["total_impact"].map("${:,.0f}".format)

        st.subheader("Response Options")
        st.dataframe(display_df, use_container_width=True)

    # --- DECISION ---
    if options:
        if decision_strategy == "Minimize Cost Impact":
            best = min(options, key=lambda x: x["total_impact"])

        elif decision_strategy == "Minimize Delay":
            best = min(options, key=lambda x: x["estimated_delay_days"])

        else:
            best = min(
                options,
                key=lambda x: (
                    x["total_impact"] * 0.7 +
                    x["estimated_delay_days"] * 0.3 * delay_cost_per_day
                )
            )

        st.subheader("Recommended Decision")

        col1, col2 = st.columns(2)

        col1.write(f"**Option:** {best['option_name']}")
        col1.write(f"**Impact:** ${best['total_impact']:,}")
        col1.write(f"**Delay:** {best['estimated_delay_days']} days")

        confidence = "High" if best["total_impact"] < 50000 else "Medium"
        col2.metric("Confidence", confidence)

        # --- EXPLANATION ---
        st.subheader("Rationale")
        st.write(
            f"Selected '{best['option_name']}' based on '{decision_strategy}' strategy."
        )

        # --- OVERRIDE ---
        st.subheader("Manual Override")

        names = [o["option_name"] for o in options]

        override = st.selectbox("Override decision:", ["No Override"] + names)

        if override != "No Override":
            selected = next(o for o in options if o["option_name"] == override)

            st.warning("Override Applied")
            st.write(f"**Option:** {selected['option_name']}")
            st.write(f"**Impact:** ${selected['total_impact']:,}")