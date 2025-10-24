import re
import pandas as pd

ubicacion_pattern = r'R\d{1,3}[A-Z]-[A-Z]-\d{1,3}$'
ubicacion_pattern_alt = r'R\d{1,3}[A-Z]-[A-Z]-[A-Z]$'
ubicacion_pattern_alt2 = r'R\d{1,3}-[A-Z]-\d{1,3}$'
ubicacion_pattern_alt3 = r'R\d{1,3}-[A-Z]-[A-Z]$'

def desconcatenar_producto_ref(clave_completa, ubicaciones_teoricas, stock_teorico_eri):
    """Extrae clave_teorica_eri y ubicación de un código ERU."""
    # 🧹 Limpieza de ubicaciones (evita float, NaN, vacíos)
    ubicaciones_validas = [
        str(u).strip()
        for u in ubicaciones_teoricas
        if pd.notna(u) and str(u).strip() != ""
    ]

    # Si no hay ubicaciones válidas, abortar temprano
    if not ubicaciones_validas:
        return None, None

    # 🔍 Buscar coincidencias exactas al final del código
    for ub_teorica in sorted(ubicaciones_validas, key=len, reverse=True):
        if clave_completa.endswith(ub_teorica):
            parte_producto_ref = clave_completa[:-len(ub_teorica)]
            for i in range(len(parte_producto_ref)):
                producto_codigo = parte_producto_ref[:i]
                referencia1 = parte_producto_ref[i:]
                clave_teorica = producto_codigo + "_" + referencia1
                if clave_teorica in stock_teorico_eri['clave_teorica_eri'].values:
                    return clave_teorica, ub_teorica

    # 🔎 Alternativa: buscar patrones válidos de ubicación
    for _, row in stock_teorico_eri.iterrows():
        if clave_completa.startswith(row['clave_teorica_eri']):
            ubicacion_extraida = clave_completa[len(row['clave_teorica_eri']):]
            if (re.search(ubicacion_pattern, ubicacion_extraida) or
                re.search(ubicacion_pattern_alt, ubicacion_extraida) or
                re.search(ubicacion_pattern_alt2, ubicacion_extraida) or
                re.search(ubicacion_pattern_alt3, ubicacion_extraida)):
                return row['clave_teorica_eri'], ubicacion_extraida

    return None, None
