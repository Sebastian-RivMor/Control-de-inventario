import streamlit as st
import streamlit.components.v1 as components
import base64
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
import plotly.graph_objects as go # Añadido para la verificación de tipo

# ===============================
# GENERAR IMAGEN DEL GRÁFICO DESDE PYTHON (SERVIDOR) - SOLUCIÓN MÁS CONFIABLE
# ===============================
def generar_imagen_grafico(fig, width=900, height=520, scale=1):
    """Genera una imagen PNG del gráfico Plotly usando kaleido del lado del servidor."""
    if fig is None:
        return None
    try:
        img_bytes = fig.to_image(format="png", width=width, height=height, scale=scale)
        return BytesIO(img_bytes)
    except Exception as e:
        st.error(f"Error al generar la imagen del gráfico con kaleido: {e}")
        # Opcional: intentar alternativa JS si kaleido falla
        # return capturar_grafico_js(fig, key) # Descomentar si se quiere intentar JS como fallback
        return None

# ===============================
# CAPTURAR GRÁFICO DESDE FRONTEND JS (OPCIONAL, COMO FALLBACK)
# ===============================
# ===============================
# CAPTURAR GRÁFICO DESDE FRONTEND JS (OPCIONAL, COMO FALLBACK)
# ===============================
def capturar_grafico_js(fig, key):
    """Renderiza el gráfico en el navegador y devuelve la imagen base64 generada por Plotly.js"""
    if fig is None:
        return None
    html_str = f"""
    <html>
      <head>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script> <!-- Corregido el espacio -->
      </head>
      <body>
        <div id='grafico_{key}' style='width:800px;height:500px;'></div>
        <script>
          var fig = {fig.to_json()};
          Plotly.newPlot('grafico_{key}', fig.data, fig.layout).then(() => {{
              Plotly.toImage('grafico_{key}', {{format:'png', width:900, height:520}})
              .then(function(url){{
                  const base64 = url.split(',')[1];
                  // Envía el valor al backend de Streamlit
                  window.parent.postMessage({{
                      type: 'streamlit:setComponentValue',
                      value: base64,
                      key: '{key}'
                  }}, '*');
              }});
          }});
        </script>
      </body>
    </html>
    """
    # components.html no puede devolver directamente el valor de JS de forma síncrona
    # Se usa para renderizar y disparar la captura
    # REMOVIDO: key=f"componente_{key}"
    components.html(html_str, height=520)
    return None # No devuelve el valor aquí

# ===============================
# SECCIÓN PRINCIPAL
# ===============================
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
        # Mostrar el gráfico en Streamlit (esto no es para PDF)
        if fig_eri:
             # Verifica que sea un objeto plotly Figure
            if isinstance(fig_eri, go.Figure):
                st.plotly_chart(fig_eri, use_container_width=True)
            else:
                st.warning("El gráfico ERI no es un objeto Plotly válido.")
        # ELIMINADO: base64_eri = capturar_grafico_js(fig_eri, key="grafico_eri") # Renderiza JS para captura futura (opcional si kaleido funciona)
        sugerencia_eri = st.text_area(
            "✏️ Observaciones sobre ERI:",
            key=f"sugerencia_eri_{almacen_actual}",
            height=100,
            placeholder="Ejemplo: Revisar ítems con diferencias o sobrantes..."
        )

    with col2:
        st.markdown("### 📊 Gráfico ERU")
        # Mostrar el gráfico en Streamlit (esto no es para PDF)
        if fig_eru:
            if isinstance(fig_eru, go.Figure):
                st.plotly_chart(fig_eru, use_container_width=True)
            else:
                 st.warning("El gráfico ERU no es un objeto Plotly válido.")
        # ELIMINADO: base64_eru = capturar_grafico_js(fig_eru, key="grafico_eru") # Renderiza JS para captura futura (opcional si kaleido funciona)
        sugerencia_eru = st.text_area(
            "✏️ Observaciones sobre ERU:",
            key=f"sugerencia_eru_{almacen_actual}",
            height=100,
            placeholder="Ejemplo: Revisar ubicaciones incorrectas o productos mal escaneados..."
        )

    st.markdown("---")

    # --- Botón para Generar PDF ---
    # Las imágenes para el PDF se generan ahora DENTRO de la función de generación,
    # usando kaleido directamente desde los objetos fig_eri y fig_eru originales.
    if st.button("📥 Generar reporte en PDF"):
        # Generar las imágenes directamente aquí, antes de llamar a generar_pdf
        eri_img_bytes = generar_imagen_grafico(fig_eri)
        eru_img_bytes = generar_imagen_grafico(fig_eru)

        # Verificar si las imágenes se generaron correctamente
        if (fig_eri is not None and eri_img_bytes is None) or (fig_eru is not None and eru_img_bytes is None):
             st.error("No se pudieron generar las imágenes de los gráficos para el PDF.")
             return # Detener la ejecución si falla

        pdf_buffer = generar_pdf(
            almacen_actual=almacen_actual,
            eri_img=eri_img_bytes, # Pasa BytesIO directamente
            eru_img=eru_img_bytes, # Pasa BytesIO directamente
            sugerencia_eri=sugerencia_eri,
            sugerencia_eru=sugerencia_eru,
            met_eri=met_eri,
            met_eru=met_eru
        )

        if pdf_buffer:
            st.download_button(
                label="⬇️ Descargar archivo PDF",
                data=pdf_buffer.getvalue(), # Usar getvalue() para obtener los bytes del buffer
                file_name=f"Reporte_{almacen_actual}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf"
            )
        else:
            st.error("Ocurrió un error al generar el PDF.")

# ===============================
# GENERACIÓN DE PDF
# ===============================
def generar_pdf(almacen_actual, eri_img, eru_img, sugerencia_eri, sugerencia_eru, met_eri, met_eru):
    """Genera PDF con encabezado, métricas y gráficos (usando imágenes generadas del lado del servidor)."""
    if eri_img is None and eru_img is None:
         st.error("No se proporcionaron imágenes para el PDF.")
         return None # Devolver None si no hay imágenes válidas

    buffer = BytesIO()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleCenter", parent=styles["Title"], alignment=1, fontSize=18))
    styles.add(ParagraphStyle(name="H2", parent=styles["Heading2"], fontSize=12, leading=14, spaceBefore=10))
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=9))
    styles.add(ParagraphStyle(name="Label", parent=styles["Normal"], fontSize=10, leading=14))

    # --- Header & Footer ---
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

    # --- Documento ---
    doc = BaseDocTemplate(buffer, pagesize=A4)
    frame = Frame(36, 48, A4[0]-72, A4[1]-108, id="normal")
    doc.addPageTemplates(PageTemplate(id="main", frames=[frame], onPage=_header_footer))

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
    elements.append(Spacer(1, 20))

    # --- Gráfico ERI ---
    elements.append(Paragraph("2. Gráfico ERI", styles["H2"]))
    if eri_img:
        # Image necesita un path o un objeto BytesIO
        # Asegurarse de que la imagen esté en la posición 0 antes de usarla
        eri_img.seek(0)
        elements.append(Image(eri_img, width=5.9*inch, height=3.4*inch))
    else:
        elements.append(Paragraph("<i>No se pudo capturar el gráfico ERI.</i>", styles["Small"]))
    if sugerencia_eri:
        elements.append(Paragraph("Observaciones ERI", styles["Label"]))
        elements.append(Paragraph(sugerencia_eri.replace("\n", "<br/>"), styles["Small"]))

    # elements.append(PageBreak()) # Descomentar si se quiere página separada

    # --- Gráfico ERU ---
    elements.append(Paragraph("3. Gráfico ERU", styles["H2"]))
    if eru_img:
        # Image necesita un path o un objeto BytesIO
        # Asegurarse de que la imagen esté en la posición 0 antes de usarla
        eru_img.seek(0)
        elements.append(Image(eru_img, width=5.9*inch, height=3.4*inch))
    else:
        elements.append(Paragraph("<i>No se pudo capturar el gráfico ERU.</i>", styles["Small"]))
    if sugerencia_eru:
        elements.append(Paragraph("Observaciones ERU", styles["Label"]))
        elements.append(Paragraph(sugerencia_eru.replace("\n", "<br/>"), styles["Small"]))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "Este documento presenta un resumen ejecutivo de precisión y hallazgos relevantes para ERI y ERU en el período evaluado.",
        styles["Small"]
    ))

    try:
        doc.build(elements)
        buffer.seek(0) # Importante: reiniciar la posición del buffer antes de devolverlo
        return buffer
    except Exception as e:
        st.error(f"Error al construir el PDF: {e}")
        return None


# --- Para probar la función ---
# Asegúrate de tener fig_eri, fig_eru, metricas, etc. en session_state
# st.session_state["almacen_actual"] = "Test_Almacen"
# st.session_state["metricas_eri"] = {"exactitud": 95.5, "ok": 95, "error": 5}
# st.session_state["metricas_eru"] = {"exactitud": 90.0, "ok": 90, "error": 10}
# fig_test = go.Figure(data=go.Bar(x=['A', 'B', 'C'], y=[1, 3, 2]))
# st.session_state["fig_eri"] = fig_test
# st.session_state["fig_eru"] = fig_test
