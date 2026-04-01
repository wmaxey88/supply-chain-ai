import streamlit as st
import json
import re
import pandas as pd

from agents.monitoring_agent import run_monitoring_agent
from agents.risk_agent import run_risk_agent
from agents.scenario_agent import run_scenario_agent

st.set_page_config(page_title="Supply Chain Disruption Manager", layout="wide")

# --- GLOBAL STYLING ---
st.markdown("""
<style>
.block-container { padding-top: 2rem; padding-bottom: 2rem; }
h2 { margin-top: 1.5rem; }
[data-testid="stMetric"] {
    background-color: #111827;
    padding: 15px;
    border-radius: 10px;
}
div[data-testid="stMarkdownContainer"] p { margin-bottom: 0.5rem; }
.section-divider { border-top: 1px solid #374151; margin: 20px 0; }
</style>
""", unsafe_allow_html=True)

st.title("Supply Chain Disruption Manager")

# --- SIDEBAR ---
st.sidebar.header("Simulation Parameters")

st.sidebar.subheader("Cost Assumptions")
delay_cost_per_day = st.sidebar.slider(
    "Delay Cost per Day ($)",
    1000, 50000, 10000, 1000
)

st.sidebar.subheader("Decision Strategy")
decision_strategy = st.sidebar.selectbox(
    "Strategy",
    ["Minimize Cost Impact", "Minimize Delay", "Balanced"]
)

show_raw = st.sidebar.checkbox("Show Detailed Agent Output", value=False)

# --- INPUT ---
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

# --- VALIDATION ---
def validate_options(options):
    if not isinstance(options, list):
        return False

    required_fields = ["option_name", "estimated_cost", "estimated_delay_days"]

    for opt in options:
        for field in required_fields:
            if field not in opt:
                return False

    return True

# --- SELF CORRECTION ---
def correct_scenario_output(monitoring_raw, risk_raw, bad_output):
    correction_prompt = f"""
The previous output was invalid or malformed.

Original output:
{bad_output}

Fix the output so that:
- It is valid JSON
- It is a LIST of objects
- Each object includes:
  - option_name
  - estimated_cost
  - estimated_delay_days

Return ONLY valid JSON. No explanation.
"""

    return run_scenario_agent(monitoring_raw, risk_raw + correction_prompt)

# --- RUN PIPELINE ---
if st.button("Run Simulation"):
    if event:
        try:
            retried = False

            with st.spinner("Monitoring disruption signals..."):
                monitoring_raw = run_monitoring_agent(event)
                monitoring = safe_parse(monitoring_raw)

                if not monitoring:
                    raise ValueError("Monitoring agent returned invalid JSON")

            with st.spinner("Assessing risk and impact..."):
                risk_raw = run_risk_agent(monitoring_raw)
                risk = safe_parse(risk_raw)

                if not risk:
                    raise ValueError("Risk agent returned invalid JSON")

            with st.spinner("Generating response scenarios..."):
                scenario_raw = run_scenario_agent(monitoring_raw, risk_raw)
                options = safe_parse(scenario_raw)

            # --- VALIDATE + AUTO-CORRECT ---
            if not validate_options(options):
                retried = True

                with st.spinner("Correcting scenario output..."):
                    scenario_raw = correct_scenario_output(monitoring_raw, risk_raw, scenario_raw)
                    options = safe_parse(scenario_raw)

            if not validate_options(options):
                raise ValueError("Scenario agent failed validation after retry")

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

    else:
        st.warning("Please enter an event.")

# --- DISPLAY ---
if "run_data" in st.session_state and st.session_state["run_data"]:

    data = st.session_state["run_data"]

    monitoring = data.get("monitoring", {})
    risk = data.get("risk", {})
    options = data.get("options", [])

    disruption_type = monitoring.get("disruption_type", "N/A")
    severity = monitoring.get("severity", "N/A")
    confidence = risk.get("confidence", "N/A")
    delay_days = risk.get("estimated_delay_days", 0)
    risk_score = risk.get("risk_score", 0)

    # --- FINANCIAL CALCS ---
    for opt in options:
        delay = opt.get("estimated_delay_days", 0)
        opt["delay_cost"] = delay * delay_cost_per_day
        opt["total_impact"] = opt.get("estimated_cost", 0) + opt["delay_cost"]

    # --- DECISION ---
    if options:
        if decision_strategy == "Minimize Cost Impact":
            best = min(options, key=lambda x: x["total_impact"])
        elif decision_strategy == "Minimize Delay":
            best = min(options, key=lambda x: x["estimated_delay_days"])
        else:
            best = min(options, key=lambda x: (x["total_impact"] * 0.7 + x["estimated_delay_days"] * 0.3 * delay_cost_per_day))
    else:
        best = None

    # --- EXECUTIVE SUMMARY ---
    if best:
        st.markdown("### Executive Summary")
        st.markdown(f"""
**Situation:** {disruption_type.title()} disruption with **{severity.upper()} severity**

**Expected Impact:** ~{delay_days} day delay

**Recommended Action:** {best.get('option_name', 'N/A')}

**Estimated Impact:** ${best.get('total_impact', 0):,}

**Confidence Level:** {confidence.title()}
""")
        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

    # --- METRICS ---
    st.markdown("### Key Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Risk Score", risk_score, "High" if risk_score > 70 else "Moderate")
    col2.metric("Estimated Delay", f"{delay_days} days")
    col3.metric("Confidence", confidence.title())

    st.markdown(f"**Time to Impact:** Immediate (within {delay_days} days)")
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

    # --- RECOMMENDED ---
    if best:
        st.markdown("### Recommended Action")
        st.markdown(f"""
**{best.get('option_name', 'N/A')}**

- Estimated Cost: ${best.get('estimated_cost', 0):,}
- Delay: {best.get('estimated_delay_days', 0)} days
- Total Impact: ${best.get('total_impact', 0):,}
""")
        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

    # --- OPTIONS ---
    st.markdown("### Decision Options")
    for i, opt in enumerate(options):
        st.markdown(f"""
**Option {i+1}: {opt.get('option_name', 'N/A')}**

- Cost: ${opt.get('estimated_cost', 0):,}
- Delay: {opt.get('estimated_delay_days', 0)} days
- Total Impact: ${opt.get('total_impact', 0):,}
""")
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

    # --- BUSINESS IMPACT ---
    st.markdown("### Business Impact")
    st.markdown(f"""
- **Operational:** {monitoring.get('likely_impact', 'N/A')}
- **Financial Exposure:** ~${delay_cost_per_day:,} per day of delay
- **Customer Risk:** Potential downstream fulfillment disruption
""")

    # --- TABLE ---
    df = pd.DataFrame(options)
    if not df.empty:
        display_df = df.copy()
        display_df["estimated_cost"] = display_df["estimated_cost"].map("${:,.0f}".format)
        display_df["delay_cost"] = display_df["delay_cost"].map("${:,.0f}".format)
        display_df["total_impact"] = display_df["total_impact"].map("${:,.0f}".format)

        with st.expander("View Detailed Option Comparison"):
            st.dataframe(display_df, use_container_width=True)

    # --- RETRY INDICATOR ---
    if data.get("retried"):
        st.caption("Output auto-corrected by validation layer")

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
