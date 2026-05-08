"""
pages/01b_atualizar_fluxo.py
Atualiza os valores realizados do fluxo_de_caixa.csv mês a mês
"""

import streamlit as st
import pandas as pd
import os, sys
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from style import apply_style, full_sidebar
from engine import MESES_ORDER

st.set_page_config(page_title="Atualizar Fluxo · Codi.com", layout="wide")
apply_style()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "data", "fluxo_de_caixa.csv")

# ── Sidebar ────────────────────────────────────────────────────────────────────
full_sidebar(current="pages/01b_atualizar_fluxo.py")

# ── Carregar CSV atual ─────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_csv():
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df.columns = df.columns.str.strip()
    df["Mês"] = df["Mês"].str.strip().str.lower()
    df["VALOR"] = pd.to_numeric(df["VALOR"], errors="coerce").fillna(0)
    df["Ano"] = df["Ano"].astype(int)
    return df

# ── Título ─────────────────────────────────────────────────────────────────────
st.title("✏️ Atualizar Fluxo de Caixa")
st.markdown("""
<div style="background:#141400;border:1px solid #C9A84C;border-radius:8px;padding:14px 18px;margin-bottom:20px">
  <b style="color:#C9A84C">Como funciona?</b><br>
  <span style="color:#ccc;font-size:13px">
  Aqui você adiciona os valores <b>realizados</b> de novos meses ao arquivo CSV do fluxo de caixa.<br>
  Você pode: <b>(1)</b> editar diretamente na tabela, <b>(2)</b> adicionar linhas novas, ou 
  <b>(3)</b> colar dados de uma planilha Excel.<br>
  Após salvar, o Fluxo de Caixa será atualizado automaticamente.
  </span>
</div>
""", unsafe_allow_html=True)

df = load_csv()

# ── Aba de métodos ─────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "📝  Adicionar lançamentos",
    "📊  Editar tabela completa",
    "📤  Importar Excel / CSV",
])

# ════════════════════════════════════════════════════════════
# TAB 1 — Formulário para adicionar lançamentos novos
# ════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Adicionar valores realizados")
    st.caption("Preencha os campos e clique em '+ Adicionar'. Ao terminar, clique em 'Salvar CSV'.")

    # Opções para dropdowns
    classifs = sorted(df["Classificação"].unique())
    planos_por_classif = df.groupby("Classificação")["PLANO DE CONTAS"].apply(
        lambda x: sorted(x.unique())
    ).to_dict()
    anos_disp = sorted(df["Ano"].unique()) + [max(df["Ano"].unique())+1]
    meses_cap = [m.capitalize() for m in MESES_ORDER]

    # Estado dos lançamentos pendentes
    if "novos_lancamentos" not in st.session_state:
        st.session_state.novos_lancamentos = []

    col1, col2 = st.columns([1, 2])
    with col1:
        classif_sel = st.selectbox("Classificação", classifs, key="add_classif")
    with col2:
        planos_disp = planos_por_classif.get(classif_sel, [])
        plano_sel = st.selectbox("Plano de Contas", planos_disp, key="add_plano")

    col3, col4, col5 = st.columns(3)
    with col3:
        ano_sel = st.selectbox("Ano", anos_disp, index=len(anos_disp)-1, key="add_ano")
    with col4:
        mes_sel = st.selectbox("Mês", meses_cap, key="add_mes")
    with col5:
        valor_input = st.number_input(
            "Valor (R$) — negativo p/ saídas",
            value=0.0, step=100.0, format="%.2f", key="add_valor"
        )

    # Ordenação automática
    ordem_map = {"Receita": 1, "Custo": 2, "Despesas": 3}
    ordem_val = ordem_map.get(classif_sel, 3)

    if st.button("➕ Adicionar lançamento", type="primary"):
        st.session_state.novos_lancamentos.append({
            "Ordem": ordem_val,
            "Classificação": classif_sel,
            "PLANO DE CONTAS": plano_sel,
            "VALOR": valor_input,
            "Ano": ano_sel,
            "Mês": mes_sel.lower(),
        })
        st.success(f"✅ Adicionado: {classif_sel} / {plano_sel} — {mes_sel}/{ano_sel} = R$ {valor_input:,.2f}")

    # Tabela de pendentes
    if st.session_state.novos_lancamentos:
        st.markdown("#### Lançamentos a salvar")
        df_pend = pd.DataFrame(st.session_state.novos_lancamentos)
        st.dataframe(df_pend, use_container_width=True, hide_index=True)

        c_save, c_clear = st.columns(2)
        with c_save:
            if st.button("💾 Salvar no CSV", type="primary"):
                df_atual = load_csv()
                df_novos = pd.DataFrame(st.session_state.novos_lancamentos)

                # Remover duplicatas: mesmo plano/ano/mês → substituir
                for _, row in df_novos.iterrows():
                    mask = (
                        (df_atual["Classificação"] == row["Classificação"]) &
                        (df_atual["PLANO DE CONTAS"] == row["PLANO DE CONTAS"]) &
                        (df_atual["Ano"] == row["Ano"]) &
                        (df_atual["Mês"] == row["Mês"])
                    )
                    df_atual = df_atual[~mask]

                df_final = pd.concat([df_atual, df_novos], ignore_index=True)
                df_final = df_final.sort_values(["Ordem","Classificação","PLANO DE CONTAS","Ano","Mês"])
                df_final.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

                st.cache_data.clear()
                st.session_state.novos_lancamentos = []
                st.success("✅ CSV salvo com sucesso! Atualize o Fluxo de Caixa para ver os dados.")
                st.balloons()

        with c_clear:
            if st.button("🗑️ Limpar lista"):
                st.session_state.novos_lancamentos = []
                st.rerun()

# ════════════════════════════════════════════════════════════
# TAB 2 — Edição direta da tabela
# ════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Editar tabela completa")
    st.caption("Filtre por Ano/Classificação, edite os valores e salve.")

    col_a, col_b = st.columns(2)
    with col_a:
        ano_f = st.multiselect("Filtrar por Ano",
            sorted(df["Ano"].unique()), default=[max(df["Ano"].unique())], key="ed_ano")
    with col_b:
        cl_f = st.multiselect("Filtrar por Classificação",
            sorted(df["Classificação"].unique()), default=[], key="ed_classif")

    df_edit = df.copy()
    if ano_f:
        df_edit = df_edit[df_edit["Ano"].isin(ano_f)]
    if cl_f:
        df_edit = df_edit[df_edit["Classificação"].isin(cl_f)]

    df_edited = st.data_editor(
        df_edit,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "Ordem":          st.column_config.NumberColumn("Ordem", width=70),
            "Classificação":  st.column_config.SelectboxColumn(
                "Classificação", options=classifs, width=120),
            "PLANO DE CONTAS":st.column_config.TextColumn("Plano de Contas", width=220),
            "VALOR":          st.column_config.NumberColumn(
                "Valor (R$)", format="R$ %.2f", width=140),
            "Ano":            st.column_config.NumberColumn("Ano", width=80),
            "Mês":            st.column_config.SelectboxColumn(
                "Mês", options=MESES_ORDER, width=110),
        },
        key="table_editor"
    )

    if st.button("💾 Salvar alterações da tabela", type="primary", key="btn_save_edit"):
        # Merge: atualiza as linhas editadas, mantém as não filtradas
        df_base = df.copy()
        if ano_f:
            df_base = df_base[~df_base["Ano"].isin(ano_f)]
        if cl_f:
            df_base = df_base[~df_base["Classificação"].isin(cl_f)]
        elif ano_f:
            df_base = df[~df["Ano"].isin(ano_f)]

        df_final = pd.concat([df_base, df_edited], ignore_index=True)
        df_final = df_final.sort_values(["Ordem","Classificação","PLANO DE CONTAS","Ano","Mês"])
        df_final.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
        st.cache_data.clear()
        st.success("✅ Alterações salvas!")
        st.rerun()

# ════════════════════════════════════════════════════════════
# TAB 3 — Importar Excel/CSV com novos dados
# ════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Importar planilha com valores realizados")

    st.markdown("""
    <div style="background:#0d0d0d;border:1px solid #2a2a2a;border-radius:8px;padding:12px 16px;margin-bottom:16px">
    <b style="color:#C9A84C">Formato esperado da planilha:</b><br>
    <code style="color:#aaa;font-size:12px">Ordem | Classificação | PLANO DE CONTAS | VALOR | Ano | Mês</code><br>
    <span style="color:#888;font-size:12px">
    • <b>Ordem</b>: 1=Receita, 2=Custo, 3=Despesas<br>
    • <b>VALOR</b>: positivo para Receita, negativo para Custo/Despesas<br>
    • <b>Mês</b>: em minúsculas (janeiro, fevereiro...)<br>
    • Linhas com o mesmo Classificação + Plano + Ano + Mês serão <b>substituídas</b>
    </span>
    </div>
    """, unsafe_allow_html=True)

    # Download do template
    template_df = pd.DataFrame([
        {"Ordem":1,"Classificação":"Receita","PLANO DE CONTAS":"Vendas","VALOR":500000,"Ano":2026,"Mês":"maio"},
        {"Ordem":2,"Classificação":"Custo","PLANO DE CONTAS":"Facção","VALOR":-50000,"Ano":2026,"Mês":"maio"},
        {"Ordem":3,"Classificação":"Despesas","PLANO DE CONTAS":"Salário e Ordenados","VALOR":-30000,"Ano":2026,"Mês":"maio"},
    ])
    buf = BytesIO()
    template_df.to_excel(buf, index=False)
    st.download_button(
        "⬇️ Baixar template Excel",
        data=buf.getvalue(),
        file_name="template_fluxo_caixa.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    uploaded = st.file_uploader(
        "Faça upload do arquivo Excel ou CSV com os novos dados",
        type=["xlsx","xls","csv"],
        key="uploader_fluxo"
    )

    if uploaded:
        try:
            if uploaded.name.endswith(".csv"):
                df_import = pd.read_csv(uploaded, encoding="utf-8-sig")
            else:
                df_import = pd.read_excel(uploaded)

            df_import.columns = df_import.columns.str.strip()
            df_import["Mês"] = df_import["Mês"].str.strip().str.lower()
            df_import["VALOR"] = pd.to_numeric(df_import["VALOR"], errors="coerce").fillna(0)
            df_import["Ano"] = df_import["Ano"].astype(int)

            st.markdown(f"**Prévia — {len(df_import)} linhas importadas:**")
            st.dataframe(df_import, use_container_width=True, hide_index=True)

            # Resumo por mês
            res = df_import.groupby(["Ano","Mês","Classificação"])["VALOR"].sum().reset_index()
            st.markdown("**Resumo por Mês / Classificação:**")
            st.dataframe(res, use_container_width=True, hide_index=True)

            if st.button("✅ Confirmar importação e salvar", type="primary"):
                df_base = load_csv()
                for _, row in df_import.iterrows():
                    mask = (
                        (df_base["Classificação"] == row["Classificação"]) &
                        (df_base["PLANO DE CONTAS"] == row["PLANO DE CONTAS"]) &
                        (df_base["Ano"] == row["Ano"]) &
                        (df_base["Mês"] == row["Mês"])
                    )
                    df_base = df_base[~mask]

                df_final = pd.concat([df_base, df_import], ignore_index=True)
                df_final = df_final.sort_values(["Ordem","Classificação","PLANO DE CONTAS","Ano","Mês"])
                df_final.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
                st.cache_data.clear()
                st.success(f"✅ {len(df_import)} lançamentos importados e salvos!")
                st.balloons()

        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")

# ── Rodapé ─────────────────────────────────────────────────────────────────────
st.markdown("---")
col_dl1, col_dl2 = st.columns(2)
with col_dl1:
    st.markdown("##### 📄 CSV atual")
    df_atual = load_csv()
    csv_bytes = df_atual.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        "⬇️ Baixar fluxo_de_caixa.csv",
        data=csv_bytes,
        file_name="fluxo_de_caixa.csv",
        mime="text/csv",
    )
with col_dl2:
    st.markdown("##### 📊 Resumo do CSV atual")
    resumo = df_atual.groupby(["Ano","Classificação"])["VALOR"].sum().reset_index()
    resumo["VALOR"] = resumo["VALOR"].apply(lambda v: f"R$ {v:,.2f}".replace(",","X").replace(".",",").replace("X","."))
    st.dataframe(resumo, use_container_width=True, hide_index=True, height=220)
