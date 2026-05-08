"""
app.py — Sistema Financeiro Codi.com
Página principal com navegação e visão geral
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from engine import (
    load_vendas, load_contas, build_kpis, build_dre_pivot,
    filter_vendas, filter_cap, MESES_ORDER
)

st.set_page_config(
    page_title="Codi.com · Financeiro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #111111 !important;
    border-right: 1px solid #2a2a2a;
}
[data-testid="stSidebar"] * { color: #d4d0c8 !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label { color: #888 !important; font-size: 11px !important; text-transform: uppercase; letter-spacing: 0.08em; }

/* Metric cards */
[data-testid="metric-container"] {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 10px;
    padding: 16px 20px;
}
[data-testid="metric-container"] label { color: #888 !important; font-size: 11px !important; text-transform: uppercase; letter-spacing: 0.06em; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #f0ede8 !important; font-size: 22px !important; font-weight: 600; }
[data-testid="metric-container"] [data-testid="stMetricDelta"] { font-size: 12px !important; }

/* Headers */
h1 { color: #C9A84C !important; font-weight: 600 !important; letter-spacing: -0.02em; }
h2, h3 { color: #f0ede8 !important; font-weight: 500 !important; }

/* Dataframe */
[data-testid="stDataFrame"] { border: 1px solid #2a2a2a; border-radius: 8px; }

/* Tabs */
[data-baseweb="tab-list"] { background: #1a1a1a; border-radius: 8px; padding: 4px; gap: 4px; }
[data-baseweb="tab"] { background: transparent !important; color: #888 !important; border-radius: 6px !important; }
[aria-selected="true"] { background: #C9A84C !important; color: #111 !important; }

/* Divider */
hr { border-color: #2a2a2a; }

/* Logo area */
.logo-area { padding: 8px 0 24px 0; border-bottom: 1px solid #2a2a2a; margin-bottom: 24px; }
.logo-text { font-size: 20px; font-weight: 600; color: #C9A84C; letter-spacing: 0.05em; }
.logo-sub  { font-size: 10px; color: #555; text-transform: uppercase; letter-spacing: 0.15em; }
</style>
""", unsafe_allow_html=True)

# ── Carregar dados ────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_all_data():
    vendas, impostos, cv, ca, custo = load_vendas()
    cap, car = load_contas()
    return vendas, impostos, cv, ca, custo, cap, car

with st.spinner("Carregando dados..."):
    vendas, impostos, cv, ca, custo, cap, car = get_all_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="logo-area"><div class="logo-text">CODI.COM</div><div class="logo-sub">Jeans Wear · Sistema Financeiro</div></div>', unsafe_allow_html=True)

    anos_disp = sorted(vendas["ANO"].dropna().unique().astype(int))
    anos_sel = st.multiselect("Ano", anos_disp, default=anos_disp)

    meses_disp = [m for m in MESES_ORDER if m in vendas["MES"].values]
    meses_sel = st.multiselect("Mês", meses_disp, default=[])

    if not meses_sel:
        meses_sel = None

    st.markdown("---")
    st.caption("Navegação")
    st.page_link("app.py", label="🏠 Visão Geral", icon=None)
    st.page_link("pages/01_fluxo_caixa.py",      label="📊 Fluxo de Caixa")
    st.page_link("pages/02_dre.py",               label="📋 DRE")
    st.page_link("pages/03_projecao_dre.py",      label="🔮 Projeção DRE")
    st.page_link("pages/04_despesas_fornecedor.py", label="🏭 Despesas por Fornecedor")
    st.page_link("pages/05_simulacao_dfc.py",     label="⚡ Simulação DFC")

# ── KPIs ──────────────────────────────────────────────────────────────────────
kpis = build_kpis(vendas, impostos, cv, ca, custo, cap, anos=anos_sel, meses=meses_sel)

st.markdown("# Visão Geral")
st.caption(f"Período: {', '.join(map(str, anos_sel))} {'· ' + ', '.join(meses_sel) if meses_sel else ''}")

def fmt(v): return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def pct(v): return f"{v:.1%}"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Receita Bruta", fmt(kpis["receita"]))
col2.metric("Margem Bruta", fmt(kpis["margem_bruta"]), pct(kpis["margem_bruta_pct"]))
col3.metric("Ebitda Operacional", fmt(kpis["ebtida_operacional"]), pct(kpis["ebtida_operacional_pct"]))
col4.metric("Ebitda Final", fmt(kpis["ebtida_final"]), pct(kpis["ebtida_final_pct"]))

st.markdown("---")

col5, col6, col7, col8 = st.columns(4)
col5.metric("CMV", fmt(kpis["custo"]), f"{kpis['custo']/kpis['receita']:.1%}" if kpis["receita"] else "—")
col6.metric("Simples Nacional", fmt(kpis["impostos"]))
col7.metric("Comissões", fmt(kpis["comissao"]))
col8.metric("Despesas c/ Folha", fmt(kpis["desp_folha"]))

st.markdown("---")

# ── Gráfico receita x margem por mês ─────────────────────────────────────────
st.subheader("Receita × Margem Bruta por mês")

from engine import build_dre
vf = filter_vendas(vendas, anos_sel, meses_sel)
imp_f = filter_vendas(impostos, anos_sel, meses_sel)
cv_f = filter_vendas(cv, anos_sel, meses_sel)
ca_f = filter_vendas(ca, anos_sel, meses_sel)
cu_f = filter_vendas(custo, anos_sel, meses_sel)
cap_f = filter_cap(cap, anos_sel, meses_sel)

dre = build_dre(vf, imp_f, cv_f, ca_f, cu_f, cap_f, groupby="MES")

if not dre.empty:
    rec_mes = dre[dre["Conta"] == "1-Receita Bruta"][["MES", "ValorDRE"]].copy()
    mg_mes  = dre[dre["Conta"] == "5-Margem Bruta R$"][["MES", "ValorDRE"]].copy()
    ebt_mes = dre[dre["Conta"] == "9.3-Ebtida Final"][["MES", "ValorDRE"]].copy()

    rec_mes = rec_mes.set_index("MES").reindex([m for m in MESES_ORDER if m in rec_mes["MES"].values])
    mg_mes  = mg_mes.set_index("MES").reindex(rec_mes.index)
    ebt_mes = ebt_mes.set_index("MES").reindex(rec_mes.index)

    fig = go.Figure()
    fig.add_bar(
        name="Receita Bruta",
        x=rec_mes.index,
        y=rec_mes["ValorDRE"],
        marker_color="#C9A84C",
        opacity=0.85,
    )
    fig.add_bar(
        name="Margem Bruta",
        x=mg_mes.index,
        y=mg_mes["ValorDRE"],
        marker_color="#4CAF9B",
        opacity=0.85,
    )
    fig.add_scatter(
        name="Ebitda Final",
        x=ebt_mes.index,
        y=ebt_mes["ValorDRE"],
        mode="lines+markers",
        line=dict(color="#E07050", width=2),
        marker=dict(size=7),
    )
    fig.update_layout(
        plot_bgcolor="#1a1a1a",
        paper_bgcolor="#1a1a1a",
        font_color="#d4d0c8",
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(l=0, r=0, t=40, b=0),
        height=340,
        yaxis=dict(gridcolor="#2a2a2a", tickprefix="R$ ", tickformat=",.0f"),
        xaxis=dict(gridcolor="#2a2a2a"),
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Mini DRE resumo ───────────────────────────────────────────────────────────
st.subheader("Resumo DRE")

dre_data = {
    "Conta": [
        "1-Receita Bruta", "2-Custo Mercadoria Vendida", "3-Simples Nacional",
        "4-Comissão", "5-Margem Bruta R$", "6-Despesas Operacionais",
        "7-Despesas com Folha", "8-Ebtida Operacional",
        "9.1-Empréstimos", "9.2-Retirada de sócios", "9.3-Ebtida Final"
    ],
    "Valor (R$)": [
        kpis["receita"], kpis["custo"], kpis["impostos"],
        kpis["comissao"], kpis["margem_bruta"], kpis["desp_operacional"],
        kpis["desp_folha"], kpis["ebtida_operacional"],
        kpis["emprestimos"], kpis["retiradas"], kpis["ebtida_final"]
    ],
    "AV%": [
        kpis["receita"] / kpis["receita"] if kpis["receita"] else 0,
        kpis["custo"] / kpis["receita"] if kpis["receita"] else 0,
        kpis["impostos"] / kpis["receita"] if kpis["receita"] else 0,
        kpis["comissao"] / kpis["receita"] if kpis["receita"] else 0,
        kpis["margem_bruta_pct"],
        kpis["desp_operacional"] / kpis["receita"] if kpis["receita"] else 0,
        kpis["desp_folha"] / kpis["receita"] if kpis["receita"] else 0,
        kpis["ebtida_operacional_pct"],
        kpis["emprestimos"] / kpis["receita"] if kpis["receita"] else 0,
        kpis["retiradas"] / kpis["receita"] if kpis["receita"] else 0,
        kpis["ebtida_final_pct"],
    ]
}

df_resumo = pd.DataFrame(dre_data)

def color_rows(row):
    negativo = row["Valor (R$)"] < 0
    if row["Conta"] in ["5-Margem Bruta R$", "8-Ebtida Operacional", "9.3-Ebtida Final"]:
        cor = "#1a3a2a" if not negativo else "#3a1a1a"
        return [f"background-color: {cor}"] * len(row)
    return [""] * len(row)

df_styled = (
    df_resumo.style
    .apply(color_rows, axis=1)
    .format({"Valor (R$)": lambda v: fmt(v), "AV%": "{:.1%}"})
)
st.dataframe(df_styled, use_container_width=True, hide_index=True, height=420)
