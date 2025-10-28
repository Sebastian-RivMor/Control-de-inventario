import streamlit as st
import pandas as pd
import plotly.express as px
from src.logic.utils import desconcatenar_producto_ref

def mostrar_reporte_eru(stock_teorico_eri):
    """Genera todo el bloque del reporte ERU: escaneos, evaluación de ubicaciones, métricas y gráficos."""
    if st.session_state["escaneos_eru"]:
        st.subheader("📊 Escaneos ERU Acumulados")
        st.write(f"Total de escaneos ERU: {len(st.session_state['escaneos_eru'])}")

        # --- DataFrame de escaneos ERU ---
        df_escaneos_eru = pd.DataFrame(st.session_state["escaneos_eru"], columns=["clave_escaneada_eru"])

        # Contar cuántas veces se escaneó cada clave ERU
        stock_fisico_eru = (
            df_escaneos_eru["clave_escaneada_eru"]
            .value_counts()
            .reset_index()
        )
        stock_fisico_eru.columns = ["clave_escaneada_eru", "stock_fisico_eru"]

        # --- Desconcatenar cada código ERU ---
        df_temp = df_escaneos_eru.copy()
        df_temp[["clave_producto_ref_eru", "ubicacion_escaneada"]] = df_temp.apply(
            lambda row: pd.Series(
                desconcatenar_producto_ref(
                    row["clave_escaneada_eru"],
                    stock_teorico_eri["UBICACION_NOMBRE"].explode().unique(),
                    stock_teorico_eri
                )
            ),
            axis=1
        )

        # --- Obtener ubicaciones teóricas por clave ERI ---
        ubicaciones_por_clave_eru = stock_teorico_eri.groupby("clave_teorica_eri")["UBICACION_NOMBRE"].apply(list).reset_index()
        ubicaciones_por_clave_eru.rename(columns={"clave_teorica_eri": "clave_producto_ref_eru"}, inplace=True)

        merged_eru_temp = df_temp.merge(
            ubicaciones_por_clave_eru,
            on="clave_producto_ref_eru",
            how="left"
        )

        # --- Normalización de ubicaciones ---
        def normalizar_ubicacion(u):
            """Convierte una ubicación a formato estándar (sin espacios, mayúsculas)."""
            if isinstance(u, list):
                u = " ".join(map(str, u))
            if pd.isna(u):
                return ""
            return str(u).strip().replace(" ", "").replace("_", "").upper()

        def evaluar_estado_ubicacion(row):
            """Evalúa si la ubicación escaneada coincide con alguna ubicación teórica."""
            if pd.isna(row["clave_producto_ref_eru"]) or pd.isna(row["ubicacion_escaneada"]):
                return "Código Escaneado Inválido"

            ubicaciones_teoricas = row["UBICACION_NOMBRE"]

            if not isinstance(ubicaciones_teoricas, list):
                return "Producto/Referencia No Encontrado"

            # Aplanar listas anidadas y normalizar
            ubicaciones_planas = []
            for ub in ubicaciones_teoricas:
                if isinstance(ub, list):
                    ubicaciones_planas.extend(ub)
                else:
                    ubicaciones_planas.append(ub)

            ubicaciones_teoricas_limpias = [normalizar_ubicacion(u) for u in ubicaciones_planas]
            ubicacion_escaneada_limpia = normalizar_ubicacion(row["ubicacion_escaneada"])

            # Comparación
            if ubicacion_escaneada_limpia in ubicaciones_teoricas_limpias:
                return "Ubicación Correcta"
            else:
                return "Ubicación Incorrecta"

        # Evaluar ubicación por fila
        merged_eru_temp["estado_ubicacion"] = merged_eru_temp.apply(evaluar_estado_ubicacion, axis=1)

        # --- Conteo de resultados ---
        conteo_estado_eru = merged_eru_temp["estado_ubicacion"].value_counts()

        # --- Cálculo de exactitud ERU ---
        total_escaneos_eru = len(merged_eru_temp)
        items_ubicacion_correcta = conteo_estado_eru.get("Ubicación Correcta", 0)
        items_ubicacion_incorrecta = (
            conteo_estado_eru.get("Ubicación Incorrecta", 0)
            + conteo_estado_eru.get("Código Escaneado Inválido", 0)
            + conteo_estado_eru.get("Producto/Referencia No Encontrado", 0)
        )
        exactitud_eru = (items_ubicacion_correcta / total_escaneos_eru) * 100 if total_escaneos_eru > 0 else 0

        # --- Métricas ERU ---
        st.subheader("📈 Reporte ERU")
        col1, col2, col3 = st.columns(3)
        col1.metric("Exactitud ERU", f"{exactitud_eru:.2f}%")
        col2.metric("Ubicaciones Correctas", items_ubicacion_correcta)
        col3.metric("Ubicaciones Incorrectas", items_ubicacion_incorrecta)

        # --- Gráfico ERU ---
        df_pie_eru = pd.DataFrame({
            "estado": conteo_estado_eru.index,
            "cantidad": conteo_estado_eru.values
        })

        fig_eru = px.pie(
            df_pie_eru,
            names="estado",
            values="cantidad",
            title="Distribución ERU",
            color="estado",
            color_discrete_map={
                "Ubicación Correcta": "#22c55e",  # verde
                "Ubicación Incorrecta": "#ef4444",     # rojo
                "Código Escaneado Inválido": "#f59e0b",
                "Producto/Referencia No Encontrado": "#f59e0b"
            }
        )
        fig_eru.update_layout(
            template="plotly_white",
            legend_title_text="Estado",
            paper_bgcolor="white",
            plot_bgcolor="white"
        )
        st.plotly_chart(
            fig_eru,
            config={
                "displaylogo": False,
                "responsive": True,
                "autosize": True,
                "style": {"width": "100%"}
            },
            key=f"fig_eru_panel_{st.session_state.get('almacen_actual','NA')}"
        )


        # --- Tabla detallada ERU ---
        st.dataframe(
            merged_eru_temp[[
                "clave_escaneada_eru",
                "clave_producto_ref_eru",
                "ubicacion_escaneada",
                "UBICACION_NOMBRE",
                "estado_ubicacion"
            ]],
            width='stretch'
        )

        # --- Exportación CSV (opcional) ---
        csv_eru = merged_eru_temp.to_csv(index=False).encode("utf-8")

        # Guardar figura globalmente para usar en el reporte general
        st.session_state["fig_eru"] = fig_eru
        st.session_state["fig_eru_almacen"] = st.session_state.get("almacen_actual")
        st.session_state["metricas_eru"] = {
            "exactitud": exactitud_eru,
            "ok": items_ubicacion_correcta,
            "error": items_ubicacion_incorrecta
        }
