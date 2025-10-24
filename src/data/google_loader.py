import os
import json
from io import BytesIO

import pandas as pd
import gspread
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Si ya tienes un helper para credenciales, usa ese; de lo contrario, estas funciones manejan local/toml
from google.oauth2.service_account import Credentials


# ========= Helpers de credenciales =========
def get_credentials_path():
    """
    Retorna ruta a credentials.json.
    - En local: usa credentials.json del proyecto.
    - En Streamlit Cloud: escribe st.secrets["gcp_credentials"] a /tmp/credentials.json
    """
    if os.path.exists("credentials.json"):
        return "credentials.json"
    else:
        creds_path = "/tmp/credentials.json"
        # En secrets debe estar el JSON completo como string
        if "gcp_credentials" not in st.secrets:
            raise RuntimeError("No se encontró 'gcp_credentials' en st.secrets.")
        with open(creds_path, "w") as f:
            f.write(st.secrets["gcp_credentials"])
        return creds_path


def get_google_credentials():
    """
    Crea objeto Credentials con los SCOPES necesarios para Drive y Sheets.
    """
    creds_path = get_credentials_path()
    SCOPES = [
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/spreadsheets.readonly",
    ]
    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    return creds, SCOPES


# ====================================================
# 📁 Carpeta de Drive que contiene los inventarios
# ====================================================
FOLDER_ID = "1vHecH1CsmgSn4oYuCu2uRf0kqV1SKgOQ"


# ====================================================
# 🧠 Buscar archivos en la carpeta (para depurar)
# ====================================================
def list_drive_files():
    """Lista todos los archivos visibles en la carpeta de Drive."""
    creds, _ = get_google_credentials()
    service = build("drive", "v3", credentials=creds)

    results = service.files().list(
        q=f"'{FOLDER_ID}' in parents",
        fields="files(id, name, mimeType, modifiedTime)"
    ).execute()

    files = results.get("files", [])
    if not files:
        st.error("⚠️ No se encontraron archivos en la carpeta. Verifica el ID o los permisos.")
        return []

    st.write("📂 Archivos encontrados en Google Drive:")
    for f in files:
        st.write(f"• {f['name']} — {f['mimeType']} — {f['modifiedTime']}")
    return files


# ====================================================
# 🔍 Buscar el archivo más reciente compatible
# ====================================================
def get_latest_file_info():
    """Busca el archivo más reciente (.xlsx, .xls, .csv o Google Sheet)."""
    creds, _ = get_google_credentials()
    service = build("drive", "v3", credentials=creds)

    query = (
        f"'{FOLDER_ID}' in parents and ("
        f"mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' or "
        f"mimeType='application/vnd.ms-excel' or "
        f"mimeType='text/csv' or "
        f"mimeType='application/vnd.google-apps.spreadsheet')"
    )

    results = service.files().list(
        q=query,
        orderBy="modifiedTime desc",
        pageSize=5,
        fields="files(id, name, mimeType, modifiedTime)"
    ).execute()

    files = results.get("files", [])
    if not files:
        st.warning("⚠️ No se encontraron archivos Excel ni Google Sheets en la carpeta.")
        list_drive_files()
        return None, None, None, None

    latest = files[0]
    st.info(f"📄 Cargando archivo más reciente: **{latest['name']}** (modificado {latest['modifiedTime'][:10]})")
    return latest["id"], latest["name"], latest["mimeType"], latest["modifiedTime"]


# ====================================================
# 📥 Descargar y leer el archivo
# ====================================================
@st.cache_data(show_spinner=False)
def load_data_from_drive(file_id, mime_type, file_name):
    """
    Descarga el archivo desde Drive y lo carga como DataFrame.
    - Si es Google Sheet: intenta hoja 'LISTADO', si no, la primera hoja.
    - Si es Excel/CSV: intenta hoja 'LISTADO' (case-insensitive, strip), si no, la primera hoja.
    - Limpia encabezados (solo strip de espacios). NO cambia mayúsc/minúsc para no romper lógica externa.
    """
    creds, _ = get_google_credentials()
    service = build("drive", "v3", credentials=creds)

    df = pd.DataFrame()  # fallback seguro

    try:
        # === Caso 1: Google Sheets ===
        if mime_type == "application/vnd.google-apps.spreadsheet":
            client = gspread.authorize(creds)
            try:
                sheet = client.open_by_key(file_id).worksheet("LISTADO")
            except Exception:
                sheet = client.open_by_key(file_id).sheet1
            data = sheet.get_all_records()
            df = pd.DataFrame(data)

        # === Caso 2: Excel o CSV ===
        else:
            request = service.files().get_media(fileId=file_id)
            buffer = BytesIO()
            downloader = MediaIoBaseDownload(buffer, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            buffer.seek(0)

            if file_name.lower().endswith(".csv"):
                df = pd.read_csv(buffer)
            else:
                xls = pd.ExcelFile(buffer, engine="openpyxl")
                sheet_names = [s.strip() for s in xls.sheet_names]
                sheet_names_lower = [s.lower() for s in sheet_names]

                # Buscar hoja que contenga las palabras clave "listado", "stock" o "inventario"
                keywords = ["listado", "stock", "inventario"]
                found_sheet = None
                for name in sheet_names:
                    name_lower = name.strip().lower()
                    if any(k in name_lower for k in keywords):
                        found_sheet = name
                        break

                if found_sheet:
                    st.info(f"📄 Usando hoja detectada automáticamente: {found_sheet}")
                    df = pd.read_excel(xls, sheet_name=found_sheet)
                else:
                    df = pd.read_excel(xls, sheet_name=xls.sheet_names[0])


        # 🧹 Normalizar encabezados (solo quitar espacios)
        df.columns = df.columns.str.strip()

    except Exception as e:
        st.error(f"❌ Error al leer el archivo: {e}")

    return df  # siempre DataFrame


# ====================================================
# 🚀 Controlador principal
# ====================================================
def get_drive_data():
    """Obtiene automáticamente el archivo más reciente desde Google Drive."""
    file_id, file_name, mime_type, _ = get_latest_file_info()
    if not file_id:
        return pd.DataFrame(), None

    try:
        df = load_data_from_drive(file_id, mime_type, file_name)
        if df.empty:
            st.warning(f"⚠️ El archivo '{file_name}' no contiene datos o está vacío.")
        return df, file_name
    except Exception as e:
        st.error(f"❌ Error al cargar el archivo '{file_name}': {e}")
        return pd.DataFrame(), None
