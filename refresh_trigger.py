import streamlit as st
import datetime as dt

def should_refresh_today():
    today = dt.datetime.today().weekday()
    return today in [1, 5]  # Tuesday (1) and Saturday (5)

def trigger_refresh():
    if should_refresh_today():
        st.experimental_rerun()
