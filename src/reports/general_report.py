import streamlit as st
from streamlit_modal import Modal

def mostrar_reporte_general():
    """Muestra la visualización combinada de ERI y ERU dentro de un modal con observaciones."""
    st.markdown("---")
    st.subheader("📘 Visualización General ERI & ERU")

    # Detectar si hay gráficos generados
    hay_eri = "fig_eri" in st.session_state
    hay_eru = "fig_eru" in st.session_state

    # --- Botón para generar visualización ---
    if hay_eri or hay_eru:
        if st.button("📊 Generar Visualización General"):
            st.session_state["mostrar_modal_graficas"] = True
    else:
        st.info("👉 Escanee productos para generar los gráficos ERI y ERU antes de visualizar el reporte.")
        return

    # --- Mostrar modal ---
    if st.session_state.get("mostrar_modal_graficas", False):
        modal = Modal(
            "📈 Visualización General de Resultados (ERI + ERU)",
            key="modal_visual_graficas",
            max_width=1100,
        )
        modal.open()

        if modal.is_open():
            with modal.container():
                st.markdown("### 📊 Gráficas Generales")

                # Mostrar las dos gráficas lado a lado
                col1, col2 = st.columns(2)
                with col1:
                    if hay_eri:
                        st.plotly_chart(st.session_state["fig_eri"], use_container_width=True)
                    else:
                        st.info("No hay datos ERI.")
                with col2:
                    if hay_eru:
                        st.plotly_chart(st.session_state["fig_eru"], use_container_width=True)
                    else:
                        st.info("No hay datos ERU.")

                st.markdown("---")
                st.markdown("### ✏️ Observaciones o Sugerencias")

                # Área de texto
                sugerencias = st.text_area(
                    "Escribe tus observaciones generales:",
                    key="sugerencias_visual",
                    height=120,
                    placeholder="Ejemplo: Revisar productos con diferencias o ubicaciones incorrectas..."
                )

                # Mostrar sugerencia como feedback
                if sugerencias:
                    st.success("✅ Sugerencia registrada:")
                    st.write(sugerencias)

                # Botón de cierre
                if st.button("❌ Cerrar"):
                    st.session_state["mostrar_modal_graficas"] = False
                    st.rerun()
