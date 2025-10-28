import streamlit as st
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import plotly.io as pio
from datetime import datetime
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import plotly.io as pio
pio.renderers.default = "svg"
pio.kaleido.scope.default_format = "png"
pio.kaleido.scope.default_width = 900
pio.kaleido.scope.default_height = 520
pio.kaleido.scope.default_scale = 1


def mostrar_reporte_general():
    """Muestra los gráficos ERI y ERU con métricas, sugerencias y opción de descarga PDF."""
    st.markdown("---")
    st.subheader("📘 Reporte General ERI & ERU")

    almacen_actual = st.session_state.get("almacen_actual", "Sin definir")

    fig_eri = st.session_state.get("fig_eri")
    fig_eru = st.session_state.get("fig_eru")

    # Extraer métricas si existen
    met_eri = st.session_state.get("metricas_eri", {})
    met_eru = st.session_state.get("metricas_eru", {})

    if not fig_eri and not fig_eru:
        st.info(f"👉 No hay datos de escaneo para el almacén **{almacen_actual}** todavía.")
        return

    st.caption(f"📦 Almacén actual: {almacen_actual}")
    st.caption(f"📅 Generado el {datetime.now().strftime('%d/%m/%Y - %H:%M:%S')}")

    # --- Mostrar métricas en columnas ---
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

    # --- Mostrar gráficos y campos de sugerencias ---
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📊 Gráfico ERI")
        st.plotly_chart(
            fig_eri,
            config={
                "displaylogo": False,
                "responsive": True,
                "autosize": True,
                "style": {"width": "100%"}
            },
            key=f"fig_eri_general_{st.session_state.get('almacen_actual','NA')}"
        )

        sugerencia_eri = st.text_area(
            "✏️ Observaciones sobre ERI:",
            key=f"sugerencia_eri_{almacen_actual}",
            height=100,
            placeholder="Ejemplo: Revisar ítems con diferencias o sobrantes..."
        )

    with col2:
        st.markdown("### 📊 Gráfico ERU")
        st.plotly_chart(
            fig_eru,
            config={
                "displaylogo": False,
                "responsive": True,
                "autosize": True,
                "style": {"width": "100%"}
            },
            key=f"fig_eru_general_{st.session_state.get('almacen_actual','NA')}"
        )
        sugerencia_eru = st.text_area(
            "✏️ Observaciones sobre ERU:",
            key=f"sugerencia_eru_{almacen_actual}",
            height=100,
            placeholder="Ejemplo: Revisar ubicaciones incorrectas o productos mal escaneados..."
        )

    st.markdown("---")

    # --- Generar PDF ---
    def fig_to_png_bytes(fig):
        try:
            img_bytes = BytesIO()
            fig.write_image(img_bytes, format="png")
            img_bytes.seek(0)
            return img_bytes
        except Exception:
            return None
    eri_img = fig_to_png_bytes(fig_eri) if fig_eri else None
    eru_img = fig_to_png_bytes(fig_eru) if fig_eru else None
    if st.button("📥 Generar reporte en PDF"):
        pdf_buffer = generar_pdf(
            almacen_actual=almacen_actual,
            fig_eri=eri_img,
            fig_eru=eru_img,
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
    """Genera un PDF minimalista (B/N) con encabezado, pie, métricas, gráficos y observaciones."""
    
    buffer = BytesIO()

    # === Estilos (minimalista B/N) ===
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleCenter", parent=styles["Title"], alignment=1, fontSize=18, leading=22))
    styles.add(ParagraphStyle(name="H2", parent=styles["Heading2"], fontSize=12, leading=14, spaceBefore=10, spaceAfter=6))
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=9, textColor=colors.black))
    styles.add(ParagraphStyle(name="Label", parent=styles["Normal"], fontSize=10, textColor=colors.black, leading=14))

    # === Encabezado y pie ===
    def _header_footer(cnv: canvas.Canvas, doc):
        cnv.saveState()

        # --- Metadatos PDF (solo 1ra página) ---
        if doc.page == 1:
            cnv.setTitle(f"Reporte ERI & ERU - {almacen_actual}")
            cnv.setAuthor("Sistema ERI-ERU (Inventario IQFarma)")
            cnv.setSubject("Resultados generales y hallazgos ERI & ERU")
            cnv.setCreator("Streamlit · ReportLab")

        # --- Encabezado ---
        top_y = A4[1] - 36
        cnv.setStrokeColor(colors.black)
        cnv.setLineWidth(0.6)
        cnv.line(36, top_y, A4[0] - 36, top_y)
        cnv.setFont("Helvetica", 9)
        cnv.drawString(36, top_y + 6, "Reporte General ERI & ERU")
        cnv.drawRightString(A4[0] - 36, top_y + 6, f"Almacén: {almacen_actual}")

        # --- Pie ---
        bottom_y = 30
        cnv.line(36, bottom_y + 12, A4[0] - 36, bottom_y + 12)
        from datetime import datetime
        cnv.setFont("Helvetica", 8)
        cnv.drawString(36, bottom_y, f"Generado el {datetime.now().strftime('%d/%m/%Y - %H:%M:%S')}")
        cnv.drawRightString(A4[0] - 36, bottom_y, f"Página {doc.page}")
        cnv.restoreState()


    # === Documento base con márgenes y frame de contenido ===
    left, right, top, bottom = 36, 36, 60, 48  # márgenes (pt)
    frame = Frame(left, bottom, A4[0] - left - right, A4[1] - top - bottom, id="normal")
    doc = BaseDocTemplate(buffer, pagesize=A4, leftMargin=left, rightMargin=right, topMargin=top, bottomMargin=bottom)
    doc.addPageTemplates(PageTemplate(id="withHF", frames=[frame], onPage=_header_footer))

    elements = []

    # === Portada breve / título principal ===
    elements.append(Paragraph("Reporte ERI & ERU", styles["TitleCenter"]))
    elements.append(Paragraph(f"Almacén: <b>{almacen_actual}</b>", styles["Small"]))
    elements.append(Spacer(1, 12))

    # === Tabla de métricas (profesional B/N) ===
    data = [["Métrica", "ERI", "ERU"]]
    data.append(["Exactitud (%)", f"{met_eri.get('exactitud', 0):.2f}", f"{met_eru.get('exactitud', 0):.2f}"])
    data.append(["Correctos", f"{met_eri.get('ok', 0)}", f"{met_eru.get('ok', 0)}"])
    data.append(["Errores", f"{met_eri.get('error', 0)}", f"{met_eru.get('error', 0)}"])

    tbl = Table(data, hAlign="LEFT", colWidths=[2.2*inch, 1.2*inch, 1.2*inch])
    tbl.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.black),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("LINEABOVE", (0, 0), (-1, 0), 1, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 1, colors.black),
        ("GRID", (0, 1), (-1, -1), 0.25, colors.black),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(Paragraph("1. Métricas generales", styles["H2"]))
    elements.append(tbl)
    elements.append(Spacer(1, 16))

    # === Helper para insertar figura Plotly con fallback elegante ===
    def _plotly_to_image_flowable(fig, title_text):
        flow = []
        flow.append(Paragraph(title_text, styles["H2"]))
        if fig is None:
            flow.append(Paragraph("<i>No se registró gráfico para esta sección.</i>", styles["Small"]))
            flow.append(Spacer(1, 8))
            return flow
        try:
            img_bytes = BytesIO()
            # Preferir to_image si está disponible
            if hasattr(fig, "to_image"):
                img = fig.to_image(format="png", width=900, height=520, scale=1)
                img_bytes.write(img)
                img_bytes.seek(0)
            else:
                if isinstance(fig_eri, BytesIO):
                    elements.append(Image(fig_eri, width=5.9*inch, height=3.4*inch))
                img_bytes.seek(0)

            flow.append(Image(img_bytes, width=5.9*inch, height=3.4*inch))  # respeta márgenes
            flow.append(Spacer(1, 6))
        except Exception as e:
            # Si Kaleido no está o falla la exportación, no rompemos el PDF
            flow.append(Paragraph(
                "<i>No fue posible incrustar la imagen del gráfico (dependencia de exportación no disponible). "
                "El reporte continúa sin imagen.</i>",
                styles["Small"]
            ))
            flow.append(Spacer(1, 6))
        return flow

    # === Sección ERI ===
    elements += _plotly_to_image_flowable(fig_eri, "2. Gráfico ERI")
    if sugerencia_eri:
        elements.append(Paragraph("Observaciones ERI", styles["Label"]))
        elements.append(Paragraph(sugerencia_eri.replace("\n", "<br/>"), styles["Small"]))
        elements.append(Spacer(1, 12))

    # Forzar salto si el contenido siguiente quedará muy apretado
    elements.append(PageBreak())

    # === Sección ERU ===
    elements += _plotly_to_image_flowable(fig_eru, "3. Gráfico ERU")
    if sugerencia_eru:
        elements.append(Paragraph("Observaciones ERU", styles["Label"]))
        elements.append(Paragraph(sugerencia_eru.replace("\n", "<br/>"), styles["Small"]))
        elements.append(Spacer(1, 12))

    # === Cierre (opcional) ===
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "Este documento presenta un resumen ejecutivo de precisión y hallazgos relevantes para ERI y ERU en el período evaluado.",
        styles["Small"]
    ))

    # === Metadatos PDF ===
    doc.title = f"Reporte ERI & ERU - {almacen_actual}"
    doc.author = "Sistema ERI-ERU (Inventario IQFarma)"
    doc.subject = "Resultados generales y hallazgos ERI & ERU"
    doc.creator = "Streamlit · ReportLab"

    # === Construir PDF ===
    doc.build(elements)
    buffer.seek(0)
    return buffer
