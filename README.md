# CUBICA+ Plataforma

Tablero de cierre de agenda de picking (taller, devoluciones y piezas) por destino, construido replicando el patrón visual y de datos de **CUBICA+** (ver [`Arquitectura del Dashboard CUBICA+.md`](./Arquitectura%20del%20Dashboard%20CUBICA+.md)), pero aplicado a la agenda de picking de "plataforma" en vez del dashboard-poligono original de Jamar Admin.

**Tablero:** https://ervintrujillorojas-code.github.io/Cubica-plataforma/

**Repositorio:** https://github.com/ervintrujillorojas-code/Cubica-plataforma

HTML autocontenido con datos embebidos: no se conecta en vivo a Tableau, es una foto del extracto de la última corrida. Se regenera sola cada hora (minuto 17) de 6:17 a 18:17, lunes a sábado (ver *Actualización automática*). La hora de la última actualización se ve en la pestaña *Actions* del repositorio.

## Versiones

La versión y la hora de la última actualización de datos se muestran al pie del tablero. La versión se cambia a mano en `dashboard_template.html` (bloque `version-bar`) con cada ajuste al tablero; la hora la pone el script en cada corrida (hora Colombia).

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0 | 18/09/2026 | Tablero inicial: foto del día por destino, capacidad fija 18 serv / 18 m³, Caucasia aparte de Antioquia |
| 1.1 | 21/09/2026 | Se agrega ZPZA (entrega piezas), mapa de calor con drill-down y tabla combinada Municipio × Clase |
| 1.2 | 22/09/2026 | Capacidad por vehículos: Antioquia con 2 vehículos (36 / 36) |
| 1.3 | 23/09/2026 | Publicación automática en GitHub Pages (cada hora) y pie con versión y hora de actualización |
| 1.4 | 23/09/2026 | Filtro de Plataforma (Galapa, Bogotá, Medellín) y exclusión de Bocas del Toro (Panamá) |
| 1.5 | 23/09/2026 | Botón *Descargar Excel* con el detalle pedido a pedido según vista y filtros |
| 1.6 | 23/09/2026 | Se agrega ZSN1 (Devolución nota de cambio) al alcance; se excluye también el destino PANAMA |

## Qué muestra

Dos modos de vista, con el mismo filtro de plataforma, de departamentos (selección múltiple) y de orden (más pedidos / menor ocupación / alfabético):

### Foto del día (default)

Una tarjeta por destino (departamento, con Caucasia separada de Antioquia — ver regla 1 abajo) para la fecha de picking seleccionada (selector con navegación ◀▶), con:

- Badge "Abierto" + badge de alerta "Capacidad llena" cuando se llena la capacidad del día.
- Dos barras de progreso: **Cubicaje** (m³ agendados / capacidad) y **Servicios** (pedidos agendados / capacidad).
- Desglose expandible ("Ver detalle") con una tabla combinada Municipio × `CLASE_PEDIDO` (cantidad de pedidos y % del total del día por cada municipio/clase).

### Mapa de calor

Toggle "VISTA" → matriz con una fila por destino y una columna por cada uno de 30 días corridos de calendario (sin saltar días vacíos), empezando en la primera fecha con datos. Cada celda es un día: número = % de ocupación (mayor entre cubicaje y servicios), coloreado con el mismo semáforo; celda gris = sin agenda ese día; línea punteada = cambio de mes. El resumen superior pasa a mostrar totales del rango completo (30 días × capacidad diaria de cada destino — ver regla 2).

**Drill-down:** clic en cualquier celda con datos abre, justo debajo de la fila de ese destino, la misma tarjeta de detalle que en "Foto del día" (badges, barras, desglose por municipio y clase) para ese destino y ese día puntual. Clic de nuevo sobre la celda (o sobre otra) la cierra/reemplaza.

### Descargar Excel

Botón *Descargar Excel* en el panel de filtros. Descarga un `.xlsx` con **un pedido por fila** del alcance del tablero, respetando los filtros:

- **Foto del día:** los pedidos de la fecha de picking seleccionada.
- **Mapa de calor:** todos los pedidos de los 30 días del rango.
- En ambos casos, solo de la plataforma y los departamentos seleccionados.

Columnas: Fecha picking, Fecha cita, Plataforma, Destino, Municipio, Clase pedido, Descripción clase, N° pedido SAP, N° pedido SEUS, Estado SEUS, Cubicaje (m³), Peso bruto, Departamento ruta, Puesto expedición, N° viaje / entrega tramo 1 y 2.

**No incluye** cédula, nombre del cliente, dirección, barrio, señas, teléfonos ni `VALOR_OFERTA`: la página es pública y esos datos viajarían embebidos en ella. Las columnas se definen en `construir_pedidos()` de `actualizar_cubica_plataforma.py`; **no agregar datos personales mientras el tablero sea público.** El Excel se arma en el navegador con SheetJS (cargado desde cdn.jsdelivr.net solo al hacer clic).

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
4. **Alcance de pedidos: taller, devolución y piezas** — `ZSCC` (Entrega taller), `ZSRT` (Recogida taller), `ZSRD` (Recogida devolución), `ZPZA` (Entrega piezas), `ZSN1` (Devolución nota de cambio, agregada 23/09/2026). Se excluyen venta, traslados (`ZTRC`) y las 4 clases de cambio total/parcial (`ZSRC`, `ZSCE`, `ZRCP`, `ZSCP`). Catálogo completo en la memoria del proyecto / `catalogo_clase_pedido.md`.
5. **No se usa el cruce de validación Salesforce** (campo `v` del extracto anterior) — la ocupación se mide contra la capacidad por destino, no contra el estado de validación del caso.
6. **La fecha es `FECHA_PICKING_POS`** (fecha de picking), no `FECHA_CITA` (fecha de entrega al cliente) — son campos distintos en `Detalle.csv`.
7. **Plataformas:** cada destino pertenece a una plataforma; el filtro *Plataforma* limita la lista de departamentos (y todos los totales) a los de esa plataforma. Se define en `PLATAFORMAS` dentro de `dashboard_template.html`.

   | Plataforma | Destinos |
   |---|---|
   | Galapa | Atlántico, Bolívar, Magdalena, Cesar, Córdoba, Guajira, Sucre, Caucasia, Santander |
   | Bogotá | Cundinamarca, Meta, Boyacá |
   | Medellín | Antioquia |

8. **Panamá se excluye de todo el tablero** (el extracto lo trae como `BOCAS DEL TORO` o `PANAMA`) (`DESTINOS_EXCLUIDOS` en `actualizar_cubica_plataforma.py`).

## Cómo se generan los datos embebidos

El HTML no lee `Detalle.csv` en vivo (es una página estática). `actualizar_cubica_plataforma.py` automatiza todo el proceso (mismo patrón que `../actualizar_torre_control.py` para el dashboard hermano):

1. Refresca `data/Detalle.csv` corriendo `extract_tableau.py`.
2. Agrega por `(FECHA_PICKING_POS, destino)` — total de pedidos y suma de cubicaje, filtrando a las 5 clases de la regla 4 y aplicando la regla 1 (Caucasia aparte), con desglose por municipio y clase. También calcula el universo completo de destinos (todas las clases, sin filtrar) para que el filtro de departamentos los liste aunque tengan 0 pedidos en el alcance actual. Guarda el resultado en `data/cubica_data.json`.
3. Inyecta ese JSON en `dashboard_template.html` (plantilla con el marcador `__RAW_JSON__`, extraída del artifact publicado) y genera `cubica_plataforma.html`.

Uso local: `python actualizar_cubica_plataforma.py` (lee el PAT de `config/tableau_config.json`).

## Actualización automática (GitHub Actions + GitHub Pages)

El workflow `.github/workflows/actualizar-tablero.yml` corre el script en los servidores de GitHub — no depende de que el PC esté encendido — y publica el HTML en GitHub Pages.

- **Horario:** cada hora al minuto 17, de 6:17 a 18:17 (hora Colombia), lunes a sábado (`cron: "17 11-23 * * 1-6"`, en UTC). Se evita la hora en punto porque GitHub retrasa o descarta más corridas programadas a esa hora; aun así no están garantizadas. Si se siguen saltando horas, la alternativa es un disparador externo (p. ej. cron-job.org llamando a *workflow_dispatch*). Si el repo pasa 60 días sin cambios, GitHub desactiva las corridas programadas.
- **Manual:** pestaña *Actions* → *Actualizar tablero CUBICA+ Plataforma* → *Run workflow*.
- **Credenciales:** el PAT de Tableau va en *Settings → Secrets and variables → Actions* como `TABLEAU_TOKEN_NAME` y `TABLEAU_TOKEN_SECRET`. `extract_tableau.py` los usa si existen; si no, lee `config/tableau_config.json`.
- **Datos personales:** `data/Detalle.csv` trae cédula, nombre, dirección y teléfono de clientes. Está en `.gitignore` y el workflow solo publica `index.html`, que contiene conteos agregados (fecha, destino, municipio, clase, cubicaje). **Nunca subir la carpeta `data/` ni `config/`.**
- **Visibilidad:** con un plan gratuito de GitHub, la página de Pages es pública para cualquiera que tenga el link (tiene `noindex` para que no aparezca en buscadores). Solo GitHub Enterprise permite Pages privado.
- **Cambios al tablero:** editar el archivo en GitHub (abrir el archivo → tecla `e` o cambiar `/blob/` por `/edit/` en la URL → *Commit changes*) o subirlo con *Add file → Upload files* **estando en la raíz del repositorio**. La siguiente corrida los toma; para verlos de inmediato, *Run workflow*. La carpeta local del PC no se sincroniza sola con GitHub.

### Configuración inicial (hecha el 22/09/2026)

1. Repositorio público creado en GitHub. Los archivos se subieron por la web (el PC no tiene Git): la carga web ignora archivos que empiezan con punto, así que `.gitignore` y `.github/workflows/actualizar-tablero.yml` se crearon con *Add file → Create new file*.
2. *Settings → Secrets and variables → Actions*: secretos `TABLEAU_TOKEN_NAME` y `TABLEAU_TOKEN_SECRET`.
3. *Settings → Pages → Source*: **GitHub Actions**.
4. Primera corrida exitosa: GitHub sí llega a `elena.mueblesjamar.com.co` (no hay bloqueo de firewall).

### Si una corrida falla

GitHub envía un correo. En *Actions*, abrir la corrida en rojo → *actualizar* → el paso con ❌:

| Error | Causa | Solución |
|---|---|---|
| `401001 ... token de acceso personal ... no es válido` | Secreto mal copiado, o el PAT venció / fue revocado en Tableau | Revisar los dos secretos (sin comillas ni espacios; `TABLEAU_TOKEN_SECRET` lleva un `:` en medio). Si el PAT venció, generar uno nuevo en Tableau y actualizar ambos secretos (y `config/tableau_config.json` en local) |
| Timeout / connection refused en "Extraer de Tableau" | Tableau caído o firewall bloqueando a GitHub | Probar más tarde; si persiste, escalar a TI |
| `No such file` / `can't open file` | Algún archivo quedó fuera de la raíz del repo | Mover el archivo a la raíz (editar → borrar la carpeta del nombre con Backspace) |
| Falla en "deploy" | Pages no está en *GitHub Actions* | *Settings → Pages → Source: GitHub Actions* |

Copia anterior del tablero en claude.ai (ya no se actualiza sola, se puede republicar a mano con Claude): https://claude.ai/artifact/6ukrWozyfgbVvd6Y3CqNuG

## Pendiente

- Conectar la capacidad (vehículos por destino × 18 servicios / 18 m³) con datos reales de flota si se define una fuente distinta al mapa fijo `VEHICULOS_POR_DESTINO`.
- Soportar capacidad variable por día de la semana si algún destino no tiene la misma cantidad de vehículos todos los días.
- Revisar `Frecuencia de viaje Plataforma -08-09-2026..XLSX` (en esta misma carpeta) como posible fuente de capacidad real por viaje/destino.
