# CUBICA+ Plataforma

Tablero de cierre de agenda de picking (taller, devoluciones y piezas) por destino, construido replicando el patrón visual y de datos de **CUBICA+** (ver [`Arquitectura del Dashboard CUBICA+.md`](./Arquitectura%20del%20Dashboard%20CUBICA+.md)), pero aplicado a la agenda de picking de "plataforma" en vez del dashboard-poligono original de Jamar Admin.

**Publicación:** GitHub Pages, actualizado automáticamente (ver *Actualización automática*). Copia manual en claude.ai: https://claude.ai/artifact/6ukrWozyfgbVvd6Y3CqNuG
(HTML autocontenido, datos embebidos — no se conecta en vivo a Tableau; es una foto del extracto vigente al momento de publicarlo).

**Última actualización local de datos:** 22/09/2026 — 431 pedidos (taller, devolución y piezas), 69 combinaciones fecha-destino.

## Qué muestra

Dos modos de vista, con el mismo filtro de departamentos (selección múltiple) y de orden (más pedidos / menor ocupación / alfabético):

### Foto del día (default)

Una tarjeta por destino (departamento, con Caucasia separada de Antioquia — ver regla 1 abajo) para la fecha de picking seleccionada (selector con navegación ◀▶), con:

- Badge "Abierto" + badge de alerta "Capacidad llena" cuando se llena la capacidad del día.
- Dos barras de progreso: **Cubicaje** (m³ agendados / capacidad) y **Servicios** (pedidos agendados / capacidad).
- Desglose expandible ("Ver detalle") con una tabla combinada Municipio × `CLASE_PEDIDO` (cantidad de pedidos y % del total del día por cada municipio/clase).

### Mapa de calor

Toggle "VISTA" → matriz con una fila por destino y una columna por cada uno de 30 días corridos de calendario (sin saltar días vacíos), empezando en la primera fecha con datos. Cada celda es un día: número = % de ocupación (mayor entre cubicaje y servicios), coloreado con el mismo semáforo; celda gris = sin agenda ese día; línea punteada = cambio de mes. El resumen superior pasa a mostrar totales del rango completo (30 días × capacidad diaria de cada destino — ver regla 2).

**Drill-down:** clic en cualquier celda con datos abre, justo debajo de la fila de ese destino, la misma tarjeta de detalle que en "Foto del día" (badges, barras, desglose por municipio y clase) para ese destino y ese día puntual. Clic de nuevo sobre la celda (o sobre otra) la cierra/reemplaza.

## Semáforo de ocupación

| Color | Rango | Significado |
|---|---|---|
| 🟡 Ámbar | < 40% | Ocupación baja |
| 🔵 Azul | 40% – 79% | Ocupación media |
| 🟢 Verde | 80% – 99% | Ocupación alta |
| 🔴 Rojo | ≥ 100% | Capacidad llena o superada |

## Fuente de datos

`data/Detalle.csv` — extracto propio del tablero Tableau "Agenda picking plataforma / ERVIN", vista "Detalle" (ver [`extract_tableau.py`](./extract_tableau.py) y `config/tableau_config.json`, con el mismo PAT y `VIEW_ID` que usa `Torre de control planeacion/config/tableau_config.json`). Es la misma fuente completa (no el Excel manual parcial) que también extrae la Torre de Control (ver [`README.md`](../Torre%20de%20control%20planeacion/README.md) del proyecto hermano) — cada dashboard mantiene su propia copia local del CSV.

## Reglas de negocio (confirmadas con el usuario)

1. **Caucasia es un destino aparte, no se mezcla con Antioquia.** Tiene ruta logística propia (`DEPARTAMENTO_RUTA` = "C2 - CAUCASIA" vs. "RE - ANTIOQUIA" del resto). Se agrupa por `NOMBRE_CIUDAD` antes que por `NOMBRE_DPTO (grupo)` cuando la ciudad es Caucasia. El filtro de departamentos lista Caucasia aunque tenga 0 pedidos en el alcance actual (universo completo de destinos, no solo los que tienen datos).
2. **Capacidad por vehículo: 18 servicios y 18 m³ por vehículo por día.** Es una constante de negocio (no viene del dato). Cada destino tiene un número de vehículos; la capacidad diaria del destino = vehículos × 18. Las barras se llenan contra la capacidad de su destino, no contra el total agendado. En la vista de mapa de calor la capacidad del rango es 30 × la capacidad diaria de cada destino.

   | Destino | Vehículos | Capacidad diaria |
   |---|---|---|
   | Antioquia | 2 | 36 servicios / 36 m³ |
   | Resto (incluida Caucasia) | 1 | 18 servicios / 18 m³ |

   Aplica todos los días de la semana (22/09/2026). Para cambiar la cantidad de vehículos de un destino, editar `VEHICULOS_POR_DESTINO` en `dashboard_template.html` (ej. `{ANTIOQUIA: 2, ATLANTICO: 2}`; los destinos no listados valen 1) y volver a correr el script.
3. **Criterio de alerta:** el destino/día queda en alerta cuando cubicaje ≥ capacidad del destino en m³ **o** servicios ≥ capacidad del destino (lo que se llene primero; ej. 18 en la mayoría, 36 en Antioquia). El estado nunca se muestra como "Cerrado" — siempre "Abierto", con el badge de alerta adicional si se llenó.
4. **Alcance de pedidos: taller, devolución y piezas** — `ZSCC` (Entrega taller), `ZSRT` (Recogida taller), `ZSRD` (Recogida devolución), `ZPZA` (Entrega piezas). Se excluyen venta, traslados (`ZTRC`) y las 4 clases de cambio total/parcial (`ZSRC`, `ZSCE`, `ZRCP`, `ZSCP`). Catálogo completo en la memoria del proyecto / `catalogo_clase_pedido.md`.
5. **No se usa el cruce de validación Salesforce** (campo `v` del extracto anterior) — la ocupación se mide contra la capacidad por destino, no contra el estado de validación del caso.
6. **La fecha es `FECHA_PICKING_POS`** (fecha de picking), no `FECHA_CITA` (fecha de entrega al cliente) — son campos distintos en `Detalle.csv`.

## Cómo se generan los datos embebidos

El HTML no lee `Detalle.csv` en vivo (los artifacts son estáticos). `actualizar_cubica_plataforma.py` automatiza todo el proceso (mismo patrón que `../actualizar_torre_control.py` para el dashboard hermano):

1. Refresca `data/Detalle.csv` corriendo `extract_tableau.py`.
2. Agrega por `(FECHA_PICKING_POS, destino)` — total de pedidos y suma de cubicaje, filtrando a las 4 clases de la regla 4 y aplicando la regla 1 (Caucasia aparte), con desglose por municipio y clase. También calcula el universo completo de destinos (todas las clases, sin filtrar) para que el filtro de departamentos los liste aunque tengan 0 pedidos en el alcance actual. Guarda el resultado en `data/cubica_data.json`.
3. Inyecta ese JSON en `dashboard_template.html` (plantilla con el marcador `__RAW_JSON__`, extraída del artifact publicado) y genera `cubica_plataforma.html`.

Uso local: `python actualizar_cubica_plataforma.py` (lee el PAT de `config/tableau_config.json`).

## Actualización automática (GitHub Actions + GitHub Pages)

El workflow `.github/workflows/actualizar-tablero.yml` corre el script en los servidores de GitHub — no depende de que el PC esté encendido — y publica el HTML en GitHub Pages.

- **Horario:** cada hora de 6:00 a 18:00 (hora Colombia), lunes a sábado (`cron: "0 11-23 * * 1-6"`, en UTC). GitHub puede retrasar unos minutos las corridas programadas.
- **Manual:** pestaña *Actions* → *Actualizar tablero CUBICA+ Plataforma* → *Run workflow*.
- **Credenciales:** el PAT de Tableau va en *Settings → Secrets and variables → Actions* como `TABLEAU_TOKEN_NAME` y `TABLEAU_TOKEN_SECRET`. `extract_tableau.py` los usa si existen; si no, lee `config/tableau_config.json`.
- **Datos personales:** `data/Detalle.csv` trae cédula, nombre, dirección y teléfono de clientes. Está en `.gitignore` y el workflow solo publica `index.html`, que contiene conteos agregados (fecha, destino, municipio, clase, cubicaje). **Nunca subir la carpeta `data/` ni `config/`.**
- **Visibilidad:** con un plan gratuito de GitHub, la página de Pages es pública para cualquiera que tenga el link (tiene `noindex` para que no aparezca en buscadores). Solo GitHub Enterprise permite Pages privado.
- **Cambios al tablero:** editar `dashboard_template.html` o el script y hacer push; la siguiente corrida los toma.

### Configuración inicial (una sola vez)

1. Crear el repositorio en GitHub y subir esta carpeta (el `.gitignore` excluye `config/`, `data/`, el Excel y los HTML generados).
2. *Settings → Secrets and variables → Actions → New repository secret*: `TABLEAU_TOKEN_NAME` y `TABLEAU_TOKEN_SECRET`.
3. *Settings → Pages → Build and deployment → Source*: **GitHub Actions**.
4. *Actions → Actualizar tablero CUBICA+ Plataforma → Run workflow* y revisar que termine en verde. Si falla en el paso "Extraer de Tableau" con un timeout o error de conexión, el firewall de Jamar está bloqueando a GitHub: hay que pedirle a TI que permita el acceso a `elena.mueblesjamar.com.co`.
5. El link del tablero queda en *Settings → Pages* (formato `https://<usuario>.github.io/<repositorio>/`).

El artifact de claude.ai (https://claude.ai/artifact/6ukrWozyfgbVvd6Y3CqNuG) deja de actualizarse solo; se puede seguir republicando a mano con Claude si se quiere mantener.

## Pendiente

- Conectar la capacidad (vehículos por destino × 18 servicios / 18 m³) con datos reales de flota si se define una fuente distinta al mapa fijo `VEHICULOS_POR_DESTINO`.
- Soportar capacidad variable por día de la semana si algún destino no tiene la misma cantidad de vehículos todos los días.
- Revisar `Frecuencia de viaje Plataforma -08-09-2026..XLSX` (en esta misma carpeta) como posible fuente de capacidad real por viaje/destino.
