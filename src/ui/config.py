import json
import streamlit as st
from google.oauth2.service_account import Credentials
import os

# ================================================================
# 🔐 CONFIGURACIÓN DE CREDENCIALES Y SCOPES (segura y unificada)
# ================================================================
def get_google_credentials():
    SCOPES = [
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/spreadsheets.readonly"
    ]

    # 🔧 Forzar modo local
    if os.path.exists("credentials.json"):
        creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
        st.warning("⚠️ Usando credenciales locales (credentials.json)")
        return creds, SCOPES

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

    st.error("❌ No se encontraron credenciales válidas")
    raise FileNotFoundError