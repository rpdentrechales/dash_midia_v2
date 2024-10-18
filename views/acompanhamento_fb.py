import streamlit as st
import altair as alt
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.set_page_config(page_title="Pró-Corpo - Acompanhamento", page_icon="💎",layout="wide")

# Calcula dias até o final do mês
def days_until_end_of_month(period):
    today = datetime.today()

    if period.year == today.year and period.month == today.month:
        last_day_of_month = period.end_time
        days_remaining = (last_day_of_month - pd.Timestamp(today)).days
        return days_remaining
    else:
        return None

# Carrega os dados do sheets, remove duplicadas e atualiza a planilha.
@st.cache_data
def load_main_dataframe(worksheet):

  conn = st.connection("gsheets", type=GSheetsConnection)
  df = conn.read(worksheet=worksheet,dtype={"Ad ID": str})

  df['Day'] = pd.to_datetime(df['Day'])

  df["Ad ID"] = df["Ad ID"].astype(str)

  df.drop_duplicates(subset=["Day","Ad ID"],inplace=True)

  conn.update(data=df,worksheet=worksheet)

  return df

# Carrega os dados do sheets, remove duplicadas e retorna um dataframe
@st.cache_data
def load_aux_dataframe(worksheet,duplicates_subset):

  conn = st.connection("gsheets", type=GSheetsConnection)
  df = conn.read(worksheet=worksheet)
  df = df.drop_duplicates(subset=duplicates_subset)

  return df

def update_sheet(df,worksheet):

  conn = st.connection("gsheets", type=GSheetsConnection)
  df = df.drop_duplicates(keep="last")
  conn.update(data=df,worksheet=worksheet)

  return df

# Carrega os dados das plataformas de mídia
df_fb = load_main_dataframe("Compilado - FB e Gads")
df_fb = df_fb.loc[df_fb["Plataforma"] == "Facebook"]

# Carrega os de-paras de unidade e categoria de FB
df_categorias = load_aux_dataframe("Auxiliar - Categorias - FB","Anuncio")
df_unidades = load_aux_dataframe("Auxiliar - Unidades - FB","Campaign Name")
df_whatsapp = load_aux_dataframe("Auxiliar - Whatsapp - FB","Ad Name")

# Carrega os dados de meta
if "df_meta_categoria" in st.session_state:
  df_metas_categoria = st.session_state["df_meta_categoria"]
else:
  df_metas_categoria = load_aux_dataframe("aux - Configurar metas categoria",["plataforma","categoria","unidade"])

df_metas_unidade = load_aux_dataframe("aux - Configurar metas unidade",["unidade","month"])

# Padroniza as datas nos dataframes das metas
df_metas_unidade['month'] = pd.to_datetime(df_metas_unidade['month'])
df_metas_unidade['month'] = df_metas_unidade['month'].dt.to_period('M')

df_fb = pd.merge(df_fb,df_categorias,how="left",left_on="Ad Name",right_on="Anuncio")
df_fb = df_fb.drop(columns=["Anuncio"])
df_fb["Results"] = df_fb["Results"].fillna(0)

df_fb = pd.merge(df_fb,df_unidades,how="left",left_on="Campaign Name",right_on="Campaign Name")
df_fb["Unidade"] = df_fb["Unidade"].fillna("Sem Categoria")
df_fb["Região"] = df_fb["Região"].fillna("Sem Categoria")

whatsapp_map = df_whatsapp.set_index('Ad Name')['Categoria'].to_dict()
df_fb.loc[df_fb['Account Name'] == "Campanhas Whatsapp","Categoria"] = df_fb.loc[df_fb['Account Name'] == "Campanhas Whatsapp","Ad Name"].map(whatsapp_map)

df_fb["Categoria"] = df_fb["Categoria"].fillna("Sem Categoria")
df_fb["month"] = df_fb["Day"].dt.to_period("M")

df_sem_cirurgia = df_fb.loc[df_fb["Account Name"] != "CA1 - ANUNCIANTE - MAIS CIRURGIA"]
df_cirurgia = df_fb.loc[df_fb["Account Name"] == "CA1 - ANUNCIANTE - MAIS CIRURGIA"]

titulo_1,titulo_2 = st.columns([3,1])

with titulo_1:
  st.markdown("# Acompanhamento de Mídia")

with titulo_2:
  month_filter = st.selectbox(label = "Selecione o Mês",
                                   placeholder= 'Selecione o mês',
                                   options=df_sem_cirurgia['month'].sort_values(ascending=False).unique())

st.markdown("## Facebook - Total por Unidade")

store_filter = st.selectbox(label = "Selecione a Unidade",
                                   placeholder= 'Selecione a Unidade',
                                   options=df_sem_cirurgia['Unidade'].unique())

if (month_filter):
  df_sem_cirurgia = df_sem_cirurgia.loc[df_sem_cirurgia['month'] == month_filter]
  df_meta_unidade_mes = df_metas_unidade.loc[df_metas_unidade['month'] == month_filter]

  # Verifica se há metas para o mês selecionado. Se não houver, copia as metas do mês anterior.

  if len(df_meta_unidade_mes) == 0:
    df_meta_unidade_mes_to_add = df_metas_unidade.loc[df_metas_unidade['month'] == month_filter - 1]
    df_meta_unidade_mes_to_add["month"] = month_filter
    if len(df_meta_unidade_mes_to_add) > 0:
      df_metas_unidade = pd.concat([df_metas_unidade,df_meta_unidade_mes_to_add])
      df_metas_unidade = update_sheet(df_metas_unidade,"aux - Configurar metas unidade")

if (store_filter):
  df_filtered = df_sem_cirurgia.loc[df_sem_cirurgia['Unidade'] == store_filter]
  meta_unidade_selecionada = df_meta_unidade_mes.loc[df_meta_unidade_mes['unidade'] == store_filter]
  meta_categoria_selecionada = df_metas_categoria.loc[df_metas_categoria['unidade'] == store_filter]

meta_facebook_mes = meta_unidade_selecionada["meta facebook"].values[0]
meta_categoria_fb = meta_categoria_selecionada.loc[meta_categoria_selecionada["plataforma"] == "Facebook"]

metrics_unidade_1,metrics_unidade_2,metrics_unidade_3,metrics_unidade_4,metrics_unidade_5,metrics_unidade_6 = st.columns(6)

total_unidade_resultados = df_filtered["Results"].sum()
total_unidade_custo = df_filtered["Amount Spent"].sum()
total_unidade_cpl = total_unidade_custo/total_unidade_resultados

verba_restante = meta_facebook_mes - total_unidade_custo
dias_para_o_fim_do_mes = days_until_end_of_month(month_filter)

if dias_para_o_fim_do_mes:
  verba_restante_por_dia = verba_restante/dias_para_o_fim_do_mes
  verba_restante_por_dia = f"R$ {verba_restante_por_dia :.2f}"
else:
  verba_restante_por_dia = "-"

with metrics_unidade_1:
  st.metric("Resultados Total",f"{total_unidade_resultados :.0f}")
with metrics_unidade_2:
  st.metric("Custo Total",f"R$ {total_unidade_custo :.2f}")
with metrics_unidade_3:
  st.metric("CPL Total",f"R$ {total_unidade_cpl :.2f}")
with metrics_unidade_4:
  st.metric("Verba Total",f"R$ {meta_facebook_mes :.2f}")
with metrics_unidade_5:
  st.metric("Verba Restante",f"R$ {verba_restante :.2f}")
with metrics_unidade_6:
  st.metric("Verba Restante por dia",verba_restante_por_dia)

categoria_groupby = df_filtered.groupby(["Categoria"]).agg({"Results":"sum","Amount Spent":"sum"})

categoria_groupby["CPL"] = categoria_groupby["Amount Spent"]/categoria_groupby["Results"]

categoria_total_row = pd.DataFrame(categoria_groupby[['Results', 'Amount Spent']].sum()).transpose()
categoria_total_row["CPL"] = categoria_total_row['Amount Spent']/categoria_total_row['Results']

categoria_total_resultados = categoria_total_row['Results'].values[0]
categoria_total_custo = categoria_total_row['Amount Spent'].values[0]
categoria_total_cpl = categoria_total_row['CPL'].values[0]

categoria_groupby["share_custo"] = (categoria_groupby["Amount Spent"]/categoria_total_custo) * 100
categoria_groupby["share_resultados"] = (categoria_groupby["Results"]/categoria_total_resultados) * 100

categoria_groupby = pd.merge(categoria_groupby,meta_categoria_fb[["categoria","meta"]],how="left",left_on=["Categoria"],right_on=["categoria"])

categoria_groupby["verba total"] = meta_facebook_mes*categoria_groupby["meta"]/100
categoria_groupby["verba restante"] = categoria_groupby["verba total"] - categoria_groupby["Amount Spent"]

if dias_para_o_fim_do_mes:
  categoria_groupby["verba restante por dia"] = categoria_groupby["verba restante"]/dias_para_o_fim_do_mes
else:
  categoria_groupby["verba restante por dia"] = 0

colunas = ["categoria","meta","Amount Spent","Results","CPL","share_custo","share_resultados","verba total","verba restante","verba restante por dia"]

colunas_fixas = ["categoria","Amount Spent","Results","CPL","share_custo","share_resultados","verba total","verba restante","verba restante por dia"]

tabela_acompanhamento = st.data_editor(
    categoria_groupby,
    use_container_width=True,
    column_order=colunas,
    disabled=colunas_fixas,
    hide_index=True,
    column_config={
        "meta": st.column_config.NumberColumn(
            "Meta",
            format="%.2f %%",
            width="small"
        ),
        "Amount Spent": st.column_config.NumberColumn(
            "Custo",
            format="R$ %.2f",
            width="small"
        ),
        "CPL": st.column_config.NumberColumn(
            "CPL",
            format="R$ %.2f",
            width="small"
        ),
        "categoria": st.column_config.Column(
            "Categoria",
            width="medium"
        ),
        "Results": st.column_config.NumberColumn(
            "Resultados",
            width="small"
        ),
        "share_custo": st.column_config.NumberColumn(
            "Share Custo (%)",
            format="%.2f %%",
            width="small"
        ),
        "share_resultados": st.column_config.NumberColumn(
            "Share Resultados (%)",
            format="%.2f %%",
            width="small"
        ),
        "verba total": st.column_config.NumberColumn(
            "Verba total",
            format="R$ %.2f",
            width="small"
        ),
        "verba restante": st.column_config.NumberColumn(
            "Verba Restante",
            format="R$ %.2f",
            width="small"
        ),
        "verba restante por dia": st.column_config.NumberColumn(
            "verba restante por dia",
            format="R$ %.2f",
            width="small"
        )
    }
  )

porcentagem_total = tabela_acompanhamento["meta"].sum()

if (porcentagem_total == 100.00):
  st.success(f'Total da meta: {porcentagem_total} %', icon="✅")
else:
  st.error(f'Total da meta: {porcentagem_total} %', icon="⚠️")

if st.button("Atualizar Metas",type="primary"):

  meta_updated = tabela_acompanhamento[["categoria","meta"]]
  meta_updated["unidade"] = store_filter
  meta_updated["plataforma"] = "Facebook"

  df_metas_categorias_updated = pd.concat([df_metas_categoria,meta_updated])
  df_metas_categorias_updated = df_metas_categorias_updated.drop_duplicates(subset=["plataforma","unidade","categoria"],keep="last")
  df_metas_categorias_updated = update_sheet(df_metas_categorias_updated,"aux - Configurar metas categoria")

  st.session_state["df_meta_categoria"] = df_metas_categorias_updated
  st.ballons()
