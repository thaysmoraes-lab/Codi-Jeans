"""
pages/03_projecao_dre.py — Projeção DRE com cenários
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
sys.path.append(str(__file__).replace("/pages/03_projecao_dre.py", ""))

from engine import (
    load_vendas, load_contas, build_dre, filter_vendas, filter_cap,
    MESES_ORDER, DRE_LINHAS, receita_dre, custo_dre, custo_impostos,
    comissao, margem_bruta, despesas_operacionais, despesas_folha,
    ebtida_operacional, emprestimos, retiradas_socios, ebtida_final
)

st.set_page_config(page_title="Projeção DRE · Codi.com", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
[data-testid="stSidebar"] { background: #111111 !important; border-right: 1px solid #2a2a2a; }
[data-testid="stSidebar"] * { color: #d4d0c8 !important; }
h1 { color: #C9A84C !important; font-weight: 600 !important; }
h2, h3 { color: #f0ede8 !important; font-weight: 500 !important; }
hr { border-color: #2a2a2a; }
[data-testid="metric-container"] { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 10px; padding: 16px 20px; }
[data-testid="metric-container"] label { color: #888 !important; font-size: 11px !important; text-transform: uppercase; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #f0ede8 !important; font-size: 22px !important; font-weight: 600; }
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
    ano_base = st.selectbox("Ano base (histórico)", anos_disp, index=len(anos_disp)-1, key="proj_ano")

    st.markdown("---")
    st.markdown("### ⚙️ Cenário de projeção")
    crescimento_receita = st.slider("Crescimento de Receita (%)", -50, 100, 10, key="proj_crec")
    reducao_custo       = st.slider("Redução de Custo (%)",        -50,  50,  0, key="proj_rcusto")
    reducao_desp        = st.slider("Redução Despesas Oper. (%)",  -50,  50,  0, key="proj_rdesp")
    reducao_folha       = st.slider("Redução Folha (%)",           -50,  50,  0, key="proj_rfolha")

    st.markdown("---")
    st.page_link("app.py", label="🏠 Visão Geral")
    st.page_link("pages/01_fluxo_caixa.py", label="📊 Fluxo de Caixa")
    st.page_link("pages/02_dre.py", label="📋 DRE")
    st.page_link("pages/03_projecao_dre.py", label="🔮 Projeção DRE")
    st.page_link("pages/04_despesas_fornecedor.py", label="🏭 Despesas por Fornecedor")
    st.page_link("pages/05_simulacao_dfc.py", label="⚡ Simulação DFC")

def fmt(v): return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def pct(v): return f"{v:.1%}"
def delta_pct(novo, base): return (novo - base) / base if base else 0

# ── Dados históricos do ano base ──────────────────────────────────────────
vf   = filter_vendas(vendas, [ano_base])
imp_f = filter_vendas(impostos, [ano_base])
cv_f  = filter_vendas(cv, [ano_base])
ca_f  = filter_vendas(ca, [ano_base])
cu_f  = filter_vendas(custo, [ano_base])
cap_f = filter_cap(cap, [ano_base])

rec_hist  = receita_dre(vf)
cus_hist  = custo_dre(cu_f)
imp_hist  = custo_impostos(imp_f)
com_hist  = comissao(cv_f, ca_f)
mg_hist   = rec_hist - cus_hist - imp_hist - com_hist
dop_hist  = despesas_operacionais(cap_f)
dfol_hist = despesas_folha(cap_f)
eop_hist  = mg_hist - dfol_hist - dop_hist
emp_hist  = emprestimos(cap_f)
ret_hist  = retiradas_socios(cap_f)
efin_hist = eop_hist - ret_hist - emp_hist

# ── Projeção ─────────────────────────────────────────────────────────────
fator_rec  = 1 + crescimento_receita / 100
fator_cus  = 1 - reducao_custo / 100
fator_desp = 1 - reducao_desp / 100
fator_folh = 1 - reducao_folha / 100

rec_proj  = rec_hist  * fator_rec
cus_proj  = cus_hist  * fator_cus
imp_proj  = imp_hist  * fator_rec   # impostos seguem receita
com_proj  = com_hist  * fator_rec   # comissões seguem receita
mg_proj   = rec_proj  - cus_proj - imp_proj - com_proj
dop_proj  = dop_hist  * fator_desp
dfol_proj = dfol_hist * fator_folh
eop_proj  = mg_proj   - dfol_proj - dop_proj
emp_proj  = emp_hist
ret_proj  = ret_hist
efin_proj = eop_proj  - ret_proj - emp_proj

st.title("Projeção DRE")
st.caption(f"Histórico base: {ano_base} | Cenário projetado com crescimento de receita {crescimento_receita:+d}%")

# ── KPIs comparativos ─────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Receita Projetada", fmt(rec_proj), f"{delta_pct(rec_proj, rec_hist):+.1%} vs histórico")
col2.metric("Margem Bruta Proj.", fmt(mg_proj),  f"{delta_pct(mg_proj, mg_hist):+.1%}")
col3.metric("Ebitda Oper. Proj.", fmt(eop_proj), f"{delta_pct(eop_proj, eop_hist):+.1%}")
col4.metric("Ebitda Final Proj.", fmt(efin_proj), f"{delta_pct(efin_proj, efin_hist):+.1%}")

st.markdown("---")

# ── Tabela comparativa Histórico vs Projeção ──────────────────────────────
st.subheader("Histórico vs Projeção")

data_comp = {
    "Conta": DRE_LINHAS,
    f"Histórico {ano_base}": [
        rec_hist, cus_hist, imp_hist, com_hist, mg_hist,
        dop_hist, dfol_hist, eop_hist, emp_hist, ret_hist, efin_hist
    ],
    "Projeção": [
        rec_proj, cus_proj, imp_proj, com_proj, mg_proj,
        dop_proj, dfol_proj, eop_proj, emp_proj, ret_proj, efin_proj
    ],
}

df_comp = pd.DataFrame(data_comp)
df_comp["Δ Valor"] = df_comp["Projeção"] - df_comp[f"Histórico {ano_base}"]
df_comp["Δ %"]     = df_comp.apply(
    lambda r: r["Δ Valor"] / r[f"Histórico {ano_base}"] if r[f"Histórico {ano_base}"] != 0 else 0, axis=1
)
df_comp["AV% Proj."] = df_comp["Projeção"] / (rec_proj or 1)

def highlight_comp(row):
    destaque = ["5-Margem Bruta R$", "8-Ebtida Operacional", "9.3-Ebtida Final"]
    if row["Conta"] in destaque:
        return ["background-color: #1e3a2a; font-weight: 600"] * len(row)
    return [""] * len(row)

df_styled = (
    df_comp.style
    .apply(highlight_comp, axis=1)
    .format({
        f"Histórico {ano_base}": lambda v: fmt(v),
        "Projeção":  lambda v: fmt(v),
        "Δ Valor":   lambda v: fmt(v),
        "Δ %":       "{:.1%}",
        "AV% Proj.": "{:.1%}",
    })
)
st.dataframe(df_styled, use_container_width=True, hide_index=True, height=420)

st.markdown("---")

# ── Gráfico comparativo barras ────────────────────────────────────────────
st.subheader("Visualização comparativa")

contas_graf = ["1-Receita Bruta", "5-Margem Bruta R$", "8-Ebtida Operacional", "9.3-Ebtida Final"]
hist_vals = [rec_hist, mg_hist, eop_hist, efin_hist]
proj_vals = [rec_proj, mg_proj, eop_proj, efin_proj]
labels_g  = ["Receita Bruta", "Margem Bruta", "Ebitda Oper.", "Ebitda Final"]

fig = go.Figure()
fig.add_bar(name=f"Histórico {ano_base}", x=labels_g, y=hist_vals, marker_color="#555", width=0.35, offset=-0.18)
fig.add_bar(name="Projeção",             x=labels_g, y=proj_vals, marker_color="#C9A84C", width=0.35, offset=0.18)

fig.update_layout(
    plot_bgcolor="#1a1a1a", paper_bgcolor="#1a1a1a",
    font_color="#d4d0c8",
    barmode="overlay",
    legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0),
    margin=dict(l=0, r=0, t=40, b=0),
    height=360,
    yaxis=dict(gridcolor="#2a2a2a", tickprefix="R$ ", tickformat=",.0f"),
)
st.plotly_chart(fig, use_container_width=True)

# ── Projeção mensal (distribuição uniforme) ────────────────────────────────
st.subheader("Projeção mensal estimada")

dre_mes_hist = build_dre(vf, imp_f, cv_f, ca_f, cu_f, cap_f, groupby="MES")
if not dre_mes_hist.empty:
    meses_hist = dre_mes_hist["MES"].unique()
    n = len(meses_hist)
    if n > 0:
        rows_proj = []
        for m in MESES_ORDER:
            if m not in meses_hist:
                continue
            hist_m = dre_mes_hist[dre_mes_hist["MES"] == m]

            def get_val(conta):
                r = hist_m[hist_m["Conta"] == conta]["ValorDRE"]
                return float(r.iloc[0]) if len(r) > 0 else 0

            rec_m  = get_val("1-Receita Bruta")  * fator_rec
            cus_m  = get_val("2-Custo Mercadoria Vendida") * fator_cus
            imp_m  = get_val("3-Simples Nacional") * fator_rec
            com_m  = get_val("4-Comissão")         * fator_rec
            mg_m   = rec_m - cus_m - imp_m - com_m
            dop_m  = get_val("6-Despesas Operacionais") * fator_desp
            dfol_m = get_val("7-Despesas com Folha")    * fator_folh
            eop_m  = mg_m - dfol_m - dop_m
            emp_m  = get_val("9.1-Empréstimos")
            ret_m  = get_val("9.2-Retirada de sócios")
            efin_m = eop_m - ret_m - emp_m

            rows_proj.append({
                "Mês": m.capitalize(),
                "Receita": fmt(rec_m),
                "Margem Bruta": fmt(mg_m),
                "Ebitda Oper.": fmt(eop_m),
                "Ebitda Final": fmt(efin_m),
                "AV% Marg.": pct(mg_m / rec_m if rec_m else 0),
                "AV% Ebitda Final": pct(efin_m / rec_m if rec_m else 0),
            })

        st.dataframe(pd.DataFrame(rows_proj), use_container_width=True, hide_index=True)
