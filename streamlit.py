import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- Link CSV público ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvhc1E8BOJfuULhmzvzcxtG9PkYD2KQfpfFIYWSTUN4Jl1eJJlXg1Nmy1zBkeLbePQaKz7-jKwWwZn/pub?gid=1995854408&single=true&output=csv"

df = pd.read_csv(SHEET_URL)
df = df.drop(columns=["Carimbo de data/hora"])

st.title("Lista de Presença com Assinatura")

data_unica = df["Data"].unique()
polo_unico = df["Polo de Instrução"].unique()

data_selecionada = st.selectbox("Selecione a Data", sorted(data_unica))
polo_selecionado = st.selectbox("Selecione o Polo de Instrução", sorted(polo_unico))

df_filtrado = df[(df["Data"] == data_selecionada) & (df["Polo de Instrução"] == polo_selecionado)]
st.write(f"{len(df_filtrado)} registros encontrados")
st.dataframe(df_filtrado)

# --- Função para gerar PDF ---
def gerar_pdf(df, polo, data):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=10)  # permite quebra de página automática
    pdf.add_page()
    
    # Função para escrever o cabeçalho da tabela
    def escrever_cabecalho():
        pdf.set_font("Arial", "B", 10)
        colunas = df.columns.tolist()
        col_width = pdf.w / (len(colunas)+1)  # +1 para assinatura
        for col in colunas:
            pdf.cell(col_width, 8, col, border=1, align='C')
        pdf.cell(col_width, 8, "Assinatura", border=1, align='C')
        pdf.ln()
        return col_width
    
    # Cabeçalho da tabela
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"Lista de Presença - {polo} - {data}", ln=True, align="C")
    pdf.ln(5)
    col_width = escrever_cabecalho()
    
    pdf.set_font("Arial", "", 8)
    
    for idx, row in df.iterrows():
        # Quebra de página se necessário
        if pdf.get_y() > 180:  # altura máxima antes do rodapé
            pdf.add_page()
            col_width = escrever_cabecalho()
        
        for item in row:
            pdf.cell(col_width, 8, str(item), border=1)
        pdf.cell(col_width, 8, " " * 25, border=1)  # espaço maior para assinatura
        pdf.ln()
    
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    pdf_bytes = pdf_buffer.getvalue()
    return pdf_bytes

# --- Botão para gerar PDF ---
if st.button("Gerar PDF"):
    pdf_bytes = gerar_pdf(df_filtrado, polo_selecionado, data_selecionada)
    st.download_button(
        label="Baixar PDF",
        data=pdf_bytes,
        file_name=f"Lista_Presenca_{polo_selecionado}_{data_selecionada}.pdf",
        mime="application/pdf"
    )
