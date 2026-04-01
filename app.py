import streamlit as st
import json
import re
import pandas as pd

from agents.monitoring_agent import run_monitoring_agent
from agents.risk_agent import run_risk_agent
from agents.scenario_agent import run_scenario_agent

st.set_page_config(page_title="Supply Chain Disruption Manager", layout="wide")

# --- STYLING ---
st.markdown("""
<style>
.block-container { padding-top: 2rem; padding-bottom: 2rem; }
.section-divider { border-top: 1px solid #374151; margin: 20px 0; }
</style>
""", unsafe_allow_html=True)

st.title("Supply Chain Disruption Manager")

# --- SIDEBAR ---
st.sidebar.header("Simulation Parameters")

delay_cost_per_day = st.sidebar.slider(
    "Delay Cost per Day ($)", 1000, 50000, 10000, 1000
)

decision_strategy = st.sidebar.selectbox(
    "Strategy",
    ["Minimize Cost Impact", "Minimize Delay", "Balanced"]
)

show_raw = st.sidebar.checkbox("Show Detailed Agent Output", value=False)

event = st.text_input(
    "Enter disruption event:",
    value="Typhoon near Shanghai port causing shipment delays"
)

# --- HELPERS ---
def safe_parse(text):
    try:
        cleaned = re.sub(r"```json|```", "", text).strip()
        return json.loads(cleaned)
    except:
        return None

def validate_options(options):
    if not isinstance(options, list):
        return False
    for opt in options:
        if not all(k in opt for k in ["option_name", "estimated_cost", "estimated_delay_days"]):
            return False
    return True

def validate_consistency(monitoring, risk):
    severity = monitoring.get("severity", "").lower()
    risk_score = risk.get("risk_score", 0)
    return not (severity == "low" and risk_score > 70)

def correct_scenario(monitoring_raw, risk_raw, bad_output):
    prompt = f"""
Fix this output into valid JSON list format.

Original:
{bad_output}

Requirements:
- list of objects
- fields: option_name, estimated_cost, estimated_delay_days
- return ONLY JSON
"""
    return run_scenario_agent(monitoring_raw, risk_raw + prompt)

# --- RUN ---
if st.button("Run Simulation"):
    if event:
        try:
            retried = False

            enriched_event = f"""
Event: {event}
Context: Supply chain disruption. Consider logistics delays, cost impact, and downstream effects.
"""

            with st.spinner("Monitoring disruption..."):
                monitoring_raw = run_monitoring_agent(enriched_event)
                monitoring = safe_parse(monitoring_raw)

            with st.spinner("Assessing risk..."):
                risk_raw = run_risk_agent(monitoring_raw)
                risk = safe_parse(risk_raw)

            if not validate_consistency(monitoring, risk):
                retried = True
                risk_raw = run_risk_agent(monitoring_raw + "\nEnsure risk aligns with severity.")
                risk = safe_parse(risk_raw)

            with st.spinner("Generating scenarios..."):
                scenario_raw = run_scenario_agent(monitoring_raw, risk_raw)
                options = safe_parse(scenario_raw)

            if not validate_options(options):
                retried = True
                scenario_raw = correct_scenario(monitoring_raw, risk_raw, scenario_raw)
                options = safe_parse(scenario_raw)

            if not validate_options(options):
                options = [{
                    "option_name": "Manual Review Required",
                    "estimated_cost": 0,
                    "estimated_delay_days": risk.get("estimated_delay_days", 0)
                }]

            st.session_state["run_data"] = {
                "monitoring": monitoring,
                "risk": risk,
                "options": options,
                "retried": retried,
                "raw": {
                    "monitoring": monitoring_raw,
                    "risk": risk_raw,
                    "scenario": scenario_raw
                }
            }

        except Exception as e:
            st.error(f"Pipeline failed: {e}")

# --- DISPLAY ---
if "run_data" in st.session_state:
    data = st.session_state["run_data"]

    monitoring = data["monitoring"]
    risk = data["risk"]
    options = data["options"]

    delay_days = risk.get("estimated_delay_days", 0)

    # financials
    for opt in options:
        opt["delay_cost"] = opt["estimated_delay_days"] * delay_cost_per_day
        opt["total_impact"] = opt["estimated_cost"] + opt["delay_cost"]

    best = min(options, key=lambda x: x["total_impact"])

    # --- EXECUTIVE SUMMARY ---
    st.markdown("### Executive Summary")
    st.write(f"""
- **Situation:** {monitoring.get("disruption_type")} ({monitoring.get("severity")})
- **Impact:** ~{delay_days} days delay
- **Recommendation:** {best['option_name']}
- **Total Impact:** ${best['total_impact']:,}
""")

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

    # --- DECISION OPTIONS ---
    st.markdown("### Decision Options")
    for opt in options:
        st.write(f"""
**{opt['option_name']}**
- Cost: ${opt['estimated_cost']:,}
- Delay: {opt['estimated_delay_days']} days
- Total Impact: ${opt['total_impact']:,}
""")

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

    # --- MANUAL OVERRIDE (FIXED) ---
    st.markdown("### Manual Override")

    option_names = [o["option_name"] for o in options]
    override = st.selectbox("Override decision:", ["No Override"] + option_names)

    if override != "No Override":
        selected = next(o for o in options if o["option_name"] == override)

        st.warning("Override Applied")
        st.write(f"""
**{selected['option_name']}**
- Cost: ${selected['estimated_cost']:,}
- Delay: {selected['estimated_delay_days']} days
- Total Impact: ${selected['total_impact']:,}
""")

    if data["retried"]:
        st.caption("Auto-corrected by validation layer")

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

    # --- RAW OUTPUTS ---
    if show_raw:
        st.markdown("### Detailed Agent Output")

        st.markdown("**Monitoring Agent Output**")
        parsed = safe_parse(data["raw"]["monitoring"])
        st.json(parsed) if parsed else st.code(data["raw"]["monitoring"])

        st.markdown("**Risk Agent Output**")
        parsed = safe_parse(data["raw"]["risk"])
        st.json(parsed) if parsed else st.code(data["raw"]["risk"])

        st.markdown("**Scenario Agent Output**")
        parsed = safe_parse(data["raw"]["scenario"])
        if isinstance(parsed, list):
            for i, item in enumerate(parsed):
                st.markdown(f"Option {i+1}")
                st.json(item)
        else:
            st.json(parsed) if parsed else st.code(data["raw"]["scenario"])