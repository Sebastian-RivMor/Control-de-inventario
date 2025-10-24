import json
import streamlit as st
from google.oauth2.service_account import Credentials

# ================================================================
# 🔐 CONFIGURACIÓN DE CREDENCIALES Y SCOPES (segura y unificada)
# ================================================================
def get_google_credentials():
    """
    Retorna credenciales y scopes de Google.
    - Si está en Streamlit Cloud, lee desde st.secrets["gcp_credentials"].
    - Si está local, usa el archivo credentials.json.
    """
    SCOPES = [
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/spreadsheets.readonly"
    ]

    # --- Modo Streamlit Cloud ---
    if "gcp_credentials" in st.secrets:
        try:
            creds_json = st.secrets["gcp_credentials"]
            creds_dict = json.loads(creds_json)
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            st.info("✅ Credenciales cargadas desde Streamlit Secrets")
            return creds, SCOPES
        except Exception as e:
            st.error(f"❌ Error leyendo credenciales desde st.secrets: {e}")
            raise

    # --- Modo local (solo si existe credentials.json) ---
    try:
        creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
        st.warning("⚠️ Usando credenciales locales (credentials.json)")
        return creds, SCOPES
    except FileNotFoundError:
        st.error("❌ No se encontraron credenciales en st.secrets ni en credentials.json")
        raise
