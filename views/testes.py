import streamlit as st
import altair as alt
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.set_page_config(page_title="Testes", page_icon="💎",layout="wide")

st.write("teste")

df = pd.DataFrame({
     "solution": [ ],
     "total_amount": [],
     "service_amount": [],
     "hours_amount": [],
     "num_horas_S": [],
     "num_horas_DS": [],
 })
 
def calc_hours(input_df):
  output_df = input_df.copy()
  output_df["num_horas"] = input_df["num_horas_S"] + input_df["num_horas_DS"]
  
  return output_df
 
st.title("Ejemplo")
 
 # Crear el editor
editable_df_new = st.data_editor(df,
                                   key="edit",
                                   hide_index=True,
                                   num_rows="dynamic",
                                   disabled=['num_horas']
                                   )
 
if st.button("Actualizar DataFrame"):
  new = calc_hours(editable_df_new)
  st.write(new)
