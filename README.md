# 💰 Sistema Financeiro Codi.com

Sistema financeiro desenvolvido em Python + Streamlit, substituindo o Power BI.

## 📁 Estrutura do projeto

```
codi-financeiro/
├── app.py                          ← Visão Geral (página principal)
├── engine.py                       ← Motor de cálculo (todas as fórmulas)
├── requirements.txt
├── .streamlit/
│   └── config.toml                 ← Tema Codi.com (dourado + escuro)
├── data/
│   ├── VENDAS_2025.xlsx
│   ├── DFC_JUL_A_OUT-25.xlsx
│   ├── Plano_de_contas.xlsx
│   ├── Simulação_de_Precificação.xlsx
│   ├── CALENDÁRIO.xlsx
│   └── CALENDÁRIO_COMPETENCIA.xlsx
└── pages/
    ├── 01_fluxo_caixa.py
    ├── 02_dre.py
    ├── 03_projecao_dre.py
    ├── 04_despesas_fornecedor.py
    └── 05_simulacao_dfc.py
```

## 🚀 Como rodar localmente

### 1. Clone o repositório
```bash
git clone https://github.com/SEU_USUARIO/codi-financeiro.git
cd codi-financeiro
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Rode o app
```bash
streamlit run app.py
```

Acesse em: http://localhost:8501

---

## ☁️ Deploy no Streamlit Cloud (gratuito)

1. Suba o projeto para o GitHub
2. Acesse https://share.streamlit.io
3. Clique em **New app**
4. Selecione o repositório e o arquivo `app.py`
5. Clique em **Deploy**

> ⚠️ **Importante**: os arquivos `.xlsx` da pasta `data/` precisam estar no repositório para o deploy funcionar.

---

## 📋 Páginas do sistema

| Página | Equivalente Power BI | Descrição |
|--------|---------------------|-----------|
| 🏠 Visão Geral | — | KPIs + gráfico receita × margem |
| 📊 Fluxo de Caixa | FLUXO DE CAIXA | Tabela hierárquica R/D + gráfico barras |
| 📋 DRE | DRE | ValorDRE + AV% + cascata + barras |
| 🔮 Projeção DRE | PROJEÇÃO DRE | Cenários com sliders |
| 🏭 Despesas Fornecedor | DESPESAS POR FORNECEDOR | Ranking + evolução mensal |
| ⚡ Simulação DFC | SIMULAÇÃO DFC | O que-se + projeção diária |

---

## 🧮 Fórmulas implementadas (equivalente DAX)

```python
ReceitaDRE         = SUM(VENDAS[VALOR TOTAL])
CustoDRE           = SUM(CUSTO[CUSTO1])
CustoImpostos      = SUM(IMPOSTOS_CALCULADO[IMPOSTOS])
Comissão           = SUM(COMISSÃO_VENDEDORES) + SUM(COMISSÃO_ASSESSORES)
MargemBruta        = Receita - Custo - Impostos - Comissão
DespesasOperac.    = CONTAS_PAGAR filtrado por 30 categorias
DespesasFolha      = CONTAS_PAGAR filtrado por 7 categorias de RH
EbtidaOperacional  = MargemBruta - Folha - Operacional
EbtidaFinal        = EbtidaOper. - Empréstimos - RetiradasSócios
AV%                = ValorDRE / ReceitaDRE
```

---

## 🔄 Como atualizar os dados

Basta substituir os arquivos `.xlsx` na pasta `data/` e fazer commit no GitHub.
O Streamlit Cloud vai recarregar automaticamente.

---

## 🛠️ Taxas configuradas

| Descrição | Valor |
|-----------|-------|
| Simples Nacional | 10,47% |
| Comissão Vendedores | 1,5% |
| Comissão Assessores | 0,1% |

> Para alterar, edite a planilha `VENDAS_2025.xlsx` → aba `TAXAS`.
