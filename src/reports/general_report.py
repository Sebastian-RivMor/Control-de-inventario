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
from reportlab.pdfgen import canvas
from datetime import datetime
import plotly.io as pio


def mostrar_reporte_general():
    """Muestra los gráficos ERI y ERU con métricas, sugerencias y opción de descarga PDF."""
    st.markdown("---")
    st.subheader("📘 Reporte General ERI & ERU")

    almacen_actual = st.session_state.get("almacen_actual", "Sin definir")
    fig_eri = st.session_state.get("fig_eri")
    fig_eru = st.session_state.get("fig_eru")
    met_eri = st.session_state.get("metricas_eri", {})
    met_eru = st.session_state.get("metricas_eru", {})

    if not fig_eri and not fig_eru:
        st.info(f"👉 No hay datos de escaneo para el almacén **{almacen_actual}** todavía.")
        return

    st.caption(f"📦 Almacén actual: {almacen_actual}")
    st.caption(f"📅 Generado el {datetime.now().strftime('%d/%m/%Y - %H:%M:%S')}")

    # --- Métricas ---
    st.markdown("### 📈 Métricas Generales")
    col1, col2 = st.columns(2)
    with col1:
        if met_eri:
            st.metric("Exactitud ERI", f"{met_eri.get('exactitud', 0):.2f}%")
            st.metric("Ítems Correctos ERI", met_eri.get("ok", 0))
            st.metric("Ítems con Error ERI", met_eri.get("error", 0))
        else:
            st.info("No hay métricas ERI registradas.")
    with col2:
        if met_eru:
            st.metric("Exactitud ERU", f"{met_eru.get('exactitud', 0):.2f}%")
            st.metric("Ubicaciones Correctas", met_eru.get("ok", 0))
            st.metric("Ubicaciones Incorrectas", met_eru.get("error", 0))
        else:
            st.info("No hay métricas ERU registradas.")

    st.markdown("---")

    # --- Gráficos y observaciones ---
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📊 Gráfico ERI")
        st.plotly_chart(fig_eri, config={"displaylogo": False, "responsive": True})
        sugerencia_eri = st.text_area(
            "✏️ Observaciones sobre ERI:",
            key=f"sugerencia_eri_{almacen_actual}",
            height=100,
            placeholder="Ejemplo: Revisar ítems con diferencias o sobrantes..."
        )

    with col2:
        st.markdown("### 📊 Gráfico ERU")
        st.plotly_chart(fig_eru, config={"displaylogo": False, "responsive": True})
        sugerencia_eru = st.text_area(
            "✏️ Observaciones sobre ERU:",
            key=f"sugerencia_eru_{almacen_actual}",
            height=100,
            placeholder="Ejemplo: Revisar ubicaciones incorrectas o productos mal escaneados..."
        )

    st.markdown("---")

    # --- Generar PDF ---
    if st.button("📥 Generar reporte en PDF"):
        pdf_buffer = generar_pdf(
            almacen_actual=almacen_actual,
            fig_eri=fig_eri,
            fig_eru=fig_eru,
            sugerencia_eri=sugerencia_eri,
            sugerencia_eru=sugerencia_eru,
            met_eri=met_eri,
            met_eru=met_eru
        )

        st.download_button(
            label="⬇️ Descargar archivo PDF",
            data=pdf_buffer,
            file_name=f"Reporte_{almacen_actual}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf"
        )


def generar_pdf(almacen_actual, fig_eri, fig_eru, sugerencia_eri, sugerencia_eru, met_eri, met_eru):
    """Genera un PDF minimalista B/N con métricas, gráficos y observaciones (sin Kaleido)."""
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleCenter", parent=styles["Title"], alignment=1, fontSize=18))
    styles.add(ParagraphStyle(name="H2", parent=styles["Heading2"], fontSize=12, leading=14, spaceBefore=10))
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=9, textColor=colors.black))
    styles.add(ParagraphStyle(name="Label", parent=styles["Normal"], fontSize=10, textColor=colors.black, leading=14))

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

    left, right, top, bottom = 36, 36, 60, 48
    frame = Frame(left, bottom, A4[0] - left - right, A4[1] - top - bottom, id="normal")
    doc = BaseDocTemplate(buffer, pagesize=A4, leftMargin=left, rightMargin=right, topMargin=top, bottomMargin=bottom)
    doc.addPageTemplates(PageTemplate(id="withHF", frames=[frame], onPage=_header_footer))

    elements = []
    elements.append(Paragraph("Reporte ERI & ERU", styles["TitleCenter"]))
    elements.append(Paragraph(f"Almacén: <b>{almacen_actual}</b>", styles["Small"]))
    elements.append(Spacer(1, 12))

    # --- Tabla de métricas ---
    data = [["Métrica", "ERI", "ERU"]]
    data.append(["Exactitud (%)", f"{met_eri.get('exactitud', 0):.2f}", f"{met_eru.get('exactitud', 0):.2f}"])
    data.append(["Correctos", f"{met_eri.get('ok', 0)}", f"{met_eru.get('ok', 0)}"])
    data.append(["Errores", f"{met_eri.get('error', 0)}", f"{met_eru.get('error', 0)}"])

    tbl = Table(data, hAlign="LEFT", colWidths=[2.2*inch, 1.2*inch, 1.2*inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.black),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 1), (-1, -1), 0.25, colors.black),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ]))
    elements.append(Paragraph("1. Métricas generales", styles["H2"]))
    elements.append(tbl)
    elements.append(Spacer(1, 16))

    # --- Conversión robusta de figuras a imagen ---
    def plotly_to_image(fig):
        try:
            img_bytes = BytesIO(fig.to_image(format="png", width=900, height=520, scale=1))
            img_bytes.seek(0)
            return img_bytes
        except Exception:
            return None

    # ERI
    elements.append(Paragraph("2. Gráfico ERI", styles["H2"]))
    eri_img = plotly_to_image(fig_eri)
    if eri_img:
        elements.append(Image(eri_img, width=5.9*inch, height=3.4*inch))
    else:
        elements.append(Paragraph("<i>No fue posible convertir el gráfico ERI a imagen.</i>", styles["Small"]))
    if sugerencia_eri:
        elements.append(Paragraph("Observaciones ERI", styles["Label"]))
        elements.append(Paragraph(sugerencia_eri.replace("\n", "<br/>"), styles["Small"]))
    elements.append(PageBreak())

    # ERU
    elements.append(Paragraph("3. Gráfico ERU", styles["H2"]))
    eru_img = plotly_to_image(fig_eru)
    if eru_img:
        elements.append(Image(eru_img, width=5.9*inch, height=3.4*inch))
    else:
        elements.append(Paragraph("<i>No fue posible convertir el gráfico ERU a imagen.</i>", styles["Small"]))
    if sugerencia_eru:
        elements.append(Paragraph("Observaciones ERU", styles["Label"]))
        elements.append(Paragraph(sugerencia_eru.replace("\n", "<br/>"), styles["Small"]))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "Este documento presenta un resumen ejecutivo de precisión y hallazgos relevantes para ERI y ERU en el período evaluado.",
        styles["Small"]
    ))

    doc.title = f"Reporte ERI & ERU - {almacen_actual}"
    doc.author = "Sistema ERI-ERU (Inventario IQFarma)"
    doc.subject = "Resultados generales y hallazgos ERI & ERU"
    doc.creator = "Streamlit · ReportLab"

    doc.build(elements)
    buffer.seek(0)
    return buffer
