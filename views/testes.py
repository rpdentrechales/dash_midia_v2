import streamlit as st
import altair as alt
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.set_page_config(page_title="Testes", page_icon="💎",layout="wide")

st.write("teste")

# Sample dataframe with columns A and B, where column C is dependent on A and B
data = {
    'A': [10, 20, 30],
    'B': [1, 2, 3],
    'C': [10, 40, 90]  # Initially calculated as A * B
}

# Create a DataFrame
df = pd.DataFrame(data)

# Use st.data_editor to allow editing columns A and B
edited_df = st.data_editor(df[['A', 'B']], num_rows="dynamic", key="unique_editor")

# Recalculate column C based on the updated values in columns A and B
edited_df['C'] = edited_df['A'] * edited_df['B']

# Update the original dataframe with the recalculated values
df.update(edited_df)

# Display the updated dataframe in the same data editor
st.data_editor(df, num_rows="dynamic", key="updated_editor")
