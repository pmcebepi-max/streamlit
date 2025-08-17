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

    # Configurações
    pdf.set_font("Arial", "", 8)
    margem = 10  # margem de cada lado
    page_width = pdf.w - 2 * margem
    assinatura_width = 40  # largura fixa da coluna de assinatura em mm

    colunas = df.columns.tolist()
    colunas.append("Assinatura")  # adiciona coluna de assinatura

    # Calcula largura mínima necessária para cada coluna (com base no maior texto do cabeçalho e dados)
    col_widths = []
    for col in df.columns:
        max_text = max([str(col)] + [str(val) for val in df[col]], key=lambda x: pdf.get_string_width(x))
        width = pdf.get_string_width(max_text) + 6  # padding 3mm de cada lado
        col_widths.append(width)
    col_widths.append(assinatura_width)  # coluna de assinatura fixa

    # Ajusta as larguras proporcionais para caber na página
    total_width = sum(col_widths)
    if total_width > page_width:
        extra_space = total_width - page_width
        scale_factor = (page_width - assinatura_width) / (total_width - assinatura_width)
        col_widths[:-1] = [w * scale_factor for w in col_widths[:-1]]  # não escala assinatura

    # Função para escrever cabeçalho
    def escrever_cabecalho():
        pdf.set_font("Arial", "B", 10)
        for i, col in enumerate(colunas):
            pdf.cell(col_widths[i], 8, col, border=1, align='C')
        pdf.ln()

    # Cabeçalho do documento
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"Lista de Presença - {polo} - {data}", ln=True, align="C")
    pdf.ln(5)
    escrever_cabecalho()

    # Conteúdo da tabela
    pdf.set_font("Arial", "", 8)
    for idx, row in df.iterrows():
        if pdf.get_y() > 180:  # altura máxima antes do rodapé
            pdf.add_page()
            escrever_cabecalho()
        for i, col in enumerate(df.columns):
            pdf.cell(col_widths[i], 8, str(row[col]), border=1)
        pdf.cell(col_widths[-1], 8, " " * 25, border=1)  # assinatura
        pdf.ln()

    # Geração do PDF
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
