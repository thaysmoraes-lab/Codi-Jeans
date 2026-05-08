"""
style.py — CSS global + helper de sidebar com logo
Importar em todas as páginas: from style import apply_style, sidebar_nav
"""
import streamlit as st
import base64, os

_BASE = os.path.dirname(os.path.abspath(__file__))
_LOGO = os.path.join(_BASE, "logo_codi.png")

def _logo_b64():
    try:
        with open(_LOGO, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return None

CODI_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0d0d0d;
    color: #d4d0c8;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #000000 !important;
    border-right: 2px solid #C9A84C !important;
}
[data-testid="stSidebar"] * { color: #d4d0c8 !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label {
    color: #C9A84C !important;
    font-size: 10px !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 600;
}
/* Tags do multiselect */
[data-testid="stSidebar"] [data-baseweb="tag"] {
    background: #C9A84C !important;
    color: #000 !important;
}

/* ── Logo container na sidebar ── */
.sidebar-logo {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20px 12px 16px;
    border-bottom: 1px solid #2a2a2a;
    margin-bottom: 20px;
}
.sidebar-logo img {
    width: 130px;
    filter: drop-shadow(0 2px 8px rgba(201,168,76,0.3));
    margin-bottom: 8px;
}
.sidebar-badge {
    font-size: 9px;
    color: #555 !important;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    text-align: center;
}

/* ── Nav links ── */
[data-testid="stSidebar"] a {
    color: #d4d0c8 !important;
    text-decoration: none !important;
    font-size: 13px;
    padding: 6px 0;
}
[data-testid="stSidebar"] a:hover { color: #C9A84C !important; }

/* ── Títulos ── */
h1 {
    color: #C9A84C !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
    border-bottom: 2px solid #C9A84C;
    padding-bottom: 8px;
    margin-bottom: 20px;
}
h2, h3 { color: #f0ede8 !important; font-weight: 500 !important; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: #141414 !important;
    border: 1px solid #C9A84C !important;
    border-radius: 10px;
    padding: 16px 20px;
}
[data-testid="metric-container"] label {
    color: #C9A84C !important;
    font-size: 10px !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 600;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #FFFFFF !important;
    font-size: 22px !important;
    font-weight: 700;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 12px !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid #2a2a2a;
    border-radius: 8px;
}
/* Header das tabelas */
[data-testid="stDataFrame"] th {
    background-color: #1a1a00 !important;
    color: #C9A84C !important;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 11px;
}

/* ── Tabs ── */
[data-baseweb="tab-list"] {
    background: #141414;
    border-radius: 8px;
    padding: 4px;
    gap: 4px;
    border: 1px solid #2a2a2a;
}
[data-baseweb="tab"] {
    background: transparent !important;
    color: #888 !important;
    border-radius: 6px !important;
}
[aria-selected="true"] {
    background: #C9A84C !important;
    color: #000000 !important;
    font-weight: 700 !important;
}

/* ── Botões ── */
[data-testid="baseButton-primary"] {
    background: #C9A84C !important;
    color: #000 !important;
    border: none !important;
    font-weight: 600 !important;
}
[data-testid="baseButton-secondary"] {
    background: transparent !important;
    color: #C9A84C !important;
    border: 1px solid #C9A84C !important;
    font-weight: 600 !important;
}
button[kind="primary"], .stButton>button {
    background: #C9A84C !important;
    color: #000 !important;
    border: none !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
}
button[kind="primary"]:hover, .stButton>button:hover {
    background: #E8C060 !important;
}

/* ── Inputs / Selects ── */
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea,
[data-baseweb="select"] {
    background: #141414 !important;
    border-color: #2a2a2a !important;
    color: #d4d0c8 !important;
}
[data-baseweb="input"]:focus-within,
[data-baseweb="select"]:focus-within {
    border-color: #C9A84C !important;
}

/* ── Divider ── */
hr { border-color: #2a2a2a; margin: 20px 0; }

/* ── Spinner ── */
[data-testid="stSpinner"] { color: #C9A84C !important; }

/* ── Success / Error / Warning ── */
[data-testid="stAlert"] {
    border-radius: 8px;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #141414; }
::-webkit-scrollbar-thumb { background: #3a3a3a; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #C9A84C; }

/* ── Faixas alternadas na tabela (zebra) ── */
.row-par  { background-color: #141414 !important; }
.row-impar{ background-color: #0d0d0d !important; }
</style>
"""

NAV_ITEMS = [
    ("app.py",                          "🏠  Visão Geral"),
    ("pages/00_importar_dados.py",       "📥  Importar Dados"),
    ("pages/01_fluxo_caixa.py",         "📊  Fluxo de Caixa"),
    ("pages/01b_atualizar_fluxo.py",    "✏️  Atualizar Fluxo"),
    ("pages/02_dre.py",                  "📋  DRE"),
    ("pages/03_projecao_dre.py",        "🔮  Projeção DRE"),
    ("pages/04_despesas_fornecedor.py", "🏭  Despesas Fornecedor"),
    ("pages/05_simulacao_dfc.py",       "⚡  Simulação DFC"),
]

def apply_style():
    """Injeta CSS global na página."""
    st.markdown(CODI_CSS, unsafe_allow_html=True)

def sidebar_logo():
    """Renderiza logo + nome na sidebar."""
    b64 = _logo_b64()
    if b64:
        st.markdown(
            f'<div class="sidebar-logo">'
            f'<img src="data:image/png;base64,{b64}" />'
            f'<div class="sidebar-badge">Sistema Financeiro</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="sidebar-logo">'
            '<div style="font-size:20px;font-weight:700;color:#C9A84C;letter-spacing:.05em">CODI.COM</div>'
            '<div class="sidebar-badge">Jeans Wear · Financeiro</div>'
            '</div>',
            unsafe_allow_html=True,
        )

def sidebar_nav(current=""):
    """Renderiza links de navegação."""
    st.markdown('<div style="padding: 0 4px;">', unsafe_allow_html=True)
    for path, label in NAV_ITEMS:
        try:
            st.page_link(path, label=label)
        except Exception:
            pass
    st.markdown('</div>', unsafe_allow_html=True)

def full_sidebar(filtros_fn=None, current=""):
    """Sidebar completa: logo + filtros + nav."""
    with st.sidebar:
        sidebar_logo()
        if filtros_fn:
            filtros_fn()
        st.markdown("---")
        st.markdown('<div style="font-size:10px;color:#555;text-transform:uppercase;letter-spacing:.1em;padding:4px 0 8px">Navegação</div>', unsafe_allow_html=True)
        sidebar_nav(current)
