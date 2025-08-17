import re
import io
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st
from fpdf import FPDF

# --- Google Sheets ---
import gspread
from google.oauth2.service_account import Credentials

# ============================================================
# Configurações fixas da planilha
# ============================================================

SHEET_ID = "1hW17V_blimDdum1A2OotpHlBJz_9fkJJH1jIoT-2J68"
WORKSHEET_NAME = None   # ou "Respostas do formulário 1" se quiser forçar uma aba específica

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

# ============================================================
# Helpers
# ============================================================

def get_gspread_client() -> gspread.Client:
    if "gcp_service_account" not in st.secrets:
        st.stop()
    creds_dict = dict(st.secrets["gcp_service_account"])
    credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
    return gspread.authorize(credentials)

def load_dataframe() -> pd.DataFrame:
    gc = get_gspread_client()
    sh = gc.open_by_key(SHEET_ID)
    ws = sh.worksheet(WORKSHEET_NAME) if WORKSHEET_NAME else sh.get_worksheet(0)
    rows = ws.get_all_records()
    df = pd.DataFrame(rows)
    df.columns = [c.strip() for c in df.columns]
    return df

def coerce_date(series: pd.Series) -> pd.Series:
    def _parse(x):
        if pd.isna(x):
            return pd.NaT
        if isinstance(x, (pd.Timestamp, datetime)):
            return pd.to_datetime(x)
        s = str(x).strip().replace(",", "/").replace(".", "/")
        try:
            return pd.to_datetime(s, dayfirst=True, errors="raise")
        except Exception:
            return pd.to_datetime(s, dayfirst=False, errors="coerce")
    parsed = series.apply(_parse)
    return parsed.dt.date

# ============================================================
# PDF
# ============================================================

class AttendancePDF(FPDF):
    def header(self): pass
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}", 0, 0, "C")

def make_attendance_pdf(df, polo, date_display, sheet_title):
    pdf = AttendancePDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.set_margins(left=12, top=12, right=12)

    cols = [
        ("#", 10, "C"),
        ("Nome Completo", 75, "L"),
        ("Matrícula", 30, "C"),
        ("OPM", 23, "C"),
        ("Subunidade", 30, "C"),
        ("Comando", 25, "C"),
        ("Assinatura", 0, "L"),
    ]

    def page_title():
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 8, "LISTA DE PRESENÇA", ln=1, align="C")
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 6, f"Polo de Instrução: {polo}", ln=1)
        pdf.cell(0, 6, f"Data: {date_display}", ln=1)
        if sheet_title:
            pdf.cell(0, 6, f"Fonte: {sheet_title}", ln=1)
        pdf.ln(2)

    def header_row():
        pdf.set_font("Helvetica", "B", 10)
        for header, w, align in cols:
            pdf.cell(w, 8, header, border=1, align=align)
        pdf.ln(8)

    def body_rows():
        pdf.set_font("Helvetica", "", 10)
        row_h = 10
        for i, row in enumerate(df.itertuples(index=False), start=1):
            values = [
                str(i),
                str(getattr(row, "Nome Completo", "")),
                str(getattr(row, "Matrícula", getattr(row, "Matricula", ""))),
                str(getattr(row, "OPM", "")),
                str(getattr(row, "Subunidade", "")),
                str(getattr(row, "Comando", "")),
                "",
            ]
            for (header, w, align), val in zip(cols, values):
                pdf.cell(w, row_h, val, border=1, align=align)
            pdf.ln(row_h)

    pdf.add_page()
    page_title()
    header_row()
    body_rows()

    pdf.ln(6)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(90, 8, "Assinatura do Coordenador:", border=0)
    pdf.cell(0, 8, "______________________________________________", border=0, ln=1)

    return pdf.output(dest="S").encode("latin1")

# ============================================================
# UI
# ============================================================

st.set_page_config(page_title="Lista de Presença", page_icon="📝", layout="centered")
st.title("📝 Lista de Presença - Polo e Data")

try:
    df = load_dataframe()

    expected = ["Comando","OPM","Subunidade","Polo de Instrução","Data","Matrícula","Nome Completo"]
    missing = [c for c in expected if c not in df.columns]
    if missing:
        st.error("Colunas ausentes: " + ", ".join(missing))
        st.stop()

    df["_DataParsed"] = coerce_date(df["Data"])

    polos = sorted(df["Polo de Instrução"].dropna().astype(str).unique())
    polo_sel = st.selectbox("Polo de Instrução", polos)

    df_polo = df[df["Polo de Instrução"].astype(str) == str(polo_sel)]
    unique_dates = sorted(df_polo["_DataParsed"].dropna().unique())

    date_sel = st.date_input("Data", value=unique_dates[0], min_value=min(unique_dates), max_value=max(unique_dates))

    mask = (df["Polo de Instrução"].astype(str) == str(polo_sel)) & (df["_DataParsed"] == pd.to_datetime(date_sel).date())
    df_filtered = df.loc[mask, expected].copy()

    st.subheader("Prévia dos inscritos")
    st.dataframe(df_filtered, use_container_width=True)

    if st.button("Gerar PDF da Lista de Presença"):
        if df_filtered.empty:
            st.warning("Nenhum registro encontrado.")
        else:
            date_display = date_sel.strftime("%d/%m/%Y")
            pdf_bytes = make_attendance_pdf(df_filtered, polo_sel, date_display, WORKSHEET_NAME or "")
            st.download_button(
                label="⬇️ Baixar PDF",
                data=pdf_bytes,
                file_name=f"lista_presenca_{polo_sel}_{date_sel:%Y%m%d}.pdf",
                mime="application/pdf",
            )

except Exception as e:
    st.error(f"Erro: {e}")
