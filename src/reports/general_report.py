import streamlit as st
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, Table, TableStyle, Image, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# =====================================================
# 📊 Función auxiliar: gráfico de pastel (para PDF)
# =====================================================
def generar_grafico_pastel(titulo, datos_ok, datos_error):
    fig, ax = plt.subplots(figsize=(4.5, 3.5))
    etiquetas = ['Correctos', 'Errores']
    valores = [datos_ok, datos_error]
    colores = ['#4CAF50', '#E53935']

    if sum(valores) == 0:
        valores = [1, 0]
        etiquetas = ['Sin datos', '']

    wedges, texts, autotexts = ax.pie(
        valores,
        labels=etiquetas,
        autopct='%1.1f%%',
        startangle=90,
        colors=colores,
        textprops={'color': "black", 'fontsize': 9}
    )
    ax.set_title(titulo, fontsize=11, fontweight='bold')
    ax.axis('equal')
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=120, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


# =====================================================
# 🧾 Función principal
# =====================================================
def mostrar_reporte_general():
    """Muestra gráficos ERI/ERU, métricas y genera reporte PDF (con gráficos junto a sus observaciones)."""
    st.markdown("---")
    st.subheader("📘 Reporte General ERI & ERU")

    # === Datos desde sesión ===
    almacen_actual = st.session_state.get("almacen_actual", "Sin definir")
    met_eri = st.session_state.get("metricas_eri", {})
    met_eru = st.session_state.get("metricas_eru", {})
    fig_eri = st.session_state.get("fig_eri")
    fig_eru = st.session_state.get("fig_eru")

    if not met_eri and not met_eru:
        st.info(f"👉 No hay métricas registradas para el almacén **{almacen_actual}** todavía.")
        return

    st.caption(f"📦 Almacén actual: {almacen_actual}")
    st.caption(f"📅 Generado el {datetime.now().strftime('%d/%m/%Y - %H:%M:%S')}")

    # =====================================================
    # 📈 Métricas Generales
    # =====================================================
    st.markdown("### 📈 Métricas Generales")
    col1, col2 = st.columns(2)
    with col1:
        if met_eri:
            st.metric("Exactitud ERI", f"{met_eri.get('exactitud', 0):.2f}%")
            st.metric("Ítems Correctos ERI", met_eri.get("ok", 0))
            st.metric("Ítems con Error ERI", met_eri.get("error", 0))
        else:
            st.info("Sin datos ERI aún.")
    with col2:
        if met_eru:
            st.metric("Exactitud ERU", f"{met_eru.get('exactitud', 0):.2f}%")
            st.metric("Ubicaciones Correctas", met_eru.get("ok", 0))
            st.metric("Ubicaciones Incorrectas", met_eru.get("error", 0))
        else:
            st.info("Sin datos ERU aún.")

    st.markdown("---")

    # =====================================================
    # 📊 Sección ERI (gráfico + observaciones)
    # =====================================================
    st.markdown("### 📊 Distribución ERI")
    if fig_eri:
        st.plotly_chart(fig_eri, use_container_width=True, config={"displaylogo": False})
    else:
        st.warning("⚠️ No se encontró gráfico ERI. Genera el reporte ERI primero.")

    sugerencia_eri = st.text_area(
        "✏️ Observaciones sobre ERI:",
        key=f"sugerencia_eri_{almacen_actual}",
        height=100,
        placeholder="Ejemplo: Revisar ítems con diferencias o sobrantes..."
    )

    st.markdown("---")

    # =====================================================
    # 📊 Sección ERU (gráfico + observaciones)
    # =====================================================
    st.markdown("### 📊 Distribución ERU")
    if fig_eru:
        st.plotly_chart(fig_eru, use_container_width=True, config={"displaylogo": False})
    else:
        st.warning("⚠️ No se encontró gráfico ERU. Genera el reporte ERU primero.")

    sugerencia_eru = st.text_area(
        "✏️ Observaciones sobre ERU:",
        key=f"sugerencia_eru_{almacen_actual}",
        height=100,
        placeholder="Ejemplo: Revisar ubicaciones incorrectas o productos mal escaneados..."
    )

    st.markdown("---")

    # =====================================================
    # 📥 Generar PDF (interno)
    # =====================================================
    if st.button("📥 Generar reporte en PDF"):
        with st.spinner("Generando reporte PDF..."):
            pdf_buffer = generar_pdf(
                almacen_actual=almacen_actual,
                met_eri=met_eri,
                met_eru=met_eru,
                sugerencia_eri=sugerencia_eri,
                sugerencia_eru=sugerencia_eru
            )

        st.success("✅ Reporte PDF generado correctamente.")
        st.download_button(
            label="⬇️ Descargar archivo PDF",
            data=pdf_buffer.getvalue(),
            file_name=f"Reporte_{almacen_actual}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf"
        )


# =====================================================
# 🧱 Generación interna de PDF (no se muestra en front)
# =====================================================
def generar_pdf(almacen_actual, met_eri, met_eru, sugerencia_eri, sugerencia_eru):
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleCenter", parent=styles["Title"], alignment=1, fontSize=18))
    styles.add(ParagraphStyle(name="H2", parent=styles["Heading2"], fontSize=12, leading=14, spaceBefore=10))
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=9))
    styles.add(ParagraphStyle(name="Label", parent=styles["Normal"], fontSize=10, leading=14))

    def _header_footer(c, doc):
        c.saveState()
        top_y = A4[1] - 36
        c.setStrokeColor(colors.black)
        c.line(36, top_y, A4[0] - 36, top_y)
        c.setFont("Helvetica", 9)
        c.drawString(36, top_y + 6, "Reporte General ERI & ERU")
        c.drawRightString(A4[0] - 36, top_y + 6, f"Almacén: {almacen_actual}")
        bottom_y = 30
        c.line(36, bottom_y + 12, A4[0] - 36, bottom_y + 12)
        c.setFont("Helvetica", 8)
        c.drawString(36, bottom_y, f"Generado el {datetime.now().strftime('%d/%m/%Y - %H:%M:%S')}")
        c.drawRightString(A4[0] - 36, bottom_y, f"Página {doc.page}")
        c.restoreState()

    doc = BaseDocTemplate(buffer, pagesize=A4)
    frame = Frame(36, 48, A4[0] - 72, A4[1] - 108, id="normal")
    doc.addPageTemplates(PageTemplate(id="main", frames=[frame], onPage=_header_footer))

    elements = []
    elements.append(Paragraph("Reporte ERI & ERU", styles["TitleCenter"]))
    elements.append(Paragraph(f"Almacén: <b>{almacen_actual}</b>", styles["Small"]))
    elements.append(Spacer(1, 12))

    # Tabla de métricas
    data = [["Métrica", "ERI", "ERU"]]
    data.append(["Exactitud (%)", f"{met_eri.get('exactitud', 0):.2f}", f"{met_eru.get('exactitud', 0):.2f}"])
    data.append(["Correctos", f"{met_eri.get('ok', 0)}", f"{met_eru.get('ok', 0)}"])
    data.append(["Errores", f"{met_eri.get('error', 0)}", f"{met_eru.get('error', 0)}"])

    tbl = Table(data, hAlign="LEFT", colWidths=[2.2 * inch, 1.2 * inch, 1.2 * inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.black),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 1), (-1, -1), 0.25, colors.black),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ]))
    elements.append(Paragraph("1. Métricas generales", styles["H2"]))
    elements.append(tbl)
    elements.append(Spacer(1, 20))

    # Gráfico ERI
    elements.append(Paragraph("2. Gráfico ERI (Pastel)", styles["H2"]))
    if met_eri:
        img_eri = generar_grafico_pastel("Distribución ERI", met_eri.get("ok", 0), met_eri.get("error", 0))
        elements.append(Image(img_eri, width=5.5 * inch, height=3.5 * inch))
    if sugerencia_eri:
        elements.append(Paragraph("Observaciones ERI", styles["Label"]))
        elements.append(Paragraph(sugerencia_eri.replace("\n", "<br/>"), styles["Small"]))
    elements.append(PageBreak())

    # Gráfico ERU
    elements.append(Paragraph("3. Gráfico ERU (Pastel)", styles["H2"]))
    if met_eru:
        img_eru = generar_grafico_pastel("Distribución ERU", met_eru.get("ok", 0), met_eru.get("error", 0))
        elements.append(Image(img_eru, width=5.5 * inch, height=3.5 * inch))
    if sugerencia_eru:
        elements.append(Paragraph("Observaciones ERU", styles["Label"]))
        elements.append(Paragraph(sugerencia_eru.replace("\n", "<br/>"), styles["Small"]))

    elements.append(Spacer(1, 10))
    elements.append(Paragraph(
        "Este documento presenta un resumen ejecutivo de precisión y hallazgos relevantes para ERI y ERU.",
        styles["Small"]
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer
