import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.set_page_config(page_title="Pró-Corpo - Configurar Metas", page_icon="💎",layout="wide")

@st.cache_data()
def load_dataframe(worksheet):

  conn = st.connection("gsheets", type=GSheetsConnection)
  df = conn.read(worksheet=worksheet)

  return df

st.markdown("# Cadastrar Metas por Unidade")

st.session_state.setdefault("meta_unidade_df", load_dataframe("aux - Configurar metas unidade"))
df_metas = st.session_state["meta_unidade_df"]

df_unidades = load_dataframe("Auxiliar - Unidades - FB")
unidades = df_unidades["Unidade"].sort_values(ascending=True).unique()
unidades = list(unidades)

df_metas["month"] = pd.PeriodIndex(df_metas["month"], freq="M")

current_date = datetime.now()
periods = pd.period_range(start=current_date - pd.DateOffset(months=11),
                          end=current_date + pd.DateOffset(months=1), freq='M')

combined_periods = pd.concat([df_metas["month"], pd.Series(periods)])
combined_periods = combined_periods.drop_duplicates().sort_values(ascending=False)
combined_periods = combined_periods.reset_index(drop=True)

filtro_1, filtro_2 = st.columns([1,1])

with filtro_1:
  period_filter = st.selectbox("Selecione o Mês",combined_periods,index=1)

filtered_metas = df_metas.loc[df_metas["month"] == period_filter]

if filtered_metas.shape[0] == 0:
  filtered_metas = pd.DataFrame(columns=["unidade","month","meta facebook","meta google"])
  filtered_metas["unidade"] = unidades
  filtered_metas["month"] = period_filter

display_1,display_2,display_3 = st.columns([2,0.7,1])

with display_1:

  edited_df = st.data_editor(
      filtered_metas,
      column_config={
          "meta facebook": st.column_config.NumberColumn(
              "Meta Facebook (R$)", min_value=0, format="R$ %.2f"
          ),
          "meta google": st.column_config.NumberColumn(
              "Meta Google (R$)", min_value=0, format="R$ %.2f"
          ),
          "unidade": st.column_config.Column(
              "Unidade", disabled=True
          ),
          "month": st.column_config.Column(
              "Mês", disabled=True
          )
      },
      hide_index=True,
      use_container_width=True
  )
  df_total = edited_df
  df_total['total'] = df_total['meta facebook'].fillna(0) + df_total['meta google'].fillna(0)

  with display_2:
    st.metric("Total Geral",f"R$ {df_total['total'].sum() :.2f}")
    st.metric("Total Facebook",f"R$ {df_total['meta facebook'].sum() :.2f}")
    st.metric("Total Google",f"R$ {df_total['meta google'].sum() :.2f}")

  with display_3:

    st.dataframe(df_total[["unidade","total"]],
                 column_config={
                      "total": st.column_config.NumberColumn(
                       "Meta Total (R$)", min_value=0, format="R$ %.2f"
                    ),
                    "unidade": st.column_config.Column(
                        "Unidade")
                  },
                  hide_index=True,
                  use_container_width=True)

def upload_changes(df_original,df_edited):

  df_to_upload = pd.concat([df_original,df_edited])
  df_to_upload = df_to_upload.drop_duplicates(subset=["unidade","month"],keep="last")

  conn = st.connection("gsheets", type=GSheetsConnection)
  try:
    response = conn.update(data=df_to_upload,worksheet="aux - Configurar metas unidade")
    st.session_state["meta_unidade_df"]  = df_to_upload
    st.session_state["callback_meta_unidade_result"] = True
  except:
    response = "Erro"
    st.session_state["callback_meta_unidade_result"] = False

if st.button("Salvar modificações",on_click=upload_changes,args=(st.session_state["meta_unidade_df"],edited_df[["unidade","month","meta facebook","meta google"]])):
  if ("callback_meta_unidade_result" in st.session_state) and st.session_state["callback_meta_unidade_result"]:
    st.balloons()
    st.success("Modificações salvas com sucesso")

  else:
    st.error("Erro: Alterações não foram salvas")
