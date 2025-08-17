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
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()

    pdf.set_font("Arial", "", 8)
    page_width = pdf.w - 20  # margem 10mm cada lado
    
    colunas = df.columns.tolist()
    assinatura_col = "Assinatura"
    colunas.append(assinatura_col)

    # Calcula a largura de cada coluna
    col_widths = []
    for col in colunas:
        if col == assinatura_col:
            max_text = " " * 25  # espaço para assinatura
        else:
            max_text = max([str(val) for val in df[col]] + [col], key=lambda x: len(str(x)))
        width = pdf.get_string_width(str(max_text)) + 6  # padding
        col_widths.append(width)
    
    # Ajusta proporcionalmente para caber na página
    total_width = sum(col_widths)
    if total_width > page_width:
        ratio = page_width / total_width
        col_widths = [w * ratio for w in col_widths]

    # Função para escrever cabeçalho
    def escrever_cabecalho():
        pdf.set_font("Arial", "B", 10)
        for i, col in enumerate(colunas):
            pdf.cell(col_widths[i], 8, col, border=1, align='C')
        pdf.ln()
    
    # Cabeçalho principal
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"Lista de Presença - {polo} - {data}", ln=True, align="C")
    pdf.ln(5)
    escrever_cabecalho()
    
    # Conteúdo
    pdf.set_font("Arial", "", 8)
    for idx, row in df.iterrows():
        if pdf.get_y() > 180:  # altura máxima antes do rodapé
            pdf.add_page()
            escrever_cabecalho()
        for i, col in enumerate(df.columns):
            pdf.cell(col_widths[i], 8, str(row[col]), border=1)
        pdf.cell(col_widths[-1], 8, " " * 25, border=1)  # assinatura
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
