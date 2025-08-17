import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- Link CSV público ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvhc1E8BOJfuULhmzvzcxtG9PkYD2KQfpfFIYWSTUN4Jl1eJJlXg1Nmy1zBkePQaKz7-jKwWwZn/pub?gid=1995854408&single=true&output=csv"

df = pd.read_csv(SHEET_URL)
df = df.drop(columns=["Carimbo de data/hora"])

st.title("Lista de Presença com Assinatura")

# --- Formulário de filtros ---
with st.form("filtros_form"):
    data_unica = df["Data"].unique()
    polo_unico = df["Polo de Instrução"].unique()

    data_selecionada = st.selectbox("Selecione a Data", sorted(data_unica))
    polo_selecionado = st.selectbox("Selecione o Polo de Instrução", sorted(polo_unico))
    
    submit_button = st.form_submit_button("Gerar PDF")

# --- Gerar PDF somente após enviar o formulário ---
if submit_button:
    df_filtrado = df[(df["Data"] == data_selecionada) & (df["Polo de Instrução"] == polo_selecionado)]
    st.write(f"{len(df_filtrado)} registros encontrados")
    st.dataframe(df_filtrado)
    
    # --- Função para gerar PDF ---
    def gerar_pdf(df, polo, data):
        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.set_auto_page_break(auto=True, margin=10)
        pdf.add_page()
        
        # Título
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"Lista de Presença - {polo} - {data}", ln=True, align="C")
        pdf.ln(5)
        
        # Colunas
        colunas = df.columns.tolist()
        largura_total = pdf.w - 20  # largura da página menos margens
        largura_assinatura = 50     # coluna assinatura maior
        largura_outras = (largura_total - largura_assinatura) / len(colunas)
        
        # Função para escrever cabeçalho
        def escrever_cabecalho():
            pdf.set_font("Arial", "B", 10)
            for col in colunas:
                pdf.cell(largura_outras, 8, col, border=1, align='C')
            pdf.cell(largura_assinatura, 8, "Assinatura", border=1, align='C')
            pdf.ln()
        
        escrever_cabecalho()
        
        pdf.set_font("Arial", "", 8)
        
        for idx, row in df.iterrows():
            if pdf.get_y() > 180:  # quebra de página
                pdf.add_page()
                escrever_cabecalho()
            
            for item in row:
                pdf.cell(largura_outras, 8, str(item), border=1)
            pdf.cell(largura_assinatura, 8, " " * 25, border=1)  # espaço para assinatura
            pdf.ln()
        
        pdf_buffer = io.BytesIO()
        pdf.output(pdf_buffer)
        pdf_bytes = pdf_buffer.getvalue()
        return pdf_bytes
    
    # --- Botão para download do PDF ---
    pdf_bytes = gerar_pdf(df_filtrado, polo_selecionado, data_selecionada)
    st.download_button(
        label="Baixar PDF",
        data=pdf_bytes,
        file_name=f"Lista_Presenca_{polo_selecionado}_{data_selecionada}.pdf",
        mime="application/pdf"
    )
