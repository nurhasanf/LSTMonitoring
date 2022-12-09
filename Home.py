import streamlit as st
import ee
import json

st.set_page_config(
    page_title='LST Monitoring',
    page_icon='🌡️'
)

json_data = st.secrets["json_data"]
service_account = st.secrets["service_account"]

@st.experimental_memo(show_spinner=False)
def Initialize():
    # Preparing values
    json_object = json.loads(json_data, strict=False)
    json_object = json.dumps(json_object)
    # Authorising the app
    credentials = ee.ServiceAccountCredentials(service_account, key_data=json_object)
    ee.Initialize(credentials)

Initialize()

st.subheader('Monitoring Dinamika Land Surface Temperature di Kota Cirebon Menggunakan Citra Landsat 8 Multitemporal Berbasis Web')
st.image('Data/Pictures/temperature.gif')