import re
import io
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st
from fpdf import FPDF

# --- Optional but recommended dependencies ---
# gspread + Google service account for Sheets access
import gspread
from google.oauth2.service_account import Credentials

# ============================================================
# 🧭 Helper functions
# ============================================================

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def extract_sheet_id(url_or_id: str) -> str:
    """Extract the Spreadsheet ID from a full Google Sheets URL or return the input if it already looks like an ID."""
    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url_or_id)
    return m.group(1) if m else url_or_id.strip()


def get_gspread_client() -> gspread.Client:
    """Authorize a gspread client using service account stored in Streamlit secrets."""
    if "gcp_service_account" not in st.secrets:
        st.stop()
    creds_dict = dict(st.secrets["gcp_service_account"])  # ensure a plain dict
    credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
    return gspread.authorize(credentials)


def load_dataframe(spreadsheet_id: str, worksheet: Optional[str] = None) -> pd.DataFrame:
    """Load the Google Sheet into a DataFrame. If worksheet is None, use the first sheet."""
    gc = get_gspread_client()
    sh = gc.open_by_key(spreadsheet_id)
    ws = sh.worksheet(worksheet) if worksheet else sh.get_worksheet(0)
    rows = ws.get_all_records()
    df = pd.DataFrame(rows)
    # Standardize expected columns (strip spaces, consistent names)
    df.columns = [c.strip() for c in df.columns]
    return df


def coerce_date(series: pd.Series) -> pd.Series:
    """Attempt to parse dates robustly (supports dd/mm/yyyy, yyyy-mm-dd, etc.)."""
    # Try common dayfirst formats first, then fallback
    def _parse(x):
        if pd.isna(x):
            return pd.NaT
        # Already a datetime?
        if isinstance(x, (pd.Timestamp, datetime)):
            return pd.to_datetime(x)
        s = str(x).strip()
        # Replace commas or dots if needed
        s = s.replace(",", "/").replace(".", "/")
        try:
            return pd.to_datetime(s, dayfirst=True, errors="raise")
        except Exception:
            return pd.to_datetime(s, dayfirst=False, errors="coerce")

    parsed = series.apply(_parse)
    return parsed.dt.tz_localize("America/Fortaleza", nonexistent="shift_forward", ambiguous="NaT", errors="ignore") if hasattr(parsed, "dt") else parsed


# ============================================================
# 🧾 PDF generation
# ============================================================

class AttendancePDF(FPDF):
    def header(self):
        # Title will be set by the caller; keep header minimal for more rows per page
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}", 0, 0, "C")


def make_attendance_pdf(
    df: pd.DataFrame,
    polo: str,
    date_display: str,
    sheet_title: str,
) -> bytes:
    """Build a PDF bytes object with attendance rows and signature lines."""
    pdf = AttendancePDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)

    # Styling
    left_margin = 12
    right_margin = 12
    pdf.set_margins(left=left_margin, top=12, right=right_margin)

    # Column configuration
    # [ (header, width in mm, alignment) ]  -> total should be <= 210 - margins
    cols = [
        ("#", 10, "C"),
        ("Nome Completo", 75, "L"),
        ("Matrícula", 30, "C"),
        ("OPM", 23, "C"),
        ("Subunidade", 30, "C"),
        ("Comando", 25, "C"),
        ("Assinatura", 0, "L"),  # 0 uses the remaining width
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
                "",  # assinatura em branco
            ]
            for (header, w, align), val in zip(cols, values):
                pdf.cell(w, row_h, val, border=1, align=align)
            pdf.ln(row_h)

    # Start PDF
    pdf.add_page()
    page_title()
    header_row()
    body_rows()

    # Extra space for coordinator signature
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(90, 8, "Assinatura do Coordenador:", border=0)
    pdf.cell(0, 8, "______________________________________________", border=0, ln=1)

    return pdf.output(dest="S").encode("latin1")


# ============================================================
# 🚀 Streamlit UI
# ============================================================

st.set_page_config(page_title="Lista de Presença (Sheets → PDF)", page_icon="📝", layout="centered")

st.title("📝 Gerar Lista de Presença em PDF a partir do Google Sheets")

with st.expander("▶️ Como configurar (primeira vez)", expanded=False):
    st.markdown(
        """
        1. Crie uma **Service Account** no Google Cloud e faça o download do JSON.
        2. Em **Streamlit Cloud** ou localmente, salve o conteúdo do JSON em `secrets`:
           ```toml
           # .streamlit/secrets.toml
           [gcp_service_account]
           type = "service_account"
           project_id = "..."
           private_key_id = "..."
           private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
           client_email = "...@....iam.gserviceaccount.com"
           client_id = "..."
           token_uri = "https://oauth2.googleapis.com/token"
           ```
        3. Compartilhe a **planilha** com o email da Service Account (permissão *Leitor*). 
        4. Cole abaixo a **URL** da planilha (ou apenas o ID) e informe o nome da guia (aba) se necessário.
        """
    )

# Inputs for sheet access
url_default = st.text_input("URL ou ID da planilha", placeholder="cole aqui a URL do Google Sheets")
worksheet_name = st.text_input("Nome da guia (opcional)", placeholder="ex.: Respostas do formulário 1")

load_button = st.button("Carregar dados")

if load_button and url_default:
    try:
        sheet_id = extract_sheet_id(url_default)
        df = load_dataframe(sheet_id, worksheet_name or None)

        # Expected columns
        expected = [
            "Comando",
            "OPM",
            "Subunidade",
            "Polo de Instrução",
            "Data",
            "Matrícula",
            "Nome Completo",
        ]
        missing = [c for c in expected if c not in df.columns]
        if missing:
            st.error(
                "Colunas ausentes na planilha: " + ", ".join(missing) +
                "\n\nColunas encontradas: " + ", ".join(df.columns)
            )
            st.stop()

        # Normalize date
        df["_DataParsed"] = coerce_date(df["Data"]).dt.date

        # Sidebar filters
        st.success("Dados carregados com sucesso! Configure os filtros abaixo:")
        polos = sorted([p for p in df["Polo de Instrução"].dropna().astype(str).unique()])
        polo_sel = st.selectbox("Polo de Instrução", polos)

        # Build list of available dates for selected polo
        df_polo = df[df["Polo de Instrução"].astype(str) == str(polo_sel)].copy()
        unique_dates = sorted([d for d in df_polo["_DataParsed"].dropna().unique()])

        if not unique_dates:
            st.warning("Nenhuma data válida encontrada para este Polo. Verifique a coluna 'Data'.")
            st.stop()

        date_sel = st.date_input("Data", value=unique_dates[0], min_value=min(unique_dates), max_value=max(unique_dates))

        # Filter by polo + date
        mask = (df["Polo de Instrução"].astype(str) == str(polo_sel)) & (df["_DataParsed"] == pd.to_datetime(date_sel).date())
        df_filtered = df.loc[mask, expected].copy()

        st.subheader("Prévia dos inscritos")
        st.dataframe(df_filtered, use_container_width=True)
        st.caption(f"Total de inscritos para {polo_sel} em {date_sel:%d/%m/%Y}: {len(df_filtered)}")

        # Generate PDF
        if st.button("Gerar PDF da Lista de Presença"):
            if df_filtered.empty:
                st.warning("Nenhum registro para os filtros escolhidos.")
            else:
                # Ensure column with both accented and plain keys
                if "Matrícula" not in df_filtered.columns and "Matricula" in df_filtered.columns:
                    df_filtered.rename(columns={"Matricula": "Matrícula"}, inplace=True)

                date_display = date_sel.strftime("%d/%m/%Y")
                pdf_bytes = make_attendance_pdf(
                    df_filtered,
                    polo=polo_sel,
                    date_display=date_display,
                    sheet_title=worksheet_name or "",
                )
                st.download_button(
                    label="⬇️ Baixar PDF",
                    data=pdf_bytes,
                    file_name=f"lista_presenca_{polo_sel}_{date_sel:%Y%m%d}.pdf",
                    mime="application/pdf",
                )

    except Exception as e:
        st.error(f"Falha ao carregar: {e}")
        st.stop()


st.divider()

st.caption(
    "Dica: se as datas não forem reconhecidas, verifique se a coluna 'Data' está como texto no formato 'dd/mm/aaaa' ou 'aaaa-mm-dd'."
)
