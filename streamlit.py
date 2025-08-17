import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from fpdf import FPDF
from io import BytesIO

# ---------- JSON da Service Account como dicionário ----------
SERVICE_ACCOUNT_INFO = {
    "type": "service_account",
    "project_id": "forms-automation-469318",
    "private_key_id": "027d8dc555d4ca80412d66124448f778571b4b4c",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCKvzrth7N6kjzO\ndeCblk702bUOFDHK8rDtag0PQ5pK54rp77fJ7Icp2SJsKeoK5DscAQMLZvWpdlGD\n5JLw98ZtK9G9QWORiRfp94fLWOHGFkbM/gdfDxJtQ2aeQsUrrEt3nl+asrScGdlT\nUxU30TKhL0vrA/EmWhrs+7K02HeKkBCQylMNERfB04yePxEBcCjETxxzjDR6Sk0T\ne5hJyMz4jz+iN24FM4kF689Qyr/0V4IXhZMPNM/h35XNgmmdkCuaLHMlOL7Qt9dR\nniv+qB9kfDQQgSpGoH/NA3UWc7YD3hL136KSlMbmIjQiPkIueeABVsRjMZpE0/4n\nJUVf0AVtAgMBAAECggEAJNzRxzH6mWIpDaF731p798mvtOHgqM75+tnmRlvrrmL+\nIVEzP068Sn4KCzrHl8Uzfyk1qd3c/v0UgzpDYAo0ieTOgL3SumP2Go9NYNVohrx8\naxJC2xqiBq2Vog6TXBsWod1OAUfhfGfRubWlOYM3NGPgg7w0YcAmzzfALxQkDof7\n94DQQiS5sR1EE0+EP5Itg2japBO6+acgyvvOOyAatuvUzS4tFILtt6W7wGKx7ZJZ\npcC31uMEvmtvZ212mIYs+nVDAuywHAW30CahBaegbvYAI+byV8FimedWDC2bNmjs\nNwvc58DrjagpbLGQNmt2cBvIlgj0KoQzX4SU2MEfcQKBgQC+24MEbjpohaXfQbek\nX7FUH9Qf2nq3wW9vKX/jrh1n1my5/p4WKF1Hmdhflsfq6vY6kLiZjoPerI3oM2f/\n62MvEFttQflHWr+qIBj0h1gQnPN+qyZg0wL3caXlquceWwxCiJExsyWaGJd0LT/Z\nmDZp1kNhJltt8QwpNSCYH1IgvwKBgQC6Gnqm2c+DGbsoFudopWov5G5P+hHprT0L\nKqpad9HjeLl9zW2OKeC/8YYf8vZFiUmmNYyc8Qj8eokrAGt7bWpcrvOU6TEwpKNB\n3floc1zoC11wB+tACB1Z2T/NluWy1FZGSF9g/+3ruJwcvyOBHGn4NBmNb75SntEY\nlL8KVBr40wKBgBWDMppePlEnt1GZ27Q4YQmFaOiKPMjXkdLqz5J/PqtEnQ69513C\nAPmgGqZznWcaQtTJGTWdvblso7YnjTJoes6EPnnrNMjZLr9jTMzLMJ72we9mJTZG\nso/njHZ9s/1U7+XT9OGwOq3K1c9vhkHliUSWtROPOkEDKYa/iUP8S8qLAoGAUV4u\nbjEhR6LCb57EAr8AFHx9tr4RgufZnr5CyVdGD3zDLTvaQKQSvhltmR5ziqeh6efT\n2PKSCUHSI1kFpWuLa4aavWrPtQLm1m+lEoQOBO6jJc5wjwh9PMF94fet6mhoaEZQ\nXWrIrZ2DtBXmAhdYRcsRuQM4ZYtGxMaUWIG5YT0CgYBjAc0TY9qLMijUFTnobjeA\nf83NIgiyddc5MqGQfZiHQ4hj74LHWhH9QOU89KR7tRcptAfm3qgswN8rUazerH3h\nisB7qY3gZ/yxkkKmpfkimUEhagYcIm5ILZHew2G1lOzSKUd2iEStd8AV0hBlp6wO\nhT0NDOc+G40jOtTsCkBK9A==\n-----END PRIVATE KEY-----\n",
    "client_email": "forms-automation@forms-automation-469318.iam.gserviceaccount.com",
    "client_id": "105140389217812513037",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/forms-automation%40forms-automation-469318.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

# ---------- Conexão com Google Sheets ----------
SCOPE = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPE)
gc = gspread.authorize(creds)

SHEET_KEY = "1hW17V_blimDdum1A2OotpHlBJz_9fkJJH1jIoT-2J68"
sh = gc.open_by_key(SHEET_KEY)
worksheet = sh.get_worksheet(0)
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# Remove espaços extras das colunas
df.columns = df.columns.str.strip()

# ---------- Streamlit ----------
st.title("📝 Lista de Presença - Polo e Data")

# Cria listas únicas para filtros
polos = sorted(df["Polo de Instrução"].dropna().unique())
datas = sorted(df["Data"].dropna().unique())

# Seletores
polo_selecionado = st.selectbox("Selecione o Polo de Instrução:", polos)
data_selecionada = st.selectbox("Selecione a Data:", datas)

# Filtra DataFrame
filtro = df[(df["Polo de Instrução"] == polo_selecionado) & (df["Data"] == data_selecionada)]

st.write(f"Registros filtrados: {filtro.shape[0]}")
st.dataframe(filtro)

# ---------- Função para gerar PDF ----------
def gerar_pdf(df, polo, data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Lista de Presença - {polo} - {data}", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", "B", 12)
    colunas = ["Matrícula", "Nome Completo", "Comando", "OPM", "Subunidade"]
    col_widths = [30, 60, 30, 30, 30]

    # Cabeçalho
    for i, col in enumerate(colunas):
        pdf.cell(col_widths[i], 10, col, 1, 0, "C")
    pdf.ln()

    pdf.set_font("Arial", "", 12)
    for _, row in df.iterrows():
        pdf.cell(col_widths[0], 10, str(row["Matrícula"]), 1)
        pdf.cell(col_widths[1], 10, str(row["Nome Completo"]), 1)
        pdf.cell(col_widths[2], 10, str(row["Comando"]), 1)
        pdf.cell(col_widths[3], 10, str(row["OPM"]), 1)
        pdf.cell(col_widths[4], 10, str(row["Subunidade"]), 1)
        pdf.ln()

    pdf.ln(10)
    pdf.cell(0, 10, "Assinatura:", ln=True)
    pdf.ln(10)
    pdf.cell(0, 10, "_____________________________", ln=True)

    pdf_buffer = BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer

# ---------- Botão para gerar PDF ----------
if st.button("Gerar PDF"):
    if filtro.empty:
        st.warning("Nenhum registro encontrado para os filtros selecionados.")
    else:
        pdf_bytes = gerar_pdf(filtro, polo_selecionado, data_selecionada)
        st.download_button(
            label="Download PDF",
            data=pdf_bytes,
            file_name=f"lista_presenca_{polo_selecionado}_{data_selecionada}.pdf",
            mime="application/pdf"
        )
