"""
Actualiza los datos embebidos del tablero CUBICA+ Plataforma.

Pasos:
1. Extrae la vista "Detalle" del tablero Tableau (Agenda picking plataforma / ERVIN)
   usando el PAT configurado en config/tableau_config.json (mismo extract_tableau.py).
2. Filtra a las 4 clases de taller/devolucion/piezas (ZSCC, ZSRT, ZSRD, ZPZA), aplica la regla de
   Caucasia aparte de Antioquia, y agrega por (FECHA_PICKING_POS, destino):
   total de pedidos, suma de cubicaje y desglose por CLASE_PEDIDO.
3. Calcula tambien el universo completo de destinos (todas las clases, sin filtrar)
   para que el filtro de departamentos los liste aunque tengan 0 pedidos en el alcance.
4. Regenera cubica_plataforma.html a partir de dashboard_template.html, incrustando
   el JSON resultante.

Uso:
    python actualizar_cubica_plataforma.py

Al terminar, el archivo cubica_plataforma.html queda listo en esta carpeta.
En GitHub Actions (.github/workflows/actualizar-tablero.yml) este script corre solo
y el HTML se publica en GitHub Pages; en local queda para revisarlo o republicarlo.
"""
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent
HORA_COLOMBIA = timezone(timedelta(hours=-5))  # Colombia no tiene horario de verano
RAW_CSV = BASE_DIR / "data" / "Detalle.csv"
TEMPLATE_HTML = BASE_DIR / "dashboard_template.html"
OUTPUT_HTML = BASE_DIR / "cubica_plataforma.html"
DATA_JSON = BASE_DIR / "data" / "cubica_data.json"

# Reglas de negocio confirmadas (ver README.md / memoria del proyecto)
CLASES_ALCANCE = {"ZSCC", "ZSRT", "ZSRD", "ZPZA"}
# Destinos fuera del alcance en todo el tablero (Bocas del Toro = Panama)
DESTINOS_EXCLUIDOS = {"BOCAS DEL TORO"}
DESC_CLASE = {
    "ZSCC": "Entrega taller",
    "ZSRT": "Recogida taller",
    "ZSRD": "Recogida devolucion",
    "ZPZA": "Entrega piezas",
}


def clean(s):
    if pd.isna(s):
        return None
    s = str(s).strip()
    return s if s not in ("", "nan") else None


def destino_de(row):
    ciudad = clean(row["NOMBRE_CIUDAD"]) or "SIN CIUDAD"
    depto = clean(row["NOMBRE_DPTO (grupo)"]) or "SIN DEPTO"
    if ciudad.upper() == "CAUCASIA":
        return "CAUCASIA"
    return depto


def extraer_de_tableau():
    subprocess.run([sys.executable, str(BASE_DIR / "extract_tableau.py")], check=True, cwd=BASE_DIR)


def construir_raw():
    df = pd.read_csv(RAW_CSV, sep=";", encoding="utf-8", dtype=str)
    df["destino"] = df.apply(destino_de, axis=1)
    df = df[~df["destino"].isin(DESTINOS_EXCLUIDOS)]
    df["cubicaje_num"] = df["CUBICAJE"].apply(
        lambda v: float(str(v).replace(",", ".")) if clean(v) is not None else 0.0
    )
    df["fecha_iso"] = pd.to_datetime(df["FECHA_PICKING_POS"], dayfirst=True, errors="coerce").dt.strftime("%Y-%m-%d")

    destinos = sorted(df["destino"].dropna().unique().tolist())

    scope = df[df["CLASE_PEDIDO"].isin(CLASES_ALCANCE) & df["fecha_iso"].notna()]

    resumen_grp = scope.groupby(["fecha_iso", "destino"], as_index=False).agg(
        total_ordenes=("NUM_PEDIDO_SAP", "count"),
        cubicaje_total=("cubicaje_num", "sum"),
    )
    resumen = []
    for _, r in resumen_grp.sort_values(["fecha_iso", "destino"]).iterrows():
        resumen.append({
            "fecha": r["fecha_iso"],
            "departamento": r["destino"],
            "total_ordenes": int(r["total_ordenes"]),
            "ordenes_ocupadas": 0,
            "cubicaje_total": round(float(r["cubicaje_total"]), 2),
            "cubicaje_ocupado": 0.0,
        })

    scope = scope.copy()
    scope["municipio"] = scope["NOMBRE_CIUDAD"].apply(lambda v: clean(v) or "SIN CIUDAD")

    detalle_grp = scope.groupby(["fecha_iso", "destino", "municipio", "CLASE_PEDIDO"], as_index=False).agg(
        total=("NUM_PEDIDO_SAP", "count"),
    )
    detalle = {}
    for _, r in detalle_grp.sort_values(["fecha_iso", "destino", "municipio", "total"], ascending=[True, True, True, False]).iterrows():
        key = f"{r['fecha_iso']}|{r['destino']}"
        detalle.setdefault(key, []).append({
            "municipio": r["municipio"],
            "clase": r["CLASE_PEDIDO"],
            "desc": DESC_CLASE.get(r["CLASE_PEDIDO"], r["CLASE_PEDIDO"]),
            "grupo": "POSVENTA",
            "total": int(r["total"]),
            "ocupado": 0,
        })

    raw = {"resumen": resumen, "detalle": detalle, "destinos": destinos, "pedidos": construir_pedidos(scope)}

    with open(DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)

    return raw, len(scope)


def construir_pedidos(scope):
    """Detalle pedido a pedido para la descarga a Excel del tablero.

    Solo columnas operativas: NO incluir cedula, nombre, direccion, barrio, senas,
    telefonos ni VALOR_OFERTA (la pagina es publica)."""
    def num(v):
        v = clean(v)
        try:
            return float(v.replace(",", ".")) if v is not None else None
        except ValueError:
            return None

    def fecha(v):
        f = pd.to_datetime(clean(v), dayfirst=True, errors="coerce")
        return None if pd.isna(f) else f.strftime("%Y-%m-%d")

    filas = []
    for _, r in scope.sort_values(["fecha_iso", "destino", "municipio", "NUM_PEDIDO_SAP"]).iterrows():
        filas.append([
            r["fecha_iso"], fecha(r["FECHA_CITA"]), r["destino"], r["municipio"],
            r["CLASE_PEDIDO"], DESC_CLASE.get(r["CLASE_PEDIDO"], r["CLASE_PEDIDO"]),
            clean(r["NUM_PEDIDO_SAP"]), clean(r["NUMERO_PEDIDO_SEUS"]), clean(r["ESTADO_SEUS"]),
            num(r["CUBICAJE"]), num(r["PESO_BRUTO"]),
            clean(r["DEPARTAMENTO_RUTA"]), clean(r["PUESTO_EXPEDICION"]),
            clean(r["NUM_VIAJE_TRAMO_1"]), clean(r["NUM_ENTREGA_TRAMO_1"]),
            clean(r["NUM_VIAJE_TRAMO_2"]), clean(r["NUM_ENTREGA_TRAMO_2"]),
        ])
    return filas


def regenerar_html(raw):
    with open(TEMPLATE_HTML, "r", encoding="utf-8") as f:
        template = f.read()

    raw_json = json.dumps(raw, ensure_ascii=False, separators=(",", ":"))
    raw_json_safe = raw_json.replace("</script", "<\\/script")

    generado = datetime.now(HORA_COLOMBIA).strftime("%d/%m/%Y %I:%M %p").replace("AM", "a. m.").replace("PM", "p. m.")

    html = template.replace("__RAW_JSON__", raw_json_safe).replace("__GENERADO__", generado)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    print("1/3 Extrayendo datos del tablero Tableau...")
    extraer_de_tableau()

    print("2/3 Agregando pedidos taller/devolucion por (fecha, destino)...")
    raw, n = construir_raw()
    print(f"    {n} pedidos en alcance, {len(raw['resumen'])} combinaciones fecha-destino, {len(raw['destinos'])} destinos en el universo")

    print("3/3 Regenerando cubica_plataforma.html...")
    regenerar_html(raw)

    print()
    print(f"Listo: {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
