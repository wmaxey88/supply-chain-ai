import streamlit as st

st.title("Supply Chain Disruption Manager")

event = st.text_input("Enter disruption event:")

if st.button("Run Simulation"):
    st.write(f"Event received: {event}")
