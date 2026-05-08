"""
pages/00_importar_dados.py — Importação de dados do período
Suporta PDF (relatórios Wiki Sistemas) e Excel
"""

import streamlit as st
import pandas as pd
import pdfplumber
import re
import io
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Importar Dados · Codi.com", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
[data-testid="stSidebar"] { background: #111111 !important; border-right: 1px solid #2a2a2a; }
[data-testid="stSidebar"] * { color: #d4d0c8 !important; }
h1 { color: #C9A84C !important; font-weight: 600 !important; }
h2, h3 { color: #f0ede8 !important; font-weight: 500 !important; }
hr { border-color: #2a2a2a; }
.upload-box {
    border: 2px dashed #2a2a2a;
    border-radius: 12px;
    padding: 24px;
    margin: 8px 0;
    transition: border-color 0.2s;
}
.success-box {
    background: #0d2a1a;
    border: 1px solid #1a4a2a;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 8px 0;
}
.error-box {
    background: #2a0d0d;
    border: 1px solid #4a1a1a;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 8px 0;
}
</style>
""", unsafe_allow_html=True)

DATA_DIR = Path(__file__).parent.parent / "data"

with st.sidebar:
    st.markdown("### 🎛️ Navegação")
    st.page_link("app.py", label="🏠 Visão Geral")
    st.page_link("pages/00_importar_dados.py", label="📥 Importar Dados")
    st.page_link("pages/01_fluxo_caixa.py", label="📊 Fluxo de Caixa")
    st.page_link("pages/02_dre.py", label="📋 DRE")
    st.page_link("pages/03_projecao_dre.py", label="🔮 Projeção DRE")
    st.page_link("pages/04_despesas_fornecedor.py", label="🏭 Despesas por Fornecedor")
    st.page_link("pages/05_simulacao_dfc.py", label="⚡ Simulação DFC")


# ── Helpers ───────────────────────────────────────────────────────────────────

def brl(s):
    try:
        return float(str(s).replace('.', '').replace(',', '.').replace('R$', '').strip())
    except:
        return 0.0

def fmt(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ── PDF parsers ───────────────────────────────────────────────────────────────

def parse_cap_pdf(file) -> pd.DataFrame:
    """Parse Relatório Contas a Pagar (Wiki Sistemas PDF)."""
    rows = []
    pending_pessoa = None
    skip = ('CODI.COM', 'RELATÓRIO', 'Período', 'Filtros', 'TOTAL DE', 'VALOR TOTAL',
            'VALOR PAGO', 'VALOR EM', 'PLANO DE', 'ID Nº', 'CONTAS', 'TIPO DOC',
            'QTD.', 'Pag.:', 'Data:', 'BAIXADOS', 'ABERTOS', 'SUBSTITUIDOS', 'CANCELADOS')

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            for line in text.split('\n'):
                line = line.strip()
                if not line or any(line.startswith(s) for s in skip):
                    continue

                dates = re.findall(r'\d{2}/\d{2}/\d{4}', line)
                values = re.findall(r'R\$\s*([\d\.]+,\d{2})', line)

                if re.match(r'^\d{3,6}\s', line) and len(dates) >= 4 and len(values) >= 1:
                    sit_m = re.search(
                        r'\s([BA])\s+(.+?)\s+(BB CODI|BB VAREN|ITAU ALV|ITAU CODI|CODI\.COM)', line
                    )
                    plano = sit_m.group(2).strip() if sit_m else ''
                    sit = sit_m.group(1) if sit_m else ''

                    id_m = re.match(r'^(\d+)\s+(\S+)\s+', line)
                    doc_id = int(id_m.group(1)) if id_m else 0
                    doc_num = id_m.group(2) if id_m else ''

                    first_date_pos = line.find(dates[0])
                    before_date = line[:first_date_pos].strip()
                    pessoa_raw = re.sub(r'^\d+\s+\S+\s+', '', before_date).strip()
                    if not pessoa_raw and pending_pessoa:
                        pessoa_raw = pending_pessoa
                    pending_pessoa = None

                    rows.append({
                        'ID': doc_id,
                        'DOCUMENTO': doc_num,
                        'PESSOA': pessoa_raw,
                        'DT. CAD.': pd.to_datetime(dates[0], dayfirst=True, errors='coerce'),
                        'DT. EMISSÃO': pd.to_datetime(dates[1], dayfirst=True, errors='coerce'),
                        'DT. VENC.': pd.to_datetime(dates[2], dayfirst=True, errors='coerce'),
                        'DT. BAIXA': pd.to_datetime(dates[3], dayfirst=True, errors='coerce'),
                        'VALOR': brl(values[0]),
                        'VALOR PAGO': brl(values[1]) if len(values) > 1 else brl(values[0]),
                        'SIT': sit,
                        'PLANO DE CONTAS': plano,
                    })
                elif (re.match(r'^[A-ZÁÉÍÓÚÇÃ]', line)
                      and not dates
                      and 'R$' not in line
                      and len(line) > 3
                      and not re.match(r'^(PIX|BOLETO|CHEQUE|CARTÃO|TRANSF|R\$)', line)):
                    pending_pessoa = line

    df = pd.DataFrame(rows)
    if not df.empty:
        df['ANO'] = df['DT. BAIXA'].dt.year
        df['MES_NUM'] = df['DT. BAIXA'].dt.month
        meses = ["janeiro","fevereiro","março","abril","maio","junho",
                 "julho","agosto","setembro","outubro","novembro","dezembro"]
        df['MES'] = df['MES_NUM'].map({i+1: m for i, m in enumerate(meses)})
    return df


def parse_car_pdf(file) -> pd.DataFrame:
    """Parse Relatório de Receitas/Contas a Receber (Wiki Sistemas PDF)."""
    rows = []
    skip = ('CODI.COM', 'RELATÓRIO', 'Período', 'Filtros', 'TOTAL DE', 'VALOR TOTAL',
            'VALOR RECEBIDO', 'VALOR EM', 'PLANO DE', 'DOCUMENTO', 'TIPO DOC',
            'QTD.', 'Pag.:', 'Data:', 'BAIXADOS', 'ABERTOS', 'SIT CONTA')

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            for line in text.split('\n'):
                line = line.strip()
                if not line or any(line.startswith(s) for s in skip):
                    continue

                dates = re.findall(r'\d{2}/\d{2}/\d{4}', line)
                values = re.findall(r'R\$\s*([\d\.]+,\d{2})', line)

                if re.match(r'^[PN\d]\S*\s', line) and len(dates) >= 2 and len(values) >= 1:
                    tokens = line.split()
                    doc = tokens[0] if tokens else ''
                    sit = 'B' if ' B ' in line else 'A'

                    first_date_pos = line.find(dates[0])
                    pessoa_raw = line[len(doc):first_date_pos].strip() if first_date_pos > 0 else ''

                    val_total = brl(values[0])
                    val_recebido = brl(values[1]) if len(values) > 1 else 0.0

                    dt_cad = pd.to_datetime(dates[0], dayfirst=True, errors='coerce')
                    dt_venc = pd.to_datetime(dates[1], dayfirst=True, errors='coerce')
                    dt_baixa = pd.to_datetime(dates[2], dayfirst=True, errors='coerce') if len(dates) >= 3 else pd.NaT

                    rows.append({
                        'DOCUMENTO': doc,
                        'PESSOA': pessoa_raw,
                        'DT. CAD.': dt_cad,
                        'DT. VENC.': dt_venc,
                        'DT. BAIXA': dt_baixa,
                        'VALOR': val_total,
                        'VALOR RECEBIDO': val_recebido,
                        'SIT': sit,
                        'PLANO DE CONTAS': 'Vendas',
                    })

    df = pd.DataFrame(rows)
    if not df.empty:
        df['ANO'] = df['DT. BAIXA'].dt.year.fillna(df['DT. CAD.'].dt.year)
        df['MES_NUM'] = df['DT. BAIXA'].dt.month.fillna(df['DT. CAD.'].dt.month)
        meses = ["janeiro","fevereiro","março","abril","maio","junho",
                 "julho","agosto","setembro","outubro","novembro","dezembro"]
        df['MES'] = df['MES_NUM'].map({i+1: m for i, m in enumerate(meses)})
    return df


# ── Excel parsers ─────────────────────────────────────────────────────────────

def parse_cap_excel(file) -> pd.DataFrame:
    """Parse Contas a Pagar from Excel (same format as in DFC file)."""
    try:
        # Try to find the right sheet
        xls = pd.ExcelFile(file)
        sheet = None
        for s in xls.sheet_names:
            if 'PAGAR' in s.upper() or 'CAP' in s.upper():
                sheet = s
                break
        sheet = sheet or xls.sheet_names[0]
        df = pd.read_excel(file, sheet_name=sheet)

        # Normalize column names
        df.columns = [str(c).strip().upper() for c in df.columns]

        # Map common variations
        col_map = {
            'VALOR': ['VALOR', 'VLOR', 'VLR'],
            'VALOR PAGO': ['VALOR PAGO', 'VLR PAGO', 'PAGO'],
            'PLANO DE CONTAS': ['PLANO DE CONTAS', 'PLANO', 'CONTA'],
            'PESSOA': ['PESSOA', 'FORNECEDOR', 'NOME'],
            'DT. BAIXA': ['DT. BAIXA', 'DATA BAIXA', 'BAIXA', 'DT BAIXA'],
            'DT. VENC.': ['DT. VENC.', 'VENCIMENTO', 'DT VENC'],
            'SIT': ['SIT', 'STATUS', 'SITUAÇÃO'],
        }

        for target, variants in col_map.items():
            for v in variants:
                if v in df.columns and target not in df.columns:
                    df.rename(columns={v: target}, inplace=True)
                    break

        # Parse dates
        for dc in ['DT. BAIXA', 'DT. VENC.', 'DT. CAD.', 'DT. EMISSÃO']:
            if dc in df.columns:
                df[dc] = pd.to_datetime(df[dc], errors='coerce', dayfirst=True)

        if 'VALOR' in df.columns:
            df['VALOR'] = pd.to_numeric(df['VALOR'], errors='coerce').fillna(0)
        if 'VALOR PAGO' in df.columns:
            df['VALOR PAGO'] = pd.to_numeric(df['VALOR PAGO'], errors='coerce').fillna(0)

        meses = ["janeiro","fevereiro","março","abril","maio","junho",
                 "julho","agosto","setembro","outubro","novembro","dezembro"]
        if 'DT. BAIXA' in df.columns:
            df['ANO'] = df['DT. BAIXA'].dt.year
            df['MES_NUM'] = df['DT. BAIXA'].dt.month
            df['MES'] = df['MES_NUM'].map({i+1: m for i, m in enumerate(meses)})

        return df
    except Exception as e:
        st.error(f"Erro ao ler Excel CAP: {e}")
        return pd.DataFrame()


def parse_car_excel(file) -> pd.DataFrame:
    """Parse Contas a Receber from Excel."""
    try:
        xls = pd.ExcelFile(file)
        sheet = None
        for s in xls.sheet_names:
            if 'RECEBER' in s.upper() or 'CAR' in s.upper() or 'RECEITA' in s.upper():
                sheet = s
                break
        sheet = sheet or xls.sheet_names[0]
        df = pd.read_excel(file, sheet_name=sheet)
        df.columns = [str(c).strip().upper() for c in df.columns]

        for dc in ['DT. BAIXA', 'DT. VENC.', 'DT. CAD.']:
            if dc in df.columns:
                df[dc] = pd.to_datetime(df[dc], errors='coerce', dayfirst=True)

        for vc in ['VALOR', 'VALOR RECEBIDO', 'VALOR _X000D_\nRECEBIDO']:
            if vc in df.columns:
                df[vc] = pd.to_numeric(df[vc], errors='coerce').fillna(0)

        meses = ["janeiro","fevereiro","março","abril","maio","junho",
                 "julho","agosto","setembro","outubro","novembro","dezembro"]
        ref_date = df.get('DT. BAIXA', df.get('DT. CAD.'))
        if ref_date is not None:
            df['ANO'] = ref_date.dt.year
            df['MES_NUM'] = ref_date.dt.month
            df['MES'] = df['MES_NUM'].map({i+1: m for i, m in enumerate(meses)})

        return df
    except Exception as e:
        st.error(f"Erro ao ler Excel CAR: {e}")
        return pd.DataFrame()


# ── Merge with existing data ───────────────────────────────────────────────────

def merge_and_save_cap(new_df: pd.DataFrame, periodo: str):
    """Merge new CAP data into the main DFC file."""
    try:
        xls_path = DATA_DIR / "DFC_JUL_A_OUT-25.xlsx"
        existing = pd.read_excel(xls_path, sheet_name="CONTAS A PAGAR")
        existing['DT. BAIXA'] = pd.to_datetime(existing['DT. BAIXA'], errors='coerce')

        # Remove records from same period to avoid duplication
        if 'ANO' in new_df.columns and 'MES_NUM' in new_df.columns:
            anos = new_df['ANO'].dropna().unique()
            meses = new_df['MES_NUM'].dropna().unique()
            mask = ~(
                existing['DT. BAIXA'].dt.year.isin(anos) &
                existing['DT. BAIXA'].dt.month.isin(meses)
            )
            existing_clean = existing[mask]
        else:
            existing_clean = existing

        # Align columns
        for col in existing_clean.columns:
            if col not in new_df.columns:
                new_df[col] = None
        new_df = new_df[[c for c in existing_clean.columns if c in new_df.columns]]

        merged = pd.concat([existing_clean, new_df], ignore_index=True)

        with pd.ExcelWriter(xls_path, engine='openpyxl', mode='a',
                            if_sheet_exists='replace') as writer:
            merged.to_excel(writer, sheet_name='CONTAS A PAGAR', index=False)

        return len(new_df), len(merged)
    except Exception as e:
        raise Exception(f"Erro ao salvar CAP: {e}")


def merge_and_save_car(new_df: pd.DataFrame, periodo: str):
    """Merge new CAR data into the main DFC file."""
    try:
        xls_path = DATA_DIR / "DFC_JUL_A_OUT-25.xlsx"
        existing = pd.read_excel(xls_path, sheet_name="CONTAS A RECEBER")
        ref_col = 'DT. BAIXA'
        if ref_col in existing.columns:
            existing[ref_col] = pd.to_datetime(existing[ref_col], errors='coerce')

        if 'ANO' in new_df.columns and 'MES_NUM' in new_df.columns:
            anos = new_df['ANO'].dropna().unique()
            meses = new_df['MES_NUM'].dropna().unique()
            if ref_col in existing.columns:
                mask = ~(
                    existing[ref_col].dt.year.isin(anos) &
                    existing[ref_col].dt.month.isin(meses)
                )
                existing_clean = existing[mask]
            else:
                existing_clean = existing
        else:
            existing_clean = existing

        merged = pd.concat([existing_clean, new_df], ignore_index=True)

        with pd.ExcelWriter(xls_path, engine='openpyxl', mode='a',
                            if_sheet_exists='replace') as writer:
            merged.to_excel(writer, sheet_name='CONTAS A RECEBER', index=False)

        return len(new_df), len(merged)
    except Exception as e:
        raise Exception(f"Erro ao salvar CAR: {e}")


# ── UI ─────────────────────────────────────────────────────────────────────────

st.title("📥 Importar Dados do Período")
st.caption("Importe relatórios do Wiki Sistemas (PDF ou Excel) para atualizar o sistema financeiro.")

st.markdown("---")

# ── Seção CAP ────────────────────────────────────────────────────────────────
st.subheader("1. Contas a Pagar")

col1, col2 = st.columns([3, 1])
with col1:
    cap_file = st.file_uploader(
        "Relatório de Contas a Pagar",
        type=["pdf", "xlsx", "xls"],
        key="cap_upload",
        help="PDF do Wiki Sistemas ou Excel com as mesmas colunas"
    )

cap_df = None
if cap_file:
    with st.spinner("Lendo arquivo..."):
        try:
            if cap_file.name.lower().endswith('.pdf'):
                cap_df = parse_cap_pdf(cap_file)
                tipo = "PDF"
            else:
                cap_df = parse_cap_excel(cap_file)
                tipo = "Excel"

            if cap_df is not None and not cap_df.empty:
                total_val = cap_df['VALOR'].sum() if 'VALOR' in cap_df.columns else 0
                n = len(cap_df)
                st.success(f"✅ **{tipo}** lido com sucesso — **{n} lançamentos** — Total: **{fmt(total_val)}**")

                with st.expander("Prévia dos dados (10 primeiras linhas)"):
                    cols_show = [c for c in ['PESSOA','DT. BAIXA','VALOR','PLANO DE CONTAS','SIT'] if c in cap_df.columns]
                    st.dataframe(cap_df[cols_show].head(10), use_container_width=True, hide_index=True)

                    if 'PLANO DE CONTAS' in cap_df.columns:
                        st.markdown("**Por Plano de Contas:**")
                        resumo = cap_df.groupby('PLANO DE CONTAS')['VALOR'].sum().sort_values(ascending=False).head(15)
                        st.dataframe(
                            resumo.reset_index().rename(columns={'VALOR':'Total'})
                            .style.format({'Total': lambda v: fmt(v)}),
                            use_container_width=True, hide_index=True
                        )
            else:
                st.error("Nenhum dado encontrado no arquivo. Verifique se é um relatório de Contas a Pagar.")
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {e}")

if cap_df is not None and not cap_df.empty:
    periodo_cap = st.text_input("Identificação do período (ex: abril/2026)", key="periodo_cap",
                                placeholder="abril/2026")
    if st.button("💾 Importar Contas a Pagar", type="primary", key="btn_cap"):
        if not periodo_cap:
            st.warning("Informe o período antes de importar.")
        else:
            with st.spinner("Salvando dados..."):
                try:
                    n_new, n_total = merge_and_save_cap(cap_df, periodo_cap)
                    st.success(f"✅ **{n_new} registros** importados. Base atualizada com **{n_total} lançamentos** no total.")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

st.markdown("---")

# ── Seção CAR ────────────────────────────────────────────────────────────────
st.subheader("2. Contas a Receber / Receitas")

car_file = st.file_uploader(
    "Relatório de Contas a Receber / Receitas",
    type=["pdf", "xlsx", "xls"],
    key="car_upload",
    help="PDF do Wiki Sistemas ou Excel exportado do sistema"
)

car_df = None
if car_file:
    with st.spinner("Lendo arquivo..."):
        try:
            if car_file.name.lower().endswith('.pdf'):
                car_df = parse_car_pdf(car_file)
                tipo = "PDF"
            else:
                car_df = parse_car_excel(car_file)
                tipo = "Excel"

            if car_df is not None and not car_df.empty:
                total_val = car_df['VALOR'].sum() if 'VALOR' in car_df.columns else 0
                val_rec_col = next((c for c in car_df.columns if 'RECEBIDO' in c.upper()), None)
                total_rec = car_df[val_rec_col].sum() if val_rec_col else 0
                n = len(car_df)
                baixados = car_df[car_df.get('SIT', pd.Series(['A']*len(car_df))) == 'B'] if 'SIT' in car_df.columns else car_df

                st.success(
                    f"✅ **{tipo}** lido — **{n} documentos** — "
                    f"Total: **{fmt(total_val)}** | Recebido: **{fmt(total_rec)}** | "
                    f"Baixados: **{len(baixados)}**"
                )

                with st.expander("Prévia dos dados (10 primeiras linhas)"):
                    cols_show = [c for c in ['DOCUMENTO','PESSOA','DT. BAIXA','VALOR','VALOR RECEBIDO','SIT'] if c in car_df.columns]
                    st.dataframe(car_df[cols_show].head(10), use_container_width=True, hide_index=True)
            else:
                st.error("Nenhum dado encontrado. Verifique se é um relatório de Receitas/Contas a Receber.")
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {e}")

if car_df is not None and not car_df.empty:
    periodo_car = st.text_input("Identificação do período", key="periodo_car",
                                placeholder="abril/2026")
    if st.button("💾 Importar Contas a Receber", type="primary", key="btn_car"):
        if not periodo_car:
            st.warning("Informe o período antes de importar.")
        else:
            with st.spinner("Salvando dados..."):
                try:
                    n_new, n_total = merge_and_save_car(car_df, periodo_car)
                    st.success(f"✅ **{n_new} registros** importados. Base com **{n_total} lançamentos** no total.")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

st.markdown("---")

# ── Seção Vendas (Excel) ──────────────────────────────────────────────────────
st.subheader("3. Vendas (Excel)")
st.caption("Para importar vendas, o Excel precisa ter o mesmo formato do VENDAS_2025.xlsx — colunas: DESCRIÇÃO DO PRODUTO, VALOR TOTAL, DATA, CUSTO1, etc.")

vd_file = st.file_uploader(
    "Planilha de Vendas (.xlsx)",
    type=["xlsx", "xls"],
    key="vd_upload"
)

if vd_file:
    with st.spinner("Lendo planilha..."):
        try:
            xls = pd.ExcelFile(vd_file)
            sheets_found = {s: pd.read_excel(vd_file, sheet_name=s) for s in xls.sheet_names}

            for sheet_name, df_sheet in sheets_found.items():
                n = len(df_sheet)
                cols = list(df_sheet.columns[:6])
                st.info(f"Aba **{sheet_name}**: {n} linhas | Colunas: {', '.join(str(c) for c in cols)}...")

            periodo_vd = st.text_input("Período (ex: jan-abr/2026)", key="periodo_vd",
                                       placeholder="jan-abr/2026")

            if st.button("💾 Substituir arquivo de Vendas", key="btn_vd"):
                if not periodo_vd:
                    st.warning("Informe o período.")
                else:
                    dest = DATA_DIR / "VENDAS_2025.xlsx"
                    dest_bkp = DATA_DIR / f"VENDAS_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    # Backup
                    import shutil
                    if dest.exists():
                        shutil.copy(dest, dest_bkp)
                    # Save new
                    vd_file.seek(0)
                    with open(dest, 'wb') as f:
                        f.write(vd_file.read())
                    st.success(f"✅ Arquivo de vendas atualizado! Backup salvo em {dest_bkp.name}")
                    st.cache_data.clear()
        except Exception as e:
            st.error(f"Erro: {e}")

st.markdown("---")

# ── Status da base atual ──────────────────────────────────────────────────────
st.subheader("📊 Status atual da base de dados")

try:
    cap_base = pd.read_excel(DATA_DIR / "DFC_JUL_A_OUT-25.xlsx", sheet_name="CONTAS A PAGAR")
    car_base = pd.read_excel(DATA_DIR / "DFC_JUL_A_OUT-25.xlsx", sheet_name="CONTAS A RECEBER")
    vd_base  = pd.read_excel(DATA_DIR / "VENDAS_2025.xlsx", sheet_name="VENDAS")

    cap_base['DT. BAIXA'] = pd.to_datetime(cap_base['DT. BAIXA'], errors='coerce')
    car_base['DT. BAIXA'] = pd.to_datetime(car_base['DT. BAIXA'], errors='coerce')
    vd_base['DATA'] = pd.to_datetime(vd_base['DATA'], errors='coerce')

    col1, col2, col3 = st.columns(3)
    col1.metric("Contas a Pagar",
                f"{len(cap_base):,} lançamentos",
                f"Até {cap_base['DT. BAIXA'].max().strftime('%d/%m/%Y') if cap_base['DT. BAIXA'].notna().any() else '—'}")
    col2.metric("Contas a Receber",
                f"{len(car_base):,} documentos",
                f"Até {car_base['DT. BAIXA'].max().strftime('%d/%m/%Y') if car_base['DT. BAIXA'].notna().any() else '—'}")
    col3.metric("Vendas",
                f"{len(vd_base):,} itens",
                f"Até {vd_base['DATA'].max().strftime('%d/%m/%Y') if vd_base['DATA'].notna().any() else '—'}")

    # Períodos por mês
    st.markdown("**Contas a Pagar — lançamentos por mês:**")
    cap_base['mes_ano'] = cap_base['DT. BAIXA'].dt.to_period('M')
    resumo_meses = cap_base.groupby('mes_ano').agg(
        Lançamentos=('VALOR', 'count'),
        Total=('VALOR', 'sum')
    ).sort_index(ascending=False).head(12)
    resumo_meses.index = resumo_meses.index.astype(str)
    st.dataframe(
        resumo_meses.style.format({'Total': lambda v: fmt(v)}),
        use_container_width=True
    )
except Exception as e:
    st.warning(f"Não foi possível carregar status da base: {e}")
