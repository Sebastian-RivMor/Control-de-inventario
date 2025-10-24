import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from io import BytesIO
import streamlit as st
from src.ui.config import get_google_credentials
from google.oauth2.service_account import Credentials
import streamlit as st
import os
import json

def get_credentials_path():
    if os.path.exists("credentials.json"):
        return "credentials.json"
    else:
        creds_path = "/tmp/credentials.json"
        with open(creds_path, "w") as f:
            f.write(st.secrets["gcp_credentials"])
        return creds_path



# ====================================================
# 📁 Carpeta de Drive que contiene los inventarios
# ====================================================
FOLDER_ID = "1vHecH1CsmgSn4oYuCu2uRf0kqV1SKgOQ"

# ====================================================
# 🧠 Buscar archivos en la carpeta (para depurar)
# ====================================================
def list_drive_files():
    """Lista todos los archivos visibles en la carpeta de Drive."""
    creds_path = get_credentials_path()
    creds, SCOPES = get_google_credentials()


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
    creds_path = get_credentials_path()
    creds, SCOPES = get_google_credentials()


    service = build("drive", "v3", credentials=creds)

    query = (
        f"'{FOLDER_ID}' in parents and "
        f"(mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' or "
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
        # Mostrar todos los archivos para diagnóstico
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
    """Descarga el archivo desde Drive y lo carga como DataFrame."""
    creds_path = get_credentials_path()
    creds, SCOPES = get_google_credentials()


    service = build("drive", "v3", credentials=creds)

    df = pd.DataFrame()  # Valor por defecto seguro

    try:
        # === Caso 1: Google Sheets ===
        if mime_type == "application/vnd.google-apps.spreadsheet":
            client = gspread.authorize(creds)
            try:
                sheet = client.open_by_key(file_id).worksheet("LISTADO")
            except:
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
                status, done = downloader.next_chunk()
            buffer.seek(0)

            if file_name.endswith(".csv"):
                df = pd.read_csv(buffer)
            else:
                xls = pd.ExcelFile(buffer, engine="openpyxl")
                sheet_names = [s.strip().lower() for s in xls.sheet_names]
                if "listado" in sheet_names:
                    df = pd.read_excel(xls, sheet_name=xls.sheet_names[sheet_names.index("listado")])
                else:
                    st.warning(f"⚠️ La hoja 'LISTADO' no fue encontrada. Hojas disponibles: {xls.sheet_names}")
                    df = pd.read_excel(xls, sheet_name=xls.sheet_names[0])

    except Exception as e:
        st.error(f"❌ Error al leer el archivo: {e}")

    return df  # ✅ Siempre devuelve algo, nunca None



# ====================================================
# 🚀 Controlador principal
# ====================================================
def get_drive_data():
    """Obtiene automáticamente el archivo más reciente desde Google Drive."""
    file_id, file_name, mime_type, modified_time = get_latest_file_info()
    if not file_id:
        return pd.DataFrame(), None

    try:
        df = load_data_from_drive(file_id, mime_type, file_name)
        if df.empty:
            st.warning(f"⚠️ El archivo '{file_name}' no contiene datos o está vacío.")
        else:
            st.success(f"✅ Datos cargados correctamente desde: {file_name}")
        return df, file_name
    except Exception as e:
        st.error(f"❌ Error al cargar el archivo '{file_name}': {e}")
        return pd.DataFrame(), None