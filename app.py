"""
app.py — Sistema Financeiro Codi.com
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from style import apply_style, full_sidebar
from engine import (
    load_vendas, load_contas, build_kpis, build_dre,
    filter_vendas, filter_cap, MESES_ORDER
)

st.set_page_config(
    page_title="Codi.com · Financeiro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_style()

@st.cache_data(show_spinner=False)
def get_all_data():
    vendas, impostos, cv, ca, custo = load_vendas()
    cap, car = load_contas()
    return vendas, impostos, cv, ca, custo, cap, car

with st.spinner("Carregando dados..."):
    vendas, impostos, cv, ca, custo, cap, car = get_all_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────
anos_sel  = []
meses_sel = None

def filtros():
    global anos_sel, meses_sel
    anos_disp = sorted(vendas["ANO"].dropna().unique().astype(int))
    anos_sel  = st.multiselect("Ano", anos_disp, default=anos_disp)
    meses_disp = [m for m in MESES_ORDER if m in vendas["MES"].values]
    m = st.multiselect("Mês", meses_disp, default=[])
    meses_sel = m if m else None

full_sidebar(filtros_fn=filtros, current="app.py")

# ── KPIs ──────────────────────────────────────────────────────────────────────
kpis = build_kpis(vendas, impostos, cv, ca, custo, cap, anos=anos_sel, meses=meses_sel)

def fmt(v): return f"R$ {v:,.2f}".replace(",","X").replace(".","," ).replace("X",".")
def pct(v): return f"{v:.1%}"

# Header com logo inline
st.markdown("""
<div style="display:flex;align-items:center;gap:16px;margin-bottom:4px">
  <h1 style="margin:0;border:none;padding:0">Visão Geral</h1>
</div>
""", unsafe_allow_html=True)
periodo = f"{', '.join(map(str, anos_sel))}" + (f" · {', '.join(meses_sel)}" if meses_sel else "")
st.caption(f"📅 Período: {periodo}")

st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

# Linha 1 — KPIs principais
c1,c2,c3,c4 = st.columns(4)
c1.metric("💰 Receita Bruta",          fmt(kpis["receita"]))
c2.metric("📊 Margem Bruta",           fmt(kpis["margem_bruta"]),       pct(kpis["margem_bruta_pct"]))
c3.metric("⚙️ Ebitda Operacional",     fmt(kpis["ebtida_operacional"]), pct(kpis["ebtida_operacional_pct"]))
c4.metric("🏁 Ebitda Final",           fmt(kpis["ebtida_final"]),       pct(kpis["ebtida_final_pct"]))

st.markdown("---")

# Linha 2 — Custos
c5,c6,c7,c8 = st.columns(4)
c5.metric("🏭 CMV",              fmt(kpis["custo"]),      f"{kpis['custo']/kpis['receita']:.1%}" if kpis["receita"] else "—")
c6.metric("🧾 Simples Nacional", fmt(kpis["impostos"]))
c7.metric("🤝 Comissões",        fmt(kpis["comissao"]))
c8.metric("👥 Despesas c/ Folha",fmt(kpis["desp_folha"]))

st.markdown("---")

# ── Gráfico receita x margem ──────────────────────────────────────────────────
st.subheader("Receita × Margem Bruta por mês")

vf    = filter_vendas(vendas, anos_sel, meses_sel)
imp_f = filter_vendas(impostos, anos_sel, meses_sel)
cv_f  = filter_vendas(cv, anos_sel, meses_sel)
ca_f  = filter_vendas(ca, anos_sel, meses_sel)
cu_f  = filter_vendas(custo, anos_sel, meses_sel)
cap_f = filter_cap(cap, anos_sel, meses_sel)

dre = build_dre(vf, imp_f, cv_f, ca_f, cu_f, cap_f, groupby="MES")

if not dre.empty:
    rec_mes = dre[dre["Conta"]=="1-Receita Bruta"][["MES","ValorDRE"]].set_index("MES")
    mg_mes  = dre[dre["Conta"]=="5-Margem Bruta R$"][["MES","ValorDRE"]].set_index("MES")
    ebt_mes = dre[dre["Conta"]=="9.3-Ebtida Final"][["MES","ValorDRE"]].set_index("MES")
    idx = [m for m in MESES_ORDER if m in rec_mes.index]
    rec_mes = rec_mes.reindex(idx); mg_mes = mg_mes.reindex(idx); ebt_mes = ebt_mes.reindex(idx)

    fig = go.Figure()
    fig.add_bar(name="Receita Bruta", x=idx, y=rec_mes["ValorDRE"],
                marker_color="#C9A84C", opacity=0.9)
    fig.add_bar(name="Margem Bruta",  x=idx, y=mg_mes["ValorDRE"],
                marker_color="#2D6A4F", opacity=0.85)
    fig.add_scatter(name="Ebitda Final", x=idx, y=ebt_mes["ValorDRE"],
                    mode="lines+markers",
                    line=dict(color="#E07050", width=2.5),
                    marker=dict(size=8, color="#E07050"))
    fig.update_layout(
        plot_bgcolor="#0d0d0d", paper_bgcolor="#0d0d0d", font_color="#d4d0c8",
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    bgcolor="rgba(0,0,0,0)", font=dict(color="#d4d0c8")),
        margin=dict(l=0,r=0,t=40,b=0), height=360,
        yaxis=dict(gridcolor="#1e1e1e", tickprefix="R$ ", tickformat=",.0f",
                   color="#888"),
        xaxis=dict(gridcolor="#1e1e1e", color="#888"),
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── Resumo DRE ────────────────────────────────────────────────────────────────
st.subheader("Resumo DRE")

linhas = [
    ("1 — Receita Bruta",           kpis["receita"]),
    ("2 — Custo Mercadoria Vendida", kpis["custo"]),
    ("3 — Simples Nacional",         kpis["impostos"]),
    ("4 — Comissão",                 kpis["comissao"]),
    ("5 — Margem Bruta",             kpis["margem_bruta"]),
    ("6 — Despesas Operacionais",    kpis["desp_operacional"]),
    ("7 — Despesas com Folha",       kpis["desp_folha"]),
    ("8 — Ebtida Operacional",       kpis["ebtida_operacional"]),
    ("9.1 — Empréstimos",            kpis["emprestimos"]),
    ("9.2 — Retirada de Sócios",     kpis["retiradas"]),
    ("9.3 — Ebtida Final",           kpis["ebtida_final"]),
]
rec = kpis["receita"] or 1
df_r = pd.DataFrame(linhas, columns=["Conta","Valor (R$)"])
df_r["AV%"] = df_r["Valor (R$)"] / rec

DESTAQUE = {"5 — Margem Bruta","8 — Ebtida Operacional","9.3 — Ebtida Final"}

def style_dre(row):
    if row["Conta"] in DESTAQUE:
        bg = "#0d2a1a" if row["Valor (R$)"] >= 0 else "#2a0d0d"
        clr = "#C9A84C"
        return [f"background:{bg};color:{clr};font-weight:700"] * len(row)
    if row["Conta"] == "1 — Receita Bruta":
        return ["background:#1a1400;color:#C9A84C;font-weight:700"] * len(row)
    return ["background:#0d0d0d;color:#d4d0c8"] * len(row)

st.dataframe(
    df_r.style.apply(style_dre, axis=1)
        .format({"Valor (R$)": lambda v: fmt(v), "AV%": "{:.1%}"}),
    use_container_width=True,
    hide_index=True,
    height=430,
)
