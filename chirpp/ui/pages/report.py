import datetime
import streamlit as st

import pandas as pd

def upload_logic(file_name):
    pass

st.set_page_config(layout="wide")

#inputs
start, end, include, get_button= st.columns([5,5,2,1])

@st.dialog("Upload Report", width="medium")
def upload_report_modal():
    st.write("Upload Filled in Report:")
    st.space(size="small")
    uploaded_file = st.file_uploader("Choose a file")

    if uploaded_file is not None:
        upload_logic(uploaded_file.getvalue())


with start:
    start_date=st.date_input("Start Date", datetime.date.today(), key="start_date")

with end:
    end=st.date_input("End Date", datetime.date.today(), key="end_date")

with include:
    include_non_chirpp=st.toggle("Include Non-Chirpp Visits", value=True, key="include_non_chirpp")

with get_button:
    report_button=st.button("Generate Report", type="primary", key="report_button",
                            width="stretch")
    upload_button = st.button("Upload Report", type="secondary",
                              key="upload_button", on_click=upload_report_modal,
                              width="stretch")



#TODO need to have dataframe here or somesuch