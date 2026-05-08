"""
pages/01_fluxo_caixa.py — Fluxo de Caixa (fonte: fluxo_de_caixa.csv)
Estrutura idêntica ao Power BI: Ordem / Classificação / PLANO DE CONTAS
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os, sys

sys.path.append(str(__file__).replace("/pages/01_fluxo_caixa.py", ""))
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from style import apply_style, full_sidebar
from engine import MESES_ORDER

st.set_page_config(page_title="Fluxo de Caixa · Codi.com", layout="wide")
apply_style()



BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "data", "fluxo_de_caixa.csv")

@st.cache_data(show_spinner=False)
def load_fluxo():
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df.columns = df.columns.str.strip()
    df["Mês"] = df["Mês"].str.strip().str.lower()
    df["Classificação"] = df["Classificação"].str.strip()
    df["PLANO DE CONTAS"] = df["PLANO DE CONTAS"].str.strip()
    df["VALOR"] = pd.to_numeric(df["VALOR"], errors="coerce").fillna(0)
    df["Ano"] = df["Ano"].astype(int)
    return df

with st.spinner("Carregando..."):
    df_raw = load_fluxo()

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎛️ Filtros")
    anos_disp = sorted(df_raw["Ano"].unique())
    anos_sel  = st.multiselect("Ano", anos_disp, default=[max(anos_disp)], key="fc_ano")

    meses_no_csv = [m for m in MESES_ORDER if m in df_raw["Mês"].values]
    meses_sel = st.multiselect("Mês", [m.capitalize() for m in meses_no_csv], default=[], key="fc_mes")
    meses_sel_lower = [m.lower() for m in meses_sel] if meses_sel else None

    st.markdown("---")
    st.page_link("app.py",                         label="🏠 Visão Geral")
    st.page_link("pages/01_fluxo_caixa.py",        label="📊 Fluxo de Caixa")
    st.page_link("pages/02_dre.py",                label="📋 DRE")
    st.page_link("pages/03_projecao_dre.py",       label="🔮 Projeção DRE")
    st.page_link("pages/04_despesas_fornecedor.py",label="🏭 Despesas por Fornecedor")
    st.page_link("pages/05_simulacao_dfc.py",      label="⚡ Simulação DFC")

# ── Filtrar ────────────────────────────────────────────────────────────────
df = df_raw[df_raw["Ano"].isin(anos_sel)].copy()
if meses_sel_lower:
    df = df[df["Mês"].isin(meses_sel_lower)]

meses_present = [m for m in MESES_ORDER if m in df["Mês"].values]

def fmt(v):
    return f"R$ {abs(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ── Construir tabela hierárquica ──────────────────────────────────────────
rows = []
for classif in ["Receita", "Custo", "Despesas"]:
    sub_df = df[df["Classificação"] == classif]
    if sub_df.empty:
        continue

    # Linha header da classificação
    header = {"_tipo": "header", "Classificação": classif}
    total_c = 0
    for mes in meses_present:
        v = sub_df[sub_df["Mês"] == mes]["VALOR"].sum()
        header[mes.capitalize()] = fmt(v)
        total_c += v
    header["Total"] = fmt(total_c)
    rows.append(header)

    # Sub-linhas por PLANO DE CONTAS (ordenadas)
    planos = sorted(sub_df["PLANO DE CONTAS"].unique())
    for plano in planos:
        sub = {"_tipo": "sub", "Classificação": f"  {plano}"}
        sub_t = 0
        for mes in meses_present:
            v = sub_df[(sub_df["PLANO DE CONTAS"] == plano) & (sub_df["Mês"] == mes)]["VALOR"].sum()
            sub[mes.capitalize()] = fmt(v)
            sub_t += v
        sub["Total"] = fmt(sub_t)
        rows.append(sub)

df_fc = pd.DataFrame(rows)
col_order = ["Classificação"] + [m.capitalize() for m in meses_present] + ["Total"]
df_fc = df_fc[[c for c in col_order if c in df_fc.columns]]

def style_row(row):
    label = row["Classificação"].strip()
    if label == "Receita":
        return ["background-color: #1a3020; font-weight: 700; color: #C9A84C; font-size: 13px"] * len(row)
    if label in ("Custo", "Despesas"):
        return ["background-color: #1a2a1a; font-weight: 700; color: #8fbc8f; font-size: 13px"] * len(row)
    return ["color: #a0a0a0; font-size: 11px"] * len(row)

st.title("Fluxo de Caixa")

st.dataframe(
    df_fc.style.apply(style_row, axis=1),
    use_container_width=True,
    hide_index=True,
    height=620,
)

st.markdown("---")

# ── Gráfico ────────────────────────────────────────────────────────────────
st.subheader("Entradas × Saídas por mês")

rec_v, custo_v, desp_v, saldo_v = [], [], [], []
for mes in meses_present:
    r = df[(df["Classificação"] == "Receita")  & (df["Mês"] == mes)]["VALOR"].sum()
    c = df[(df["Classificação"] == "Custo")    & (df["Mês"] == mes)]["VALOR"].sum()
    d = df[(df["Classificação"] == "Despesas") & (df["Mês"] == mes)]["VALOR"].sum()
    rec_v.append(r); custo_v.append(abs(c)); desp_v.append(abs(d))
    saldo_v.append(r + c + d)  # c e d já negativos

meses_label = [m.capitalize() for m in meses_present]

fig = go.Figure()
fig.add_bar(name="Receita",  x=meses_label, y=rec_v,              marker_color="#C9A84C", opacity=0.9)
fig.add_bar(name="Custo",    x=meses_label, y=[-v for v in custo_v], marker_color="#E07050", opacity=0.85)
fig.add_bar(name="Despesas", x=meses_label, y=[-v for v in desp_v],  marker_color="#A05030", opacity=0.80)
fig.add_scatter(
    name="Saldo", x=meses_label, y=saldo_v,
    mode="lines+markers",
    line=dict(color="#4CAF9B", width=2.5),
    marker=dict(size=8),
)
fig.update_layout(
    barmode="relative",
    plot_bgcolor="#1a1a1a", paper_bgcolor="#1a1a1a", font_color="#d4d0c8",
    legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0),
    margin=dict(l=0, r=0, t=40, b=0), height=400,
    yaxis=dict(gridcolor="#2a2a2a", tickprefix="R$ ", tickformat=",.0f"),
    xaxis=dict(gridcolor="#2a2a2a"),
)
st.plotly_chart(fig, use_container_width=True)

# ── NCG ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Necessidade de Capital de Giro (NCG)")

total_rec = df[df["Classificação"] == "Receita"]["VALOR"].sum()
total_sai = df[df["Classificação"] != "Receita"]["VALOR"].sum()
ncg       = total_rec + total_sai

c1, c2, c3 = st.columns(3)
c1.metric("Total Saídas",        fmt(abs(total_sai)))
c2.metric("Previsão de Receita", fmt(total_rec))
c3.metric("Saldo Líquido (NCG)", fmt(ncg))
