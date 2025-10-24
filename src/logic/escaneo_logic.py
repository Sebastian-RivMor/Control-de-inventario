import streamlit as st
import pandas as pd
from src.logic.utils import desconcatenar_producto_ref

def procesar_escaneo(stock_teorico_eri):
    st.subheader("🔍 Escaneo Físico ")

    if "escaneos_eri" not in st.session_state:
        st.session_state["escaneos_eri"] = []
    if "escaneos_eru" not in st.session_state:
        st.session_state["escaneos_eru"] = []
    if "mensaje_escaneo" not in st.session_state:
        st.session_state["mensaje_escaneo"] = ""

    def callback_procesar():
        codigo_ingresado = st.session_state.get("codigo_escaneado_form", "")
        if codigo_ingresado:
            clave_producto_ref, ubicacion_escaneada = desconcatenar_producto_ref(
                codigo_ingresado,
                stock_teorico_eri['UBICACION_NOMBRE'].explode().unique(),
                stock_teorico_eri
            )

            if clave_producto_ref and ubicacion_escaneada:
                st.session_state["escaneos_eru"].append(codigo_ingresado)
                st.session_state["mensaje_escaneo"] = f"✅ Escaneado: {codigo_ingresado}"
                st.session_state["escaneos_eri"].append(clave_producto_ref)
            else:
                st.session_state["mensaje_escaneo"] = f"⚠️ Código escaneado no coincide: {codigo_ingresado}"
            st.session_state["codigo_escaneado_form"] = ""

    # Mostrar mensaje
    if st.session_state["mensaje_escaneo"]:
        st.success(st.session_state["mensaje_escaneo"])
        st.session_state["mensaje_escaneo"] = ""

    # Formulario
    with st.form(key="form_escaneo"):
        st.text_input("Escanee un código de barras", key="codigo_escaneado_form")
        st.form_submit_button("Agregar Escaneo", on_click=callback_procesar)

    # Botón limpiar
    if st.button("🗑️ Limpiar Todos los Escaneos"):
        st.session_state["escaneos_eri"].clear()
        st.session_state["escaneos_eru"].clear()
        st.success("Escaneos limpiados")
