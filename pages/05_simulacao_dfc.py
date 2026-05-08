"""
pages/05_simulacao_dfc.py — Simulação DFC (o que-se)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
sys.path.append(str(__file__).replace("/pages/05_simulacao_dfc.py", ""))
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from style import apply_style, full_sidebar

from engine import (
    load_vendas, load_contas, filter_vendas, filter_cap,
    MESES_ORDER, receita_dre, build_kpis
)

st.set_page_config(page_title="Simulação DFC · Codi.com", layout="wide")
apply_style()



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
    anos_sel = st.multiselect("Ano", anos_disp, default=anos_disp, key="sim_ano")
    meses_disp = [m for m in MESES_ORDER if m in vendas["MES"].values]
    meses_sel = st.multiselect("Mês", meses_disp, default=[], key="sim_mes")
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
def pct(v): return f"{v:.1%}"

vf   = filter_vendas(vendas, anos_sel, meses_sel)
cap_f = filter_cap(cap, anos_sel, meses_sel)

kpis_base = build_kpis(vendas, impostos, cv, ca, custo, cap, anos=anos_sel, meses=meses_sel)

st.title("Simulação DFC")
st.caption("Simule o impacto de mudanças no caixa — recebimentos, pagamentos e empréstimos")

# ── Saldo base ────────────────────────────────────────────────────────────
receita_base = kpis_base["receita"]
pagar_base   = cap_f["VALOR"].sum()
receber_base = car["VALOR _x000D_\nRECEBIDO"].sum() if "VALOR _x000D_\nRECEBIDO" in car.columns else 0

# Tentar coluna com nome limpo
valor_rec_col = [c for c in car.columns if "RECEBIDO" in c.upper()]
if valor_rec_col:
    receber_base = car[valor_rec_col[0]].sum()

saldo_base = receber_base - pagar_base

st.markdown("### Posição atual")
c1, c2, c3 = st.columns(3)
c1.metric("Títulos a Receber", fmt(receber_base))
c2.metric("Títulos a Pagar",   fmt(pagar_base))
c3.metric("Saldo Líquido",     fmt(saldo_base))

st.markdown("---")
st.markdown("### Simulação — O que acontece se...")

# ── Painel de simulação ────────────────────────────────────────────────────
col_sim, col_res = st.columns([1, 1])

with col_sim:
    st.markdown("#### Ajustes")

    antecipa_rec = st.number_input(
        "Antecipação de recebimentos (R$)",
        min_value=0.0, max_value=float(receber_base), value=0.0, step=1000.0,
        help="Valor que será recebido antecipadamente",
    )
    desconto_rec = st.slider("Desconto concedido para antecipação (%)", 0.0, 10.0, 0.0, 0.1)

    st.markdown("---")
    postergacao_pag = st.number_input(
        "Postergação de pagamentos (R$)",
        min_value=0.0, max_value=float(pagar_base), value=0.0, step=1000.0,
        help="Valor de contas a pagar que será postergado",
    )
    juros_posterg = st.slider("Juros por postergação (%)", 0.0, 5.0, 0.0, 0.1)

    st.markdown("---")
    novo_emprestimo = st.number_input(
        "Novo empréstimo (R$)", min_value=0.0, value=0.0, step=5000.0
    )
    taxa_emprestimo = st.slider("Taxa mensal do empréstimo (%)", 0.5, 5.0, 1.5, 0.1)
    prazo_meses     = st.slider("Prazo (meses)", 6, 60, 12)

with col_res:
    st.markdown("#### Resultado da Simulação")

    rec_antecipado  = antecipa_rec * (1 - desconto_rec / 100)
    custo_desconto  = antecipa_rec * (desconto_rec / 100)
    custo_juros_post = postergacao_pag * (juros_posterg / 100)

    # Parcela do empréstimo (Price)
    if novo_emprestimo > 0 and taxa_emprestimo > 0:
        i_m = taxa_emprestimo / 100
        parcela = novo_emprestimo * (i_m * (1 + i_m) ** prazo_meses) / ((1 + i_m) ** prazo_meses - 1)
        total_emprestimo = parcela * prazo_meses
        juros_total_emp  = total_emprestimo - novo_emprestimo
    else:
        parcela = 0.0
        total_emprestimo = 0.0
        juros_total_emp  = 0.0

    saldo_sim = (
        saldo_base
        + rec_antecipado
        - custo_desconto
        - custo_juros_post
        + novo_emprestimo
    )

    delta_saldo = saldo_sim - saldo_base

    st.metric("Recebimento líquido c/ antecipação", fmt(rec_antecipado),
              f"-{fmt(custo_desconto)} em descontos" if custo_desconto > 0 else None)
    st.metric("Custo de postergação", fmt(custo_juros_post))
    if novo_emprestimo > 0:
        st.metric("Parcela mensal estimada", fmt(parcela),
                  f"Total juros: {fmt(juros_total_emp)}")
    st.markdown("---")
    st.metric(
        "Saldo simulado",
        fmt(saldo_sim),
        f"{'+' if delta_saldo >= 0 else ''}{fmt(delta_saldo)} vs atual",
        delta_color="normal",
    )

    if novo_emprestimo > 0:
        st.info(f"💡 Empréstimo de {fmt(novo_emprestimo)} em {prazo_meses}x de {fmt(parcela)} = total {fmt(total_emprestimo)}")

st.markdown("---")

# ── Projeção diária DFC ────────────────────────────────────────────────────
st.subheader("Projeção de saldo diário — mês corrente")

meses_disp2 = [m for m in MESES_ORDER if m in cap_f["MES"].values]
if meses_disp2:
    mes_sel_diario = st.selectbox("Mês para projeção diária", meses_disp2, index=len(meses_disp2)-1)

    cap_mes = cap_f[cap_f["MES"] == mes_sel_diario].copy()
    cap_mes["DT. VENC."] = pd.to_datetime(cap_mes["DT. VENC."], errors="coerce")

    vend_mes = vf[vf["MES"] == mes_sel_diario].copy() if mes_sel_diario in vf["MES"].values else pd.DataFrame()

    # Distribuir receita uniformemente pelos dias úteis
    if not vend_mes.empty:
        rec_total_mes = vend_mes["VALOR TOTAL"].sum()
        datas_vend = pd.date_range(
            vend_mes["DATA"].min(), vend_mes["DATA"].max(), freq="B"
        )
        rec_diaria = rec_total_mes / len(datas_vend) if len(datas_vend) > 0 else 0
    else:
        rec_diaria = 0
        datas_vend = pd.DatetimeIndex([])

    if not cap_mes.empty and cap_mes["DT. VENC."].notna().any():
        pag_diario = cap_mes.groupby("DT. VENC.")["VALOR"].sum()

        datas_all = pd.date_range(
            cap_mes["DT. VENC."].min(),
            cap_mes["DT. VENC."].max(),
            freq="D"
        )

        saldo_acum = []
        saldo = saldo_base * 0.1  # saldo inicial estimado
        for d in datas_all:
            entrada = rec_diaria if d in datas_vend else 0
            saida   = pag_diario.get(d, 0)
            saldo  += entrada - saida
            saldo_acum.append({"Data": d, "Saldo": saldo, "Entrada": entrada, "Saída": saida})

        df_diario = pd.DataFrame(saldo_acum)

        fig_diario = go.Figure()
        fig_diario.add_scatter(
            name="Saldo acumulado",
            x=df_diario["Data"], y=df_diario["Saldo"],
            fill="tozeroy",
            line=dict(color="#C9A84C", width=2),
            fillcolor="rgba(201,168,76,0.15)",
        )
        fig_diario.add_bar(
            name="Saídas", x=df_diario["Data"], y=-df_diario["Saída"],
            marker_color="#E07050", opacity=0.7,
        )
        fig_diario.add_bar(
            name="Entradas", x=df_diario["Data"], y=df_diario["Entrada"],
            marker_color="#4CAF9B", opacity=0.7,
        )
        fig_diario.add_hline(y=0, line_dash="dash", line_color="#555")

        fig_diario.update_layout(
            barmode="relative",
            plot_bgcolor="#1a1a1a", paper_bgcolor="#1a1a1a",
            font_color="#d4d0c8",
            legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0),
            margin=dict(l=0, r=0, t=40, b=0),
            height=360,
            yaxis=dict(gridcolor="#2a2a2a", tickprefix="R$ ", tickformat=",.0f"),
            xaxis=dict(gridcolor="#2a2a2a"),
        )
        st.plotly_chart(fig_diario, use_container_width=True)
    else:
        st.info("Sem vencimentos de contas a pagar para o mês selecionado.")
