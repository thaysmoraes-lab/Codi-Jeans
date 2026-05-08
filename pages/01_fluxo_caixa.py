"""
pages/01_fluxo_caixa.py — Fluxo de Caixa hierárquico
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
sys.path.append(str(__file__).replace("/pages/01_fluxo_caixa.py", ""))

from engine import (
    load_vendas, load_contas, filter_vendas, filter_cap,
    MESES_ORDER, DESPESAS_OPERACIONAIS, DESPESAS_FOLHA,
    receita_dre, despesas_operacionais, despesas_folha,
    emprestimos, retiradas_socios
)

st.set_page_config(page_title="Fluxo de Caixa · Codi.com", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
[data-testid="stSidebar"] { background: #111111 !important; border-right: 1px solid #2a2a2a; }
[data-testid="stSidebar"] * { color: #d4d0c8 !important; }
h1 { color: #C9A84C !important; font-weight: 600 !important; }
h2, h3 { color: #f0ede8 !important; font-weight: 500 !important; }
hr { border-color: #2a2a2a; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def get_all():
    v, i, cv, ca, cu = load_vendas()
    cap, car = load_contas()
    return v, i, cv, ca, cu, cap, car

with st.spinner("Carregando..."):
    vendas, impostos, cv, ca, custo, cap, car = get_all()

with st.sidebar:
    st.markdown("### 🎛️ Filtros")
    anos_disp = sorted(vendas["ANO"].dropna().unique().astype(int))
    anos_sel = st.multiselect("Ano", anos_disp, default=anos_disp, key="fc_ano")
    meses_disp = [m for m in MESES_ORDER if m in vendas["MES"].values]
    meses_sel = st.multiselect("Mês", meses_disp, default=[], key="fc_mes")
    if not meses_sel:
        meses_sel = None

    st.markdown("---")
    st.page_link("app.py", label="🏠 Visão Geral")
    st.page_link("pages/01_fluxo_caixa.py", label="📊 Fluxo de Caixa")
    st.page_link("pages/02_dre.py", label="📋 DRE")
    st.page_link("pages/03_projecao_dre.py", label="🔮 Projeção DRE")
    st.page_link("pages/04_despesas_fornecedor.py", label="🏭 Despesas por Fornecedor")
    st.page_link("pages/05_simulacao_dfc.py", label="⚡ Simulação DFC")

def fmt(v): return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

vf   = filter_vendas(vendas, anos_sel, meses_sel)
cap_f = filter_cap(cap, anos_sel, meses_sel)
car_f = filter_cap(car, anos_sel, meses_sel)

st.title("Fluxo de Caixa")

# ── Receita mensal ─────────────────────────────────────────────────────────
rec_mes = (
    vf.groupby(["MES", "MES_NUM"])["VALOR TOTAL"]
    .sum().reset_index()
    .sort_values("MES_NUM")
)

# ── Tabela hierárquica Receita / Custo / Despesa por mês ──────────────────
meses_present = [m for m in MESES_ORDER if m in rec_mes["MES"].values]

# Agrupa despesas por PLANO DE CONTAS e mês
cap_grupo = (
    cap_f.groupby(["PLANO DE CONTAS", "MES", "MES_NUM"])["VALOR"]
    .sum().reset_index()
)

# Classificar cada plano
def classifica(plano):
    if plano in DESPESAS_FOLHA:
        return "Despesas com Folha"
    if plano in DESPESAS_OPERACIONAIS:
        return "Despesas Operacionais"
    if plano == "Empréstimos":
        return "Financeiro"
    if plano == "Retiradas de Sócios":
        return "Financeiro"
    return "Custo"

cap_grupo["Classificação"] = cap_grupo["PLANO DE CONTAS"].apply(classifica)

# Pivot por classificação e mês
rows = []
for classif in ["Receita", "Custo", "Despesas com Folha", "Despesas Operacionais", "Financeiro"]:
    row = {"Ordem": classif, "Classificação": classif}
    total = 0
    for mes in meses_present:
        if classif == "Receita":
            v = rec_mes[rec_mes["MES"] == mes]["VALOR TOTAL"].sum()
        else:
            v = cap_grupo[(cap_grupo["Classificação"] == classif) & (cap_grupo["MES"] == mes)]["VALOR"].sum()
        row[mes.capitalize()] = fmt(v)
        total += v
    row["Total"] = fmt(total)
    rows.append(row)

    # Sub-linhas
    if classif != "Receita":
        planos = cap_grupo[cap_grupo["Classificação"] == classif]["PLANO DE CONTAS"].unique()
        for plano in sorted(planos):
            sub = {"Ordem": f"  {plano}", "Classificação": f"  {plano}"}
            sub_total = 0
            for mes in meses_present:
                v = cap_grupo[
                    (cap_grupo["PLANO DE CONTAS"] == plano) & (cap_grupo["MES"] == mes)
                ]["VALOR"].sum()
                sub[mes.capitalize()] = fmt(v)
                sub_total += v
            sub["Total"] = fmt(sub_total)
            rows.append(sub)

df_fc = pd.DataFrame(rows)

def style_fc(row):
    classifs = ["Receita", "Custo", "Despesas com Folha", "Despesas Operacionais", "Financeiro"]
    if row["Classificação"].strip() in classifs:
        return ["background-color: #1a2a1a; font-weight: 600; color: #C9A84C"] * len(row)
    return ["color: #a0a0a0; font-size: 12px"] * len(row)

st.dataframe(
    df_fc.drop(columns=["Ordem"]).style.apply(style_fc, axis=1),
    use_container_width=True,
    hide_index=True,
    height=500,
)

st.markdown("---")

# ── Gráfico barras empilhadas mensal ───────────────────────────────────────
st.subheader("Entradas × Saídas por mês")

rec_vals  = [rec_mes[rec_mes["MES"] == m]["VALOR TOTAL"].sum() for m in meses_present]
custo_vals = [cap_grupo[(cap_grupo["Classificação"] == "Custo") & (cap_grupo["MES"] == m)]["VALOR"].sum() for m in meses_present]
folha_vals = [cap_grupo[(cap_grupo["Classificação"] == "Despesas com Folha") & (cap_grupo["MES"] == m)]["VALOR"].sum() for m in meses_present]
desp_vals  = [cap_grupo[(cap_grupo["Classificação"] == "Despesas Operacionais") & (cap_grupo["MES"] == m)]["VALOR"].sum() for m in meses_present]
fin_vals   = [cap_grupo[(cap_grupo["Classificação"] == "Financeiro") & (cap_grupo["MES"] == m)]["VALOR"].sum() for m in meses_present]
saldo_vals = [rec_vals[i] - custo_vals[i] - folha_vals[i] - desp_vals[i] - fin_vals[i] for i in range(len(meses_present))]

meses_label = [m.capitalize() for m in meses_present]

fig = go.Figure()
fig.add_bar(name="Receita",          x=meses_label, y=rec_vals,   marker_color="#C9A84C", opacity=0.9)
fig.add_bar(name="Custo",            x=meses_label, y=[-v for v in custo_vals], marker_color="#E07050", opacity=0.85)
fig.add_bar(name="Folha",            x=meses_label, y=[-v for v in folha_vals], marker_color="#C06040", opacity=0.8)
fig.add_bar(name="Desp. Operac.",    x=meses_label, y=[-v for v in desp_vals],  marker_color="#A05030", opacity=0.75)
fig.add_bar(name="Financeiro",       x=meses_label, y=[-v for v in fin_vals],   marker_color="#803020", opacity=0.7)
fig.add_scatter(
    name="Saldo", x=meses_label, y=saldo_vals,
    mode="lines+markers",
    line=dict(color="#4CAF9B", width=2.5),
    marker=dict(size=8),
)

fig.update_layout(
    barmode="relative",
    plot_bgcolor="#1a1a1a", paper_bgcolor="#1a1a1a",
    font_color="#d4d0c8",
    legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0),
    margin=dict(l=0, r=0, t=40, b=0),
    height=400,
    yaxis=dict(gridcolor="#2a2a2a", tickprefix="R$ ", tickformat=",.0f"),
    xaxis=dict(gridcolor="#2a2a2a"),
)
st.plotly_chart(fig, use_container_width=True)

# ── NCG (Necessidade de Capital de Giro) ─────────────────────────────────
st.markdown("---")
st.subheader("Necessidade de Capital de Giro (NCG)")

titulos_pagar = cap_f["VALOR"].sum()
previsao_receita = vf["VALOR TOTAL"].sum()
ncg = previsao_receita - titulos_pagar

col1, col2, col3 = st.columns(3)
col1.metric("Títulos a Pagar", fmt(titulos_pagar))
col2.metric("Previsão de Receita", fmt(previsao_receita))
col3.metric("NCG", fmt(ncg), delta=None)
