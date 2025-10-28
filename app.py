# app.py
import os, sys
import streamlit as st
import plotly.io as pio
import importlib.util

pio.templates.default = "plotly_white"

# === Fix de importaciones si Streamlit no detecta src/ ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# === Importaciones del proyecto ===
from src.data.google_loader import get_drive_data
from src.ui.layout import configurar_pagina, seleccionar_almacen
from src.logic.escaneo_logic import procesar_escaneo
from src.reports.eri_report import mostrar_reporte_eri
from src.reports.eru_report import mostrar_reporte_eru
from src.reports.general_report import mostrar_reporte_general

# === Configuración de página ===
configurar_pagina()

# === Carga automática de datos desde Google Drive ===
st.sidebar.header("📂 Datos desde Google Drive")
data, file_name = get_drive_data()

if data.empty:
    st.warning("⚠️ No hay datos disponibles. Verifica la carpeta en Drive o tus credenciales.")
    st.stop()

st.success(f"✅ Datos cargados correctamente desde: {file_name}")

# === Selección de almacén ===
almacen_seleccionado, df_filtrado, stock_teorico_eri = seleccionar_almacen(data)

if df_filtrado.empty:
    st.warning("⚠️ No hay datos para el almacén seleccionado.")
    st.stop()

# === Escaneo de códigos ===
procesar_escaneo(stock_teorico_eri)

# === Reporte ERI ===
mostrar_reporte_eri(stock_teorico_eri)

# === Reporte ERU ===
mostrar_reporte_eru(stock_teorico_eri)

# === Visualización general (modal flotante) ===
mostrar_reporte_general()


if importlib.util.find_spec("kaleido") is None:
    st.error("❌ Kaleido no está instalado correctamente.")
else:
    st.success("✅ Kaleido está instalado y listo.")