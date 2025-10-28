import streamlit as st
import pandas as pd
import plotly.express as px

def mostrar_reporte_eri(stock_teorico_eri):
    """Genera todo el bloque del reporte ERI: escaneos, métricas, gráfico y tabla."""
    if st.session_state["escaneos_eri"]:
        st.subheader("📊 Escaneos ERI Acumulados")
        st.write(f"Total de escaneos ERI: {len(st.session_state['escaneos_eri'])}")

        # --- DataFrame de escaneos ERI ---
        df_escaneos_eri = pd.DataFrame(st.session_state["escaneos_eri"], columns=["clave_escaneada_eri"])
        stock_fisico_eri = (
            df_escaneos_eri["clave_escaneada_eri"]
            .value_counts()
            .reset_index()
        )
        stock_fisico_eri.columns = ["clave_escaneada_eri", "stock_fisico"]
        st.dataframe(stock_fisico_eri, use_container_width=True)

        # --- Cruce ERI (teórico vs físico) ---
        merged_eri = pd.merge(
            stock_teorico_eri,
            stock_fisico_eri,
            left_on="clave_teorica_eri",
            right_on="clave_escaneada_eri",
            how="outer"
        ).fillna(0)

        # --- Cálculo de diferencias ---
        merged_eri["diferencia"] = merged_eri["stock_fisico"] - merged_eri["stock_teorico"]

        # --- Estado por ítem ---
        merged_eri["estado"] = merged_eri["diferencia"].apply(
            lambda x: "Completo" if x == 0 else ("Sobrante" if x > 0 else "Faltante")
        )

        # --- Exactitud ERI ---
        total_items_eri = len(merged_eri)
        items_con_error_eri = len(merged_eri[merged_eri["diferencia"] != 0])
        exactitud_eri = (1 - items_con_error_eri / total_items_eri) * 100 if total_items_eri > 0 else 0

        # --- Métricas ERI ---
        st.subheader("📈 Reporte ERI")
        col1, col2, col3 = st.columns(3)
        col1.metric("Exactitud ERI", f"{exactitud_eri:.2f}%")
        col2.metric("Ítems Correctos ERI", len(merged_eri[merged_eri["estado"] == "Completo"]))
        col3.metric("Ítems con Error ERI", items_con_error_eri)

        # --- Gráfico ERI ---
        fig_eri = px.pie(
            merged_eri,
            names="estado",
            title="Distribución ERI",
            color="estado",
            color_discrete_map={
                "Completo": "#22c55e",         # verde
                "Faltante": "#ef4444",   # rojo
                "Sobrante": "#f59e0b"    # naranja
            }
        )
        fig_eri.update_layout(
            template="plotly_white",
            legend_title_text="Estado",
            paper_bgcolor="white",
            plot_bgcolor="white"
        )

        st.plotly_chart(
            fig_eri,
            config={
                "displaylogo": False,
                "responsive": True,
                "autosize": True,
                "style": {"width": "100%"}
            },
            key=f"fig_eri_panel_{st.session_state.get('almacen_actual','NA')}"
        )



        # --- Tabla detallada ERI ---
        tabla_detalle_eri = merged_eri.rename(columns={
            "clave_teorica_eri": "clave_producto_referencia",
            "stock_teorico": "stock_registro",
            "stock_fisico": "stock_fisico_contado",
            "diferencia": "diferencia_fisico_registro",
            "estado": "estado_conteo",
            "UBICACION_NOMBRE": "ubicaciones_teoricas"
        })
        st.dataframe(
            tabla_detalle_eri[[
                "clave_producto_referencia",
                "stock_registro",
                "stock_fisico_contado",
                "diferencia_fisico_registro",
                "estado_conteo",
                "ubicaciones_teoricas"
            ]],
            width='stretch'
        )

        # --- Exportación CSV (opcional) ---
        csv_eri = tabla_detalle_eri.to_csv(index=False).encode("utf-8")

        # Guardar figura globalmente para usar en reporte general
        st.session_state["fig_eri"] = fig_eri
        st.session_state["fig_eri_almacen"] = st.session_state.get("almacen_actual")
        st.session_state["metricas_eri"] = {
            "exactitud": exactitud_eri,
            "Completo": len(merged_eri[merged_eri["estado"] == "Completo"]),
            "error": items_con_error_eri
        }
