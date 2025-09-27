import streamlit as st
from app1.ui import run_app1
from app2.ui import run_app2
import os
os.system("playwright install")
def main():
    st.sidebar.title("Navigation")
    choice = st.sidebar.radio("Go to:", ["Step 1: Scrape Instruments", "Step 2: HCAD Search"])

    # Use session_state to pass the DataFrame from App1 to App2
    if "app1_results" not in st.session_state:
        st.session_state.app1_results = None

    if choice == "Step 1: Scrape Instruments":
        df = run_app1()
        if df is not None:
            st.session_state.app1_results = df

    elif choice == "Step 2: HCAD Search":
        run_app2(st.session_state.app1_results)


if __name__ == "__main__":
    main()
