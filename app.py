# app.py
import os, sys
import streamlit as st

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


# import streamlit as st
# import pandas as pd
# import gspread
# from google.oauth2.service_account import Credentials
# import plotly.express as px
# import plotly.io as pio # Para exportar gráficos a imagen
# import re
# # import xlsxwrite
# import streamlit_modal
# from streamlit_modal import Modal
# import io


# # === Configuración de Google Sheets ===
# SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
# CREDS_FILE = "credentials.json"

# @st.cache_resource
# def load_data_from_sheets():
#     creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
#     client = gspread.authorize(creds)
#     sheet = client.open("Inventario_ERI").worksheet("Data_Principal")
#     data = sheet.get_all_records()
#     return pd.DataFrame(data)

# # === Interfaz de la app ===
# st.set_page_config(page_title="📊 ERI & ERU - Exactitud de Inventario", layout="wide")
# st.title("📊 Sistema ERI & ERU - Exactitud de Registro de Inventario y Ubicación")

# # Cargar datos
# try:
#     df_raw = load_data_from_sheets()
#     st.success("✅ Datos cargados desde Google Sheets")
# except Exception as e:
#     st.error(f"❌ Error al cargar datos: {e}")
#     st.stop()

# # Limpiar y normalizar nombres de columnas
# df_raw.columns = df_raw.columns.str.strip().str.upper()

# # Validar columnas
# required_cols = ["ALMACEN_NOMBRE", "PRODUCTO_CODIGO", "REFERENCIA1", "STOCK_REFERENCIAUBICACION", "UBICACION_NOMBRE"]
# missing_cols = [col for col in required_cols if col not in df_raw.columns]

# if missing_cols:
#     st.error(f"❌ Faltan columnas: {missing_cols}. Las columnas disponibles son: {list(df_raw.columns)}")
#     st.stop()
# else:
#     st.success("✅ Todas las columnas requeridas están presentes.")

# # Paso 1: Seleccionar almacén
# almacenes = sorted(df_raw["ALMACEN_NOMBRE"].dropna().unique())
# almacen_seleccionado = st.selectbox("📍 Seleccionar Almacén", almacenes)

# # Filtrar por almacén
# df_filtrado = df_raw[df_raw["ALMACEN_NOMBRE"] == almacen_seleccionado].copy()

# # Crear clave única concatenada: PRODUCTO_CODIGO + "_" + REFERENCIA1 (para ERI)
# df_filtrado["clave_teorica_eri"] = (
#     df_filtrado["PRODUCTO_CODIGO"].astype(str) + df_filtrado["REFERENCIA1"].astype(str)
# )

# # Crear clave única concatenada: PRODUCTO_CODIGO + "_" + REFERENCIA1 + UBICACION_NOMBRE (para ERU)
# df_filtrado["clave_teorica_eru"] = df_filtrado["clave_teorica_eri"] + df_filtrado["UBICACION_NOMBRE"].astype(str)

# # Agrupar stock teórico por la clave ERI (producto + ref)
# stock_teorico_eri = (
#     df_filtrado.groupby("clave_teorica_eri")["STOCK_REFERENCIAUBICACION"]
#     .sum()
#     .round(3)
#     .reset_index()
#     .rename(columns={"STOCK_REFERENCIAUBICACION": "stock_teorico"})
# )

# # Agrupar stock teórico por la clave ERU (producto + ref + ubicación)
# # Agrupar también la ubicación teórica por la clave ERI
# ubicaciones_por_eri = df_filtrado.groupby("clave_teorica_eri")["UBICACION_NOMBRE"].apply(lambda x: list(x.unique())).reset_index()

# # Combinar stock y ubicaciones teóricas
# stock_teorico_eri = stock_teorico_eri.merge(ubicaciones_por_eri, on="clave_teorica_eri", how="left")

# st.info(f"📦 {len(stock_teorico_eri)} ítems teóricos en {almacen_seleccionado}")

# # --- NUEVA SECCIÓN: Escaneo para ERI y ERU ---
# st.subheader("🔍 Escaneo Físico (ERI y ERU)")

# # Patrones de ubicación (definidos aquí para reutilizar)
# ubicacion_pattern = r'R\d{1,3}[A-Z]-[A-Z]-\d{1,3}$'
# ubicacion_pattern_alt = r'R\d{1,3}[A-Z]-[A-Z]-[A-Z]$'
# ubicacion_pattern_alt2 = r'R\d{1,3}-[A-Z]-\d{1,3}$'
# ubicacion_pattern_alt3 = r'R\d{1,3}-[A-Z]-[A-Z]$'

# # Callback para procesar el escaneo
# def procesar_escaneo():
#     codigo_ingresado = st.session_state.get("codigo_escaneado_form", "")
#     if codigo_ingresado:
#         # Intentar desconcatenar como si fuera ERU
#         clave_producto_ref, ubicacion_escaneada = desconcatenar_producto_ref(codigo_ingresado, stock_teorico_eri['UBICACION_NOMBRE'].explode().unique())

#         if clave_producto_ref and ubicacion_escaneada:
#             # Es un código de ERU (producto+ref+ubicación)
#             st.session_state["escaneos_eru"].append(codigo_ingresado)
#             # Opcional: Mostrar mensaje de éxito para ERU
#             st.session_state["mensaje_escaneo"] = f"✅ Escaneado (ERU): {codigo_ingresado}"

#             # AHORA: Procesar también como ERI
#             # Agregar la parte de producto+referencia a los escaneos ERI
#             st.session_state["escaneos_eri"].append(clave_producto_ref)
#             # Opcional: No mostrar mensaje adicional para ERI aquí, o hacerlo solo si es diferente del ERU

#         else:
#             # No es un código ERU válido, puede ser solo ERI o inválido
#             # Opcional: Verificar si coincide con alguna clave_teorica_eri directamente
#             # Por ahora, lo dejamos como escaneo "no ERU", pero puedes implementar lógica adicional si es necesario
#             st.session_state["mensaje_escaneo"] = f"⚠️ Código escaneado no coincide con formato ERU esperado: {codigo_ingresado}"

#         # Limpiar el campo en el estado de sesión
#         st.session_state["codigo_escaneado_form"] = ""

# # Función para desconcatenar producto+ref de un código ERU
# # Función para desconcatenar producto+ref de un código ERU
# def desconcatenar_producto_ref(clave_completa, ubicaciones_teoricas):
#     # Iterar sobre las longitudes posibles de ubicación (asumiendo que no son extremadamente largas)
#     # De mayor a menor para evitar ambigüedades (ej. R10-C-2 vs R10-C-27)
#     for ub_teorica in sorted(ubicaciones_teoricas, key=len, reverse=True):
#         if clave_completa.endswith(ub_teorica):
#             # Extraer la parte de producto+referencia
#             parte_producto_ref = clave_completa[:-len(ub_teorica)]
#             # Crear la clave teórica agregando el guion bajo
#             # Esto asume que la parte_producto_ref tiene la estructura PRODUCTO_CODIGO + REFERENCIA1
#             # Podemos intentar encontrar el punto donde termina el PRODUCTO_CODIGO
#             # Usaremos un bucle para probar diferentes longitudes
#             for i in range(len(parte_producto_ref)):
#                 producto_codigo = parte_producto_ref[:i]
#                 referencia1 = parte_producto_ref[i:]
#                 # Verificar si esta combinación existe en la data teórica
#                 clave_teorica = producto_codigo + "_" + referencia1
#                 if clave_teorica in stock_teorico_eri['clave_teorica_eri'].values:
#                     return clave_teorica, ub_teorica
#     # Si no se encuentra coincidencia con ubicaciones conocidas, intentar buscar patrón
#     # Buscamos una clave_teorica_eri que esté contenida al inicio
#     for _, row in stock_teorico_eri.iterrows():
#         if clave_completa.startswith(row['clave_teorica_eri']):
#             # Extraer la parte de ubicación
#             ubicacion_extraida = clave_completa[len(row['clave_teorica_eri']):]
#             # Verificar si esta ubicación extraída es plausible (patrón)
#             if (re.search(ubicacion_pattern, ubicacion_extraida) or
#                 re.search(ubicacion_pattern_alt, ubicacion_extraida) or
#                 re.search(ubicacion_pattern_alt2, ubicacion_extraida) or
#                 re.search(ubicacion_pattern_alt3, ubicacion_extraida)):
#                 return row['clave_teorica_eri'], ubicacion_extraida
#     return None, None # No se pudo desconcatenar


# # Inicializar session_state para escaneos ERI y ERU si no existen
# if "escaneos_eri" not in st.session_state:
#     st.session_state["escaneos_eri"] = []
# if "escaneos_eru" not in st.session_state:
#     st.session_state["escaneos_eru"] = []

# # Inicializar mensaje de escaneo si no existe
# if "mensaje_escaneo" not in st.session_state:
#     st.session_state["mensaje_escaneo"] = ""

# # Mostrar mensaje de escaneo si existe
# if st.session_state["mensaje_escaneo"]:
#     st.success(st.session_state["mensaje_escaneo"])
#     # Limpiar el mensaje después de mostrarlo
#     st.session_state["mensaje_escaneo"] = ""

# # Crear formulario para el escaneo
# with st.form(key="form_escaneo"):
#     # Campo de texto para escanear
#     # La key es crucial para que el form la maneje correctamente
#     codigo_escaneado = st.text_input(
#         "Escanee un código de barras (ERI o ERU)",
#         key="codigo_escaneado_form" # Esta key es la que se usa en el callback
#     )
#     # Botón de envío del formulario
#     submit_button = st.form_submit_button(label="Agregar Escaneo", on_click=procesar_escaneo)

# # Botón para limpiar escaneos (opcional)
# if st.button("🗑️ Limpiar Todos los Escaneos"):
#     st.session_state["escaneos_eri"] = []
#     st.session_state["escaneos_eru"] = []
#     st.success("Escaneos limpiados")

# # --- FIN NUEVA SECCIÓN ---

# # Mostrar escaneos acumulados (ERI)
# if st.session_state["escaneos_eri"]:
#     st.subheader("📊 Escaneos ERI Acumulados")
#     st.write(f"Total de escaneos ERI: {len(st.session_state['escaneos_eri'])}")

#     # Convertir los escaneos ERI a un DataFrame y contar cuántas veces se ha escaneado cada código
#     df_escaneos_eri = pd.DataFrame(st.session_state["escaneos_eri"], columns=["clave_escaneada_eri"])
#     stock_fisico_eri = (
#         df_escaneos_eri["clave_escaneada_eri"]
#         .value_counts()
#         .reset_index()
#     )
#     stock_fisico_eri.columns = ["clave_escaneada_eri", "stock_fisico"]
#     st.dataframe(stock_fisico_eri, use_container_width=True)

#     # Paso 3: Cruce ERI - Unir stock teórico con stock físico escaneado
#     merged_eri = pd.merge(
#         stock_teorico_eri,
#         stock_fisico_eri,
#         left_on="clave_teorica_eri",
#         right_on="clave_escaneada_eri",
#         how="outer"
#     ).fillna(0) # Rellenar NaN con 0 para valores no encontrados en uno u otro lado

#     # Calcular diferencia
#     merged_eri["diferencia"] = merged_eri["stock_fisico"] - merged_eri["stock_teorico"]

#     # Calcular estado
#     merged_eri["estado"] = merged_eri["diferencia"].apply(
#         lambda x: "OK" if x == 0 else ("Sobrante" if x > 0 else "Faltante")
#     )

#     # Calcular ERI
#     total_items_eri = len(merged_eri)
#     items_con_error_eri = len(merged_eri[merged_eri["diferencia"] != 0])
#     exactitud_eri = (1 - items_con_error_eri / total_items_eri) * 100

#     # Reporte ERI
#     st.subheader("📈 Reporte ERI")
#     col1, col2, col3 = st.columns(3)
#     col1.metric("Exactitud ERI", f"{exactitud_eri:.2f}%")
#     col2.metric("Ítems Correctos ERI", len(merged_eri[merged_eri["estado"] == "OK"]))
#     col3.metric("Ítems con Error ERI", items_con_error_eri)

#     # Gráfico ERI
#     fig_eri = px.pie(
#         merged_eri,
#         names="estado",
#         title="Distribución ERI",
#         color_discrete_map={"OK": "green", "Faltante": "red", "Sobrante": "orange"}
#     )
#     st.plotly_chart(fig_eri, use_container_width=True)

#     # Tabla detallada ERI
#     tabla_detalle_eri = merged_eri.rename(columns={
#         "clave_teorica_eri": "clave_producto_referencia",
#         "stock_teorico": "stock_registro",
#         "stock_fisico": "stock_fisico_contado",
#         "diferencia": "diferencia_fisico_registro",
#         "estado": "estado_conteo",
#         "UBICACION_NOMBRE": "ubicaciones_teoricas"
#     })
#     st.dataframe(
#         tabla_detalle_eri[[
#             "clave_producto_referencia", "stock_registro", "stock_fisico_contado", "diferencia_fisico_registro", "estado_conteo", "ubicaciones_teoricas"
#         ]],
#         use_container_width=True
#     )

#     # Botón para descargar ERI
#     csv_eri = tabla_detalle_eri.to_csv(index=False).encode("utf-8")

# else:
#     st.info("👉 Escanee códigos para generar el reporte ERI.")

# # Mostrar escaneos acumulados (ERU)
# if st.session_state["escaneos_eru"]:
#     st.subheader("📊 Escaneos ERU Acumulados")
#     st.write(f"Total de escaneos ERU: {len(st.session_state['escaneos_eru'])}")

#     # Convertir los escaneos ERU a un DataFrame
#     df_escaneos_eru = pd.DataFrame(st.session_state["escaneos_eru"], columns=["clave_escaneada_eru"])
#     # Contar cuántas veces se ha escaneado cada código ERU (producto+ref+ubicación)
#     stock_fisico_eru = (
#         df_escaneos_eru["clave_escaneada_eru"]
#         .value_counts()
#         .reset_index()
#     )
#     stock_fisico_eru.columns = ["clave_escaneada_eru", "stock_fisico_eru"]

#     # Crear una columna que solo contenga la parte de producto+referencia del código escaneado
#     # Esto es para identificar a qué ítem teórico pertenece (aunque la ubicación pueda estar mal)
#     # Necesitamos revertir la concatenación: clave_escaneada_eru = clave_eri + ubicacion

#     # Aplicar la desconcatenación
#     df_temp = df_escaneos_eru.copy()
#     # Usamos apply con axis=1 para iterar por filas
#     df_temp[['clave_producto_ref_eru', 'ubicacion_escaneada']] = df_temp.apply(
#         lambda row: pd.Series(desconcatenar_producto_ref(row['clave_escaneada_eru'], stock_teorico_eri['UBICACION_NOMBRE'].explode().unique())),
#         axis=1
#     )

#     # Unir con la data teórica para obtener las ubicaciones teóricas posibles (puede haber varias)
#     # Agrupamos por clave_teorica_eri para tener una lista de ubicaciones
#     ubicaciones_por_clave_eru = stock_teorico_eri.groupby('clave_teorica_eri')['UBICACION_NOMBRE'].apply(list).reset_index()
#     ubicaciones_por_clave_eru.rename(columns={'clave_teorica_eri': 'clave_producto_ref_eru'}, inplace=True)

#     merged_eru_temp = df_temp.merge(
#         ubicaciones_por_clave_eru,
#         on='clave_producto_ref_eru',
#         how='left'
#     )

#     # === Función robusta para evaluar el estado de ubicación ===
#     def normalizar_ubicacion(u):
#         """Convierte una ubicación a formato estandarizado (sin espacios, mayúsculas)."""
#         if isinstance(u, list):  # Si por error es una lista, la convertimos en texto
#             u = " ".join(map(str, u))
#         if pd.isna(u):
#             return ""
#         return str(u).strip().replace(" ", "").replace("_", "").upper()

#     def evaluar_estado_ubicacion(row):
#         # Validaciones iniciales
#         if pd.isna(row['clave_producto_ref_eru']) or pd.isna(row['ubicacion_escaneada']):
#             return "Código Escaneado Inválido"

#         ubicaciones_teoricas = row['UBICACION_NOMBRE']

#         # Si no es lista (NaN o valor único)
#         if not isinstance(ubicaciones_teoricas, list):
#             return "Producto/Referencia No Encontrado"

#         # --- Normalización segura ---
#         ubicaciones_planas = []
#         for ub in ubicaciones_teoricas:
#             if isinstance(ub, list):  # Si dentro hay una sublista, la extendemos
#                 ubicaciones_planas.extend(ub)
#             else:
#                 ubicaciones_planas.append(ub)

#         ubicaciones_teoricas_limpias = [normalizar_ubicacion(u) for u in ubicaciones_planas]
#         ubicacion_escaneada_limpia = normalizar_ubicacion(row['ubicacion_escaneada'])

#         # --- Comparación robusta ---
#         if ubicacion_escaneada_limpia in ubicaciones_teoricas_limpias:
#             return "OK (Ubicación Correcta)"
#         else:
#             return "Ubicación Incorrecta"

#     merged_eru_temp['estado_ubicacion'] = merged_eru_temp.apply(evaluar_estado_ubicacion, axis=1)

#     # Contar resultados
#     conteo_estado_eru = merged_eru_temp['estado_ubicacion'].value_counts()

#     # Calcular ERU
#     total_escaneos_eru = len(merged_eru_temp)
#     items_ubicacion_correcta = conteo_estado_eru.get("OK (Ubicación Correcta)", 0)
#     items_ubicacion_incorrecta = conteo_estado_eru.get("Ubicación Incorrecta", 0) + conteo_estado_eru.get("Código Escaneado Inválido", 0) + conteo_estado_eru.get("Producto/Referencia No Encontrado", 0)
#     exactitud_eru = (items_ubicacion_correcta / total_escaneos_eru) * 100 if total_escaneos_eru > 0 else 0

#     # Reporte ERU
#     st.subheader("📈 Reporte ERU")
#     col1, col2, col3 = st.columns(3)
#     col1.metric("Exactitud ERU", f"{exactitud_eru:.2f}%")
#     col2.metric("Ubicaciones Correctas", items_ubicacion_correcta)
#     col3.metric("Ubicaciones Incorrectas", items_ubicacion_incorrecta)

#     # Gráfico ERU
#     fig_eru = px.pie(
#         names=conteo_estado_eru.index,
#         values=conteo_estado_eru.values,
#         title="Distribución ERU",
#         color_discrete_map={
#             "OK (Ubicación Correcta)": "green",
#             "Ubicación Incorrecta": "red",
#             "Código Escaneado Inválido": "orange",
#             "Producto/Referencia No Encontrado": "orange"
#         }
#     )
#     st.plotly_chart(fig_eru, use_container_width=True)

#     # Tabla detallada ERU
#     st.dataframe(
#         merged_eru_temp[[
#             "clave_escaneada_eru", "clave_producto_ref_eru", "ubicacion_escaneada", "UBICACION_NOMBRE", "estado_ubicacion"
#         ]],
#         use_container_width=True
#     )

#     # Botón para descargar ERU
#     csv_eru = merged_eru_temp.to_csv(index=False).encode("utf-8")

# # ================== REPORTE GENERAL (VISUAL + SUGERENCIAS) ==================
# from streamlit_modal import Modal

# st.markdown("---")
# st.subheader("📘 Visualización General ERI & ERU")

# # Solo mostrar si hay escaneos
# hay_eri = "fig_eri" in locals()
# hay_eru = "fig_eru" in locals()

# if hay_eri or hay_eru:
#     if st.button("📊 Generar Visualización General"):
#         st.session_state["mostrar_modal_graficas"] = True
# else:
#     st.info("👉 Escanee productos para generar los gráficos ERI y ERU antes de visualizar el reporte.")

# # --- Mostrar modal ---
# if st.session_state.get("mostrar_modal_graficas", False):
#     modal = Modal(
#         "📈 Visualización General de Resultados (ERI + ERU)",
#         key="modal_visual_graficas",
#         max_width=1100,
#     )
#     modal.open()

#     if modal.is_open():
#         with modal.container():
#             st.markdown("### 📊 Gráficas Generales")

#             # Mostrar las dos gráficas una al lado de la otra
#             col1, col2 = st.columns(2)
#             with col1:
#                 if hay_eri:
#                     st.plotly_chart(fig_eri, use_container_width=True)
#                 else:
#                     st.info("No hay datos ERI.")
#             with col2:
#                 if hay_eru:
#                     st.plotly_chart(fig_eru, use_container_width=True)
#                 else:
#                     st.info("No hay datos ERU.")

#             st.markdown("---")
#             st.markdown("### ✏️ Observaciones o Sugerencias")
#             sugerencias = st.text_area(
#                 "Escribe tus observaciones generales:",
#                 key="sugerencias_visual",
#                 height=120,
#                 placeholder="Ejemplo: Revisar productos con diferencias o ubicaciones incorrectas..."
#             )

#             # Mostrar texto en pantalla (no descarga, solo feedback)
#             if sugerencias:
#                 st.success("✅ Sugerencia registrada:")
#                 st.write(sugerencias)

#             # Botón de cierre
#             if st.button("❌ Cerrar"):
#                 st.session_state["mostrar_modal_graficas"] = False
#                 st.rerun()


# else:
#     st.info("👉 Escanee códigos con ubicación (ERU) para generar el reporte ERU.")
