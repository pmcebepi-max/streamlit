import streamlit as st
import pandas as pd
from fpdf import FPDF

# --- URL da planilha pública publicada como CSV ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1hW17V_blimDdum1A2OotpHlBJz_9fkJJH1jIoT-2J68/edit?usp=sharing"

# --- Carregar dados ---
df = pd.read_csv(SHEET_URL)

# Remover coluna de carimbo de data/hora
df = df.drop(columns=["Carimbo de data/hora"])

st.title("Lista de Presença com Assinatura")

# --- Filtros ---
data_unica = df["Data"].unique()
polo_unico = df["Polo de Instrução"].unique()

data_selecionada = st.selectbox("Selecione a Data", sorted(data_unica))
polo_selecionado = st.selectbox("Selecione o Polo de Instrução", sorted(polo_unico))

# Filtrar dataframe
df_filtrado = df[(df["Data"] == data_selecionada) & (df["Polo de Instrução"] == polo_selecionado)]

st.write(f"{len(df_filtrado)} registros encontrados")
st.dataframe(df_filtrado)

# --- Função para gerar PDF ---
def gerar_pdf(df, polo, data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Lista de Presença - {polo} - {data}", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", "", 12)
    
    # Cabeçalho
    colunas = df.columns.tolist()
    col_width = pdf.w / len(colunas) - 10  # largura proporcional
    for col in colunas:
        pdf.cell(col_width, 10, col, border=1)
    pdf.ln()
    
    # Linhas com espaço para assinatura
    for _, row in df.iterrows():
        for item in row:
            pdf.cell(col_width, 10, str(item), border=1)
        pdf.cell(col_width, 10, "__________________", border=1)  # espaço para assinatura
        pdf.ln()
    
    return pdf.output(dest="S").encode("latin1")

# --- Botão para gerar PDF ---
if st.button("Gerar PDF"):
    pdf_bytes = gerar_pdf(df_filtrado, polo_selecionado, data_selecionada)
    st.download_button(
        label="Baixar PDF",
        data=pdf_bytes,
        file_name=f"Lista_Presenca_{polo_selecionado}_{data_selecionada}.pdf",
        mime="application/pdf"
    )
