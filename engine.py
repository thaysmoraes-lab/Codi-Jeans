"""
engine.py — Motor de cálculo financeiro Codi.com
Tradução das fórmulas DAX do Power BI para Python/pandas
"""

import pandas as pd
import numpy as np
from pathlib import Path
import streamlit as st

DATA_DIR = Path(__file__).parent / "data"

MESES_ORDER = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
]

DESPESAS_OPERACIONAIS = {
    "Combustíveis", "Manutenção de Máquinas e Peças",
    "Manutenção de Veiculos e Estacionamento",
    "Compra de Computadores e Eletrônicos", "Aluguéis e Condomínios",
    "Web Site e Sistema ERP", "Ipva", "Patrocínio",
    "Material de Copa e Cozinha", "Consulta de Crédito Cliente",
    "Frete e Transporte de Mercadorias", "Segurança e Monitoramento",
    "Seguros", "Telefonia Fixa e Internet", "Compra de Veículos",
    "Material de Limpeza e Higiene", "Água", "Material de Escritório",
    "Despesas com Documentos e Xerox",
    "Honorários Contábeis (Contabilidade)",
    "Tarifas e Custos de Op. Bancárias", "Telefonia Móvel",
    "Viagens e estadas", "Assessoria Técnica Profissional",
    "Outros Tributos", "Multas", "Advogados - Honorários",
    "Publicidade", "Energia Elétrica", "Multas e Juros por Atraso",
}

DESPESAS_FOLHA = {
    "Alimentação", "Exame Adminissional/Demissional",
    "Vale Transporte", "Salário e Ordenados",
    "Despesa com Sindicatos", "Vales e Adiantamentos",
    "Premiações e Abonos",
}

DRE_LINHAS = [
    "1-Receita Bruta",
    "2-Custo Mercadoria Vendida",
    "3-Simples Nacional",
    "4-Comissão",
    "5-Margem Bruta R$",
    "6-Despesas Operacionais",
    "7-Despesas com Folha",
    "8-Ebtida Operacional",
    "9.1-Empréstimos",
    "9.2-Retirada de sócios",
    "9.3-Ebtida Final",
]


@st.cache_data(show_spinner=False)
def load_vendas():
    xls = pd.ExcelFile(DATA_DIR / "VENDAS_2025.xlsx")
    vendas = pd.read_excel(xls, "VENDAS")
    impostos = pd.read_excel(xls, "IMPOSTOS CALCULADO")
    comm_vend = pd.read_excel(xls, "COMISSÃO VENDEDORES")
    comm_asses = pd.read_excel(xls, "COMISSÃO ASSESSORES")
    custo = pd.read_excel(xls, "CUSTO")

    for df in [vendas, impostos, comm_vend, comm_asses, custo]:
        df["DATA"] = pd.to_datetime(df["DATA"], errors="coerce")
        df["ANO"] = df["DATA"].dt.year
        df["MES_NUM"] = df["DATA"].dt.month
        df["MES"] = df["DATA"].dt.month.map(
            {i + 1: m for i, m in enumerate(MESES_ORDER)}
        )

    return vendas, impostos, comm_vend, comm_asses, custo


@st.cache_data(show_spinner=False)
def load_contas():
    xls = pd.ExcelFile(DATA_DIR / "DFC_JUL_A_OUT-25.xlsx")
    cap = pd.read_excel(xls, "CONTAS A PAGAR")
    car = pd.read_excel(xls, "CONTAS A RECEBER")

    cap["DT. BAIXA"] = pd.to_datetime(cap["DT. BAIXA"], errors="coerce")
    cap["ANO"] = cap["DT. BAIXA"].dt.year
    cap["MES_NUM"] = cap["DT. BAIXA"].dt.month
    cap["MES"] = cap["DT. BAIXA"].dt.month.map(
        {i + 1: m for i, m in enumerate(MESES_ORDER)}
    )

    car["DT. BAIXA"] = pd.to_datetime(car["DT. BAIXA"], errors="coerce")
    car["ANO"] = car["DT. BAIXA"].dt.year
    car["MES_NUM"] = car["DT. BAIXA"].dt.month
    car["MES"] = car["DT. BAIXA"].dt.month.map(
        {i + 1: m for i, m in enumerate(MESES_ORDER)}
    )

    return cap, car


def filter_vendas(df, anos=None, meses=None):
    d = df.copy()
    if anos:
        d = d[d["ANO"].isin(anos)]
    if meses:
        d = d[d["MES"].isin(meses)]
    return d


def filter_cap(df, anos=None, meses=None):
    d = df.copy()
    if anos:
        d = d[d["ANO"].isin(anos)]
    if meses:
        d = d[d["MES"].isin(meses)]
    return d


# ── Medidas DRE ──────────────────────────────────────────────────────────────

def receita_dre(vendas):
    return vendas["VALOR TOTAL"].sum()


def custo_dre(custo):
    return custo["CUSTO1"].sum()


def custo_impostos(impostos):
    return impostos["IMPOSTOS"].sum()


def comissao(comm_vend, comm_asses):
    return comm_vend["COMISSAO"].sum() + comm_asses["COMISSAO"].sum()


def margem_bruta(vendas, custo, impostos, cv, ca):
    return (
        receita_dre(vendas)
        - custo_dre(custo)
        - custo_impostos(impostos)
        - comissao(cv, ca)
    )


def despesas_operacionais(cap):
    return cap[cap["PLANO DE CONTAS"].isin(DESPESAS_OPERACIONAIS)]["VALOR"].sum()


def despesas_folha(cap):
    return cap[cap["PLANO DE CONTAS"].isin(DESPESAS_FOLHA)]["VALOR"].sum()


def ebtida_operacional(vendas, custo, impostos, cv, ca, cap):
    return (
        margem_bruta(vendas, custo, impostos, cv, ca)
        - despesas_folha(cap)
        - despesas_operacionais(cap)
    )


def emprestimos(cap):
    return cap[cap["PLANO DE CONTAS"] == "Empréstimos"]["VALOR"].sum()


def retiradas_socios(cap):
    return cap[cap["PLANO DE CONTAS"] == "Retiradas de Sócios"]["VALOR"].sum()


def ebtida_final(vendas, custo, impostos, cv, ca, cap):
    return (
        ebtida_operacional(vendas, custo, impostos, cv, ca, cap)
        - retiradas_socios(cap)
        - emprestimos(cap)
    )


# ── Tabela DRE completa ───────────────────────────────────────────────────────

def build_dre(vendas, impostos, cv, ca, custo, cap, groupby="MES"):
    """Retorna DataFrame DRE com todas as linhas, agrupado por mês ou ano."""
    dims = vendas[[groupby, "ANO", "MES_NUM"]].drop_duplicates()

    rows = []
    periods = (
        vendas.groupby([groupby, "MES_NUM"])
        .size()
        .reset_index()[[groupby, "MES_NUM"]]
        .drop_duplicates()
        .sort_values("MES_NUM")
    ) if groupby == "MES" else (
        vendas[[groupby]].drop_duplicates().sort_values(groupby)
    )

    for _, row in periods.iterrows():
        p = row[groupby]
        vf = vendas[vendas[groupby] == p]
        imp_f = impostos[impostos[groupby] == p]
        cv_f = cv[cv[groupby] == p]
        ca_f = ca[ca[groupby] == p]
        cu_f = custo[custo[groupby] == p]
        cap_f = cap[cap[groupby] == p]

        rec = receita_dre(vf)
        cus = custo_dre(cu_f)
        imp = custo_impostos(imp_f)
        com = comissao(cv_f, ca_f)
        mg = rec - cus - imp - com
        dop = despesas_operacionais(cap_f)
        dfol = despesas_folha(cap_f)
        eop = mg - dfol - dop
        emp = emprestimos(cap_f)
        ret = retiradas_socios(cap_f)
        efin = eop - ret - emp

        base = rec if rec != 0 else 1
        for conta, val in [
            ("1-Receita Bruta", rec),
            ("2-Custo Mercadoria Vendida", cus),
            ("3-Simples Nacional", imp),
            ("4-Comissão", com),
            ("5-Margem Bruta R$", mg),
            ("6-Despesas Operacionais", dop),
            ("7-Despesas com Folha", dfol),
            ("8-Ebtida Operacional", eop),
            ("9.1-Empréstimos", emp),
            ("9.2-Retirada de sócios", ret),
            ("9.3-Ebtida Final", efin),
        ]:
            rows.append({
                "Conta": conta,
                groupby: p,
                "ValorDRE": val,
                "AV%": val / base,
            })

    df_dre = pd.DataFrame(rows)
    return df_dre


# ── Tabela DRE pivotada (meses nas colunas) ──────────────────────────────────

def build_dre_pivot(vendas, impostos, cv, ca, custo, cap, anos=None, meses=None):
    vf = filter_vendas(vendas, anos, meses)
    imp_f = filter_vendas(impostos, anos, meses)
    cv_f = filter_vendas(cv, anos, meses)
    ca_f = filter_vendas(ca, anos, meses)
    cu_f = filter_vendas(custo, anos, meses)
    cap_f = filter_cap(cap, anos, meses)

    dre = build_dre(vf, imp_f, cv_f, ca_f, cu_f, cap_f, groupby="MES")
    if dre.empty:
        return pd.DataFrame()

    pivot = dre.pivot_table(
        index="Conta", columns="MES", values="ValorDRE", aggfunc="sum"
    ).reindex(DRE_LINHAS)

    meses_present = [m for m in MESES_ORDER if m in pivot.columns]
    pivot = pivot[meses_present]
    pivot["Total"] = pivot.sum(axis=1)

    rec_row = pivot.loc["1-Receita Bruta"]
    av_cols = {}
    for col in pivot.columns:
        base = rec_row[col] if rec_row[col] != 0 else 1
        av_cols[col] = pivot[col] / base

    return pivot, pd.DataFrame(av_cols)


# ── Fluxo de Caixa mensal ────────────────────────────────────────────────────

def build_fluxo_caixa(vendas, cap, car, anos=None, meses=None):
    vf = filter_vendas(vendas, anos, meses)
    cap_f = filter_cap(cap, anos, meses)
    car_f = filter_cap(car, anos, meses)

    receita_mes = (
        vf.groupby(["ANO", "MES", "MES_NUM"])["VALOR TOTAL"]
        .sum()
        .reset_index()
        .rename(columns={"VALOR TOTAL": "Valor"})
    )
    receita_mes["Classificação"] = "Receita"
    receita_mes["Conta"] = "Receita"

    custo_mes = (
        cap_f[~cap_f["PLANO DE CONTAS"].isin(
            DESPESAS_OPERACIONAIS | DESPESAS_FOLHA |
            {"Empréstimos", "Retiradas de Sócios"}
        )]
        .groupby(["ANO", "MES", "MES_NUM"])["VALOR"]
        .sum()
        .reset_index()
        .rename(columns={"VALOR": "Valor"})
    )
    custo_mes["Classificação"] = "Custo"
    custo_mes["Conta"] = "Custo"

    desp_mes = (
        cap_f[cap_f["PLANO DE CONTAS"].isin(
            DESPESAS_OPERACIONAIS | DESPESAS_FOLHA |
            {"Empréstimos", "Retiradas de Sócios"}
        )]
        .groupby(["ANO", "MES", "MES_NUM"])["VALOR"]
        .sum()
        .reset_index()
        .rename(columns={"VALOR": "Valor"})
    )
    desp_mes["Classificação"] = "Despesa"
    desp_mes["Conta"] = "Despesa"

    df = pd.concat([receita_mes, custo_mes, desp_mes], ignore_index=True)
    return df


# ── Despesas por fornecedor ──────────────────────────────────────────────────

def build_despesas_fornecedor(cap, anos=None, meses=None):
    cap_f = filter_cap(cap, anos, meses)
    df = (
        cap_f.groupby(["PESSOA", "PLANO DE CONTAS", "MES", "MES_NUM"])["VALOR"]
        .sum()
        .reset_index()
    )
    return df


# ── KPIs resumo ─────────────────────────────────────────────────────────────

def build_kpis(vendas, impostos, cv, ca, custo, cap, anos=None, meses=None):
    vf = filter_vendas(vendas, anos, meses)
    imp_f = filter_vendas(impostos, anos, meses)
    cv_f = filter_vendas(cv, anos, meses)
    ca_f = filter_vendas(ca, anos, meses)
    cu_f = filter_vendas(custo, anos, meses)
    cap_f = filter_cap(cap, anos, meses)

    rec = receita_dre(vf)
    cus = custo_dre(cu_f)
    imp = custo_impostos(imp_f)
    com = comissao(cv_f, ca_f)
    mg = rec - cus - imp - com
    dop = despesas_operacionais(cap_f)
    dfol = despesas_folha(cap_f)
    eop = mg - dfol - dop
    emp = emprestimos(cap_f)
    ret = retiradas_socios(cap_f)
    efin = eop - ret - emp

    base = rec if rec != 0 else 1

    return {
        "receita": rec,
        "custo": cus,
        "impostos": imp,
        "comissao": com,
        "margem_bruta": mg,
        "margem_bruta_pct": mg / base,
        "desp_operacional": dop,
        "desp_folha": dfol,
        "ebtida_operacional": eop,
        "ebtida_operacional_pct": eop / base,
        "emprestimos": emp,
        "retiradas": ret,
        "ebtida_final": efin,
        "ebtida_final_pct": efin / base,
    }
