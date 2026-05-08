"""
pages/04_despesas_fornecedor.py — Despesas por fornecedor
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
sys.path.append(str(__file__).replace("/pages/04_despesas_fornecedor.py", ""))
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from style import apply_style, full_sidebar

from engine import load_vendas, load_contas, filter_cap, MESES_ORDER

st.set_page_config(page_title="Despesas por Fornecedor · Codi.com", layout="wide")
apply_style()



@st.cache_data(show_spinner=False)
def get_all():
    v, i, cv, ca, cu = load_vendas()
    cap, car = load_contas()
    return cap, car

with st.spinner("Carregando..."):
    cap, car = get_all()

with st.sidebar:
    st.markdown("### 🎛️ Filtros")
    anos_disp = sorted(cap["ANO"].dropna().unique().astype(int))
    anos_sel = st.multiselect("Ano", anos_disp, default=anos_disp, key="forn_ano")
    meses_disp = [m for m in MESES_ORDER if m in cap["MES"].values]
    meses_sel = st.multiselect("Mês", meses_disp, default=[], key="forn_mes")
    if not meses_sel:
        meses_sel = None

    planos_disp = sorted(cap["PLANO DE CONTAS"].dropna().unique())
    planos_sel = st.multiselect("Plano de Contas", planos_disp, default=[], key="forn_plano")

    top_n = st.slider("Top fornecedores", 5, 30, 15)

    st.markdown("---")
    st.page_link("app.py", label="🏠 Visão Geral")
    st.page_link("pages/01_fluxo_caixa.py", label="📊 Fluxo de Caixa")
    st.page_link("pages/02_dre.py", label="📋 DRE")
    st.page_link("pages/03_projecao_dre.py", label="🔮 Projeção DRE")
    st.page_link("pages/04_despesas_fornecedor.py", label="🏭 Despesas por Fornecedor")
    st.page_link("pages/05_simulacao_dfc.py", label="⚡ Simulação DFC")

def fmt(v): return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

cap_f = filter_cap(cap, anos_sel, meses_sel)
if planos_sel:
    cap_f = cap_f[cap_f["PLANO DE CONTAS"].isin(planos_sel)]

st.title("Despesas por Fornecedor")

if cap_f.empty:
    st.warning("Sem dados para os filtros selecionados.")
    st.stop()

# ── Top fornecedores ───────────────────────────────────────────────────────
top = (
    cap_f.groupby("PESSOA")["VALOR"].sum()
    .sort_values(ascending=False)
    .head(top_n)
    .reset_index()
)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"Top {top_n} fornecedores")
    fig_bar = go.Figure(go.Bar(
        x=top["VALOR"],
        y=top["PESSOA"],
        orientation="h",
        marker_color="#C9A84C",
        text=[fmt(v) for v in top["VALOR"]],
        textposition="outside",
    ))
    fig_bar.update_layout(
        plot_bgcolor="#1a1a1a", paper_bgcolor="#1a1a1a",
        font_color="#d4d0c8",
        margin=dict(l=0, r=80, t=10, b=0),
        height=max(300, top_n * 28),
        xaxis=dict(gridcolor="#2a2a2a", tickprefix="R$ ", tickformat=",.0f"),
        yaxis=dict(gridcolor="#2a2a2a", autorange="reversed"),
        showlegend=False,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    st.subheader("Por Plano de Contas")
    por_plano = (
        cap_f.groupby("PLANO DE CONTAS")["VALOR"].sum()
        .sort_values(ascending=False)
        .head(15)
        .reset_index()
    )
    fig_pie = px.pie(
        por_plano, values="VALOR", names="PLANO DE CONTAS",
        color_discrete_sequence=px.colors.sequential.YlOrBr_r,
        hole=0.45,
    )
    fig_pie.update_layout(
        plot_bgcolor="#1a1a1a", paper_bgcolor="#1a1a1a",
        font_color="#d4d0c8",
        margin=dict(l=0, r=0, t=10, b=0),
        height=360,
        showlegend=True,
        legend=dict(font=dict(size=10)),
    )
    fig_pie.update_traces(textposition="inside", textinfo="percent")
    st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

# ── Tabela por fornecedor × mês ────────────────────────────────────────────
st.subheader("Detalhamento por fornecedor e mês")

meses_present = [m for m in MESES_ORDER if m in cap_f["MES"].values]
top_pessoas = top["PESSOA"].tolist()

pivot = (
    cap_f[cap_f["PESSOA"].isin(top_pessoas)]
    .groupby(["PESSOA", "MES"])["VALOR"]
    .sum()
    .unstack(fill_value=0)
)
pivot = pivot.reindex(columns=[m for m in MESES_ORDER if m in pivot.columns])
pivot.columns = [c.capitalize() for c in pivot.columns]
pivot["Total"] = pivot.sum(axis=1)
pivot = pivot.sort_values("Total", ascending=False)

fmt_cols = {c: lambda v: fmt(v) for c in pivot.columns}
st.dataframe(
    pivot.style.format(fmt_cols).background_gradient(
        subset=["Total"], cmap="YlOrBr"
    ),
    use_container_width=True,
    height=400,
)

st.markdown("---")

# ── Evolução mensal dos maiores fornecedores ───────────────────────────────
st.subheader("Evolução mensal — Top 5 fornecedores")

top5 = top.head(5)["PESSOA"].tolist()
df_evol = cap_f[cap_f["PESSOA"].isin(top5)].groupby(["PESSOA", "MES", "MES_NUM"])["VALOR"].sum().reset_index()
df_evol = df_evol.sort_values("MES_NUM")

fig_evol = go.Figure()
colors = ["#C9A84C", "#4CAF9B", "#E07050", "#7B9FD4", "#B07ABF"]
for i, pessoa in enumerate(top5):
    d = df_evol[df_evol["PESSOA"] == pessoa].sort_values("MES_NUM")
    fig_evol.add_scatter(
        name=pessoa[:30],
        x=[m.capitalize() for m in d["MES"]],
        y=d["VALOR"],
        mode="lines+markers",
        line=dict(color=colors[i % len(colors)], width=2),
        marker=dict(size=7),
    )

fig_evol.update_layout(
    plot_bgcolor="#1a1a1a", paper_bgcolor="#1a1a1a",
    font_color="#d4d0c8",
    legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0, font=dict(size=10)),
    margin=dict(l=0, r=0, t=40, b=0),
    height=340,
    yaxis=dict(gridcolor="#2a2a2a", tickprefix="R$ ", tickformat=",.0f"),
    xaxis=dict(gridcolor="#2a2a2a"),
)
st.plotly_chart(fig_evol, use_container_width=True)
