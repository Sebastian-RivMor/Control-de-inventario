import streamlit as st
import pandas as pd

def configurar_pagina():
    st.set_page_config(page_title="📊 ERI & ERU - Exactitud de Inventario", layout="wide")
    st.title("📊 Sistema ERI & ERU - Exactitud de Registro de Inventario y Ubicación")

def seleccionar_almacen(df_raw):
    # Normalizar nombres de columnas
    df_raw.columns = df_raw.columns.str.strip().str.upper()

    required_cols = ["ALMACEN_NOMBRE", "PRODUCTO_CODIGO", "REFERENCIA1", "STOCK_REFERENCIAUBICACION", "UBICACION_NOMBRE"]
    missing_cols = [col for col in required_cols if col not in df_raw.columns]

    if missing_cols:
        st.error(f"❌ Faltan columnas: {missing_cols}. Las columnas disponibles son: {list(df_raw.columns)}")
        st.stop()
    else:
        st.success("✅ Todas las columnas requeridas están presentes.")

    # Seleccionar almacén
    almacenes = sorted(df_raw["ALMACEN_NOMBRE"].dropna().unique())
    almacen_seleccionado = st.selectbox("📍 Seleccionar Almacén", almacenes)

    # Filtrar por almacén
    df_filtrado = df_raw[df_raw["ALMACEN_NOMBRE"] == almacen_seleccionado].copy()

    # Crear claves únicas
    df_filtrado["clave_teorica_eri"] = df_filtrado["PRODUCTO_CODIGO"].astype(str) + df_filtrado["REFERENCIA1"].astype(str)
    df_filtrado["clave_teorica_eru"] = df_filtrado["clave_teorica_eri"] + df_filtrado["UBICACION_NOMBRE"].astype(str)

    # Agrupar stock teórico
    stock_teorico_eri = (
        df_filtrado.groupby("clave_teorica_eri")["STOCK_REFERENCIAUBICACION"]
        .sum().round(3).reset_index()
        .rename(columns={"STOCK_REFERENCIAUBICACION": "stock_teorico"})
    )

    ubicaciones_por_eri = df_filtrado.groupby("clave_teorica_eri")["UBICACION_NOMBRE"].apply(lambda x: list(x.unique())).reset_index()
    stock_teorico_eri = stock_teorico_eri.merge(ubicaciones_por_eri, on="clave_teorica_eri", how="left")

    st.info(f"📦 {len(stock_teorico_eri)} ítems teóricos en {almacen_seleccionado}")
    return almacen_seleccionado, df_filtrado, stock_teorico_eri
