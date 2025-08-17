import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- Link CSV público ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvhc1E8BOJfuULhmzvzcxtG9PkYD2KQfpfFIYWSTUN4Jl1eJJlXg1Nmy1zBkeLbePQaKz7-jKwWwZn/pub?gid=1995854408&single=true&output=csv"

st.title("Lista de Presença com Assinatura")

# --- Função para gerar PDF ---
def gerar_pdf(df, polo, data):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()

    pdf.set_font("Arial", "", 8)
    margem = 10
    page_width = pdf.w - 2 * margem
    assinatura_width = 80

    colunas = df.columns.tolist()
    colunas.append("Assinatura")

    col_widths = []
    for col in df.columns:
        max_text = max([str(col)] + [str(val) for val in df[col]], key=lambda x: pdf.get_string_width(x))
        width = pdf.get_string_width(max_text) + 6
        col_widths.append(width)
    col_widths.append(assinatura_width)

    total_width = sum(col_widths)
    if total_width > page_width:
        scale_factor = (page_width - assinatura_width) / (total_width - assinatura_width)
        col_widths[:-1] = [w * scale_factor for w in col_widths[:-1]]

    def escrever_cabecalho():
        pdf.set_font("Arial", "B", 8)
        for i, col in enumerate(colunas):
            pdf.cell(col_widths[i], 8, col, border=1, align='C')
        pdf.ln()

    pdf.set_font("Arial", "B", 8)
    pdf.cell(0, 10, f"Lista de Presença - {polo} - {data}", ln=True, align="C")
    pdf.ln(5)
    escrever_cabecalho()

    pdf.set_font("Arial", "", 8)
    for idx, row in df.iterrows():
        if pdf.get_y() > 180:
            pdf.add_page()
            escrever_cabecalho()
        for i, col in enumerate(df.columns):
            pdf.cell(col_widths[i], 8, str(row[col]), border=1)
        pdf.cell(col_widths[-1], 8, " " * 25, border=1)
        pdf.ln()

    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    pdf_bytes = pdf_buffer.getvalue()
    return pdf_bytes

# --- Botão para gerar PDF com atualização dos dados ---
if st.button("Gerar PDF"):
    # Atualiza o CSV no clique
    df = pd.read_csv(SHEET_URL)
    df = df.drop(columns=["Carimbo de data/hora"])

    data_unica = df["Data"].unique()
    polo_unico = df["Polo de Instrução"].unique()

    # Mantém o filtro selecionado anteriormente
    data_selecionada = st.selectbox("Selecione a Data", sorted(data_unica))
    polo_selecionado = st.selectbox("Selecione o Polo de Instrução", sorted(polo_unico))

    df_filtrado = df[(df["Data"] == data_selecionada) & (df["Polo de Instrução"] == polo_selecionado)]

    pdf_bytes = gerar_pdf(df_filtrado, polo_selecionado, data_selecionada)
    st.download_button(
        label="Baixar PDF",
        data=pdf_bytes,
        file_name=f"Lista_Presenca_{polo_selecionado}_{data_selecionada}.pdf",
        mime="application/pdf"
    )
