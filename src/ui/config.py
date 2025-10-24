import json
import streamlit as st
from google.oauth2.service_account import Credentials

# ================================================================
# 🔐 CONFIGURACIÓN DE CREDENCIALES Y SCOPES
# ================================================================
def get_google_credentials():
    """
    Retorna credenciales y scopes de Google.
    - Si se ejecuta en Streamlit Cloud, lee desde st.secrets.
    - Si se ejecuta localmente, lee desde credentials.json.
    """
    try:
        # Modo Streamlit Cloud
        creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
        scopes = st.secrets["SCOPES"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return creds, scopes
    except Exception:
        # Modo local (archivo físico)
        CREDS_FILE = "credentials.json"
        SCOPES = [
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/spreadsheets.readonly"
        ]
        creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
        return creds, SCOPES
