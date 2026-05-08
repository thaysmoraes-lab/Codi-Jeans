"""
pages/02_dre.py — DRE com ValorDRE + Análise Vertical %
Replica fielmente o visual do Power BI
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
sys.path.append(str(__file__).replace("/pages/02_dre.py", ""))
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from style import apply_style, full_sidebar

from engine import (
    load_vendas, load_contas, build_dre, build_dre_pivot,
    filter_vendas, filter_cap, MESES_ORDER, DRE_LINHAS
)

st.set_page_config(page_title="DRE · Codi.com", layout="wide")
apply_style()



@st.cache_data(show_spinner=False)
def get_all():
    v, i, cv, ca, cu = load_vendas()
    cap, car = load_contas()
    return v, i, cv, ca, cu, cap, car

with st.spinner("Carregando..."):
    vendas, impostos, cv, ca, custo, cap, car = get_all()

# Sidebar filtros
with st.sidebar:
    st.markdown("### 🎛️ Filtros")
    anos_disp = sorted(vendas["ANO"].dropna().unique().astype(int))
    anos_sel = st.multiselect("Ano", anos_disp, default=anos_disp, key="dre_ano")
    meses_disp = [m for m in MESES_ORDER if m in vendas["MES"].values]
    meses_sel = st.multiselect("Mês", meses_disp, default=[], key="dre_mes")
    if not meses_sel:
        meses_sel = None

    st.markdown("---")
    st.page_link("app.py", label="🏠 Visão Geral")
    st.page_link("pages/01_fluxo_caixa.py", label="📊 Fluxo de Caixa")
    st.page_link("pages/02_dre.py", label="📋 DRE")
    st.page_link("pages/03_projecao_dre.py", label="🔮 Projeção DRE")
    st.page_link("pages/04_despesas_fornecedor.py", label="🏭 Despesas por Fornecedor")
    st.page_link("pages/05_simulacao_dfc.py", label="⚡ Simulação DFC")

# Filtrar
vf   = filter_vendas(vendas, anos_sel, meses_sel)
imp_f = filter_vendas(impostos, anos_sel, meses_sel)
cv_f  = filter_vendas(cv, anos_sel, meses_sel)
ca_f  = filter_vendas(ca, anos_sel, meses_sel)
cu_f  = filter_vendas(custo, anos_sel, meses_sel)
cap_f = filter_cap(cap, anos_sel, meses_sel)

st.title("DRE — Demonstrativo de Resultados")

# DRE pivotada por mês
dre_mes = build_dre(vf, imp_f, cv_f, ca_f, cu_f, cap_f, groupby="MES")

def fmt(v): return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def pct(v): return f"{v:.1%}"

if dre_mes.empty:
    st.warning("Sem dados para o período selecionado.")
    st.stop()

# ── Pivot ValorDRE ────────────────────────────────────────────────────────────
pivot = dre_mes.pivot_table(
    index="Conta", columns="MES", values="ValorDRE", aggfunc="sum"
).reindex(DRE_LINHAS)
pivot_av = dre_mes.pivot_table(
    index="Conta", columns="MES", values="AV%", aggfunc="mean"
).reindex(DRE_LINHAS)

meses_present = [m for m in MESES_ORDER if m in pivot.columns]
pivot    = pivot[meses_present]
pivot_av = pivot_av[meses_present]
pivot["Total"] = pivot.sum(axis=1)

rec_total = pivot.loc["1-Receita Bruta", "Total"] or 1
pivot_av["Total"] = pivot["Total"] / rec_total

# ── Tabela interleaved ValorDRE + AV% ─────────────────────────────────────────
st.subheader("DRE por mês")

rows_display = []
for conta in DRE_LINHAS:
    row_val = {"Conta": conta, "Tipo": "R$"}
    row_av  = {"Conta": conta, "Tipo": "AV%"}
    for col in meses_present + ["Total"]:
        v = pivot.loc[conta, col] if conta in pivot.index else 0
        a = pivot_av.loc[conta, col] if conta in pivot_av.index else 0
        row_val[col.capitalize()] = fmt(v)
        row_av[col.capitalize()]  = pct(a)
    rows_display.append(row_val)
    rows_display.append(row_av)

df_display = pd.DataFrame(rows_display)

def highlight_dre(row):
    conta = row["Conta"]
    tipo  = row["Tipo"]
    destaque = ["5-Margem Bruta R$", "8-Ebtida Operacional", "9.3-Ebtida Final"]
    if conta in destaque and tipo == "R$":
        return ["background-color: #1e3a2a; font-weight: 600"] * len(row)
    if tipo == "AV%":
        return ["color: #888; font-size: 12px"] * len(row)
    return [""] * len(row)

st.dataframe(
    df_display.style.apply(highlight_dre, axis=1),
    use_container_width=True,
    hide_index=True,
    height=min(60 * len(DRE_LINHAS) * 2, 700),
)

st.markdown("---")

# ── Gráfico Cascata (waterfall) da DRE Total ──────────────────────────────────
st.subheader("Cascata DRE — Período total")

contas_waterfall = [
    ("Receita Bruta",         pivot.loc["1-Receita Bruta", "Total"],       "absolute"),
    ("(-) CMV",               -pivot.loc["2-Custo Mercadoria Vendida", "Total"], "relative"),
    ("(-) Simples",           -pivot.loc["3-Simples Nacional", "Total"],   "relative"),
    ("(-) Comissão",          -pivot.loc["4-Comissão", "Total"],           "relative"),
    ("= Margem Bruta",        pivot.loc["5-Margem Bruta R$", "Total"],     "total"),
    ("(-) Desp. Operac.",     -pivot.loc["6-Despesas Operacionais", "Total"], "relative"),
    ("(-) Folha",             -pivot.loc["7-Despesas com Folha", "Total"], "relative"),
    ("= Ebitda Oper.",        pivot.loc["8-Ebtida Operacional", "Total"],  "total"),
    ("(-) Empréstimos",       -pivot.loc["9.1-Empréstimos", "Total"],      "relative"),
    ("(-) Retiradas",         -pivot.loc["9.2-Retirada de sócios", "Total"], "relative"),
    ("= Ebitda Final",        pivot.loc["9.3-Ebtida Final", "Total"],      "total"),
]

labels = [c[0] for c in contas_waterfall]
values = [c[1] for c in contas_waterfall]
measures = [c[2] for c in contas_waterfall]

fig_wf = go.Figure(go.Waterfall(
    name="DRE",
    orientation="v",
    measure=measures,
    x=labels,
    y=values,
    text=[fmt(v) for v in values],
    textposition="outside",
    connector=dict(line=dict(color="#444", width=0.8)),
    increasing=dict(marker_color="#4CAF9B"),
    decreasing=dict(marker_color="#E07050"),
    totals=dict(marker_color="#C9A84C"),
))
fig_wf.update_layout(
    plot_bgcolor="#1a1a1a",
    paper_bgcolor="#1a1a1a",
    font_color="#d4d0c8",
    margin=dict(l=0, r=0, t=20, b=0),
    height=420,
    yaxis=dict(gridcolor="#2a2a2a", tickprefix="R$ ", tickformat=",.0f"),
    xaxis=dict(gridcolor="#2a2a2a"),
    showlegend=False,
)
st.plotly_chart(fig_wf, use_container_width=True)

# ── Análise Vertical — gráfico de barras horizontais ─────────────────────────
st.subheader("Análise Vertical % — Participação sobre Receita Bruta")

contas_av = [c for c in DRE_LINHAS if c != "1-Receita Bruta"]
av_vals = [pivot_av.loc[c, "Total"] if c in pivot_av.index else 0 for c in contas_av]

cores = ["#E07050" if v < 0 else "#4CAF9B" for v in av_vals]
cores_map = {
    "5-Margem Bruta R$": "#C9A84C",
    "8-Ebtida Operacional": "#C9A84C",
    "9.3-Ebtida Final": "#C9A84C",
}
cores = [cores_map.get(c, cor) for c, cor in zip(contas_av, cores)]

fig_av = go.Figure(go.Bar(
    x=av_vals,
    y=contas_av,
    orientation="h",
    marker_color=cores,
    text=[pct(v) for v in av_vals],
    textposition="outside",
))
fig_av.update_layout(
    plot_bgcolor="#1a1a1a",
    paper_bgcolor="#1a1a1a",
    font_color="#d4d0c8",
    margin=dict(l=0, r=60, t=10, b=0),
    height=380,
    xaxis=dict(gridcolor="#2a2a2a", tickformat=".0%"),
    yaxis=dict(gridcolor="#2a2a2a"),
    showlegend=False,
)
st.plotly_chart(fig_av, use_container_width=True)
