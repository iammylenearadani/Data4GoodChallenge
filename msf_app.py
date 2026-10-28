"""MSF Field Library — one app, two views.   streamlit run msf_app.py
Field search (field.py): search only, 4 interface languages, QR code for team phones.
Data science (app.py): filters, search modes, document web, collection & data quality, evaluation."""
import streamlit as st

st.navigation([st.Page("field.py", title="Field search", default=True),
               st.Page("app.py", title="Data science")], position="top").run()
