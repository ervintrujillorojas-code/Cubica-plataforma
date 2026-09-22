# Arquitectura del Dashboard CUBICA+

2026-09-18 · @Ervin

## Resumen ejecutivo

CUBICA+ es el módulo de Jamar Admin que hace seguimiento en tiempo real al cierre de picking por polígono/bodega: cuánto cubicaje y cuántas órdenes se han ocupado frente al total disponible del día. El **DASHBOARD CUBICA+** (`#/admin/logistica/dashboard-poligono`) es la vista de seguimiento: un panel de filtros arriba y, debajo, una tarjeta por polígono con dos barras de progreso (cubicaje y órdenes), un badge de estado (Abierto/Cerrado) y acciones rápidas (exportar Excel, ver detalle).

Este documento describe el patrón de arquitectura de esa pantalla — stack, contrato de datos, estructura de componentes y sistema visual — para que pueda reutilizarse tal cual en un dashboard nuevo, cambiando solo la fuente de datos y las métricas mostradas.

## Stack tecnológico

**Frontend:** Angular 12.2.17, SPA con hash routing (`#/admin/logistica/dashboard-poligono`), empaquetado en tres bundles (`runtime`, `polyfills`, `main`) más una sola hoja `styles.css` — build estándar de Angular CLI. Usa **Angular Material** solo para iconografía (`mat-icon` + Material Icons: `inventory_2`, `receipt_long`, `visibility`, `description`…) y controles de formulario (autocomplete de bodega, date picker), combinado con **Bootstrap** para grilla y tarjetas (`card`, `card-body`, `mb-4`, `row`/`col`).

**Backend:** serverless en AWS — API Gateway + Lambda, stage `prd`, rutas versionadas `api/v1/...` (ej. `capacidades_poligono`). El frontend llama estos endpoints directo por HTTPS desde el `HttpClient` de Angular, sin backend-for-frontend intermedio visible.

**Tipografía y hosting:** familia base `Karla`/`Poppins`, fondo de página `#F8F9FE`; servido desde `nova.appsjamar.com`.

## Arquitectura de datos

Cada búsqueda del dashboard dispara un `POST` al endpoint de capacidades, con la bodega y fecha seleccionadas:

```
POST https://th2py80lcd.execute-api.us-east-1.amazonaws.com/prd/api/v1/capacidades_poligono

{ "empresa": "JA", "fecha_picking": "2026-09-18", "codigo_bodega": "72" }
```

La respuesta trae un arreglo `data`, un objeto por polígono, con los campos ya calculados en el backend (el frontend no recalcula porcentajes):

| Campo | Tipo | Uso en la tarjeta |
| --- | --- | --- |
| `NOMBRE_POLIGONO` | texto | Título de la tarjeta |
| `COD_POLIGONO` / `POLIGONO` | texto / número | Identificador interno |
| `CUBICAJE_OCUPADO` / `CUBICAJE_TOTAL` | decimal | Fracción "78.06 / 160" |
| `CANT_ORDENES_OCUPADO` / `CANTIDAD_ORD_TOTAL` | entero | Fracción "69 / 160" |
| `PORC_AVANCE_CUBICAJE` | decimal (0-100) | Ancho y color de la barra de cubicaje |
| `PORC_AVANCE_ORDENES` | decimal (0-100) | Ancho y color de la barra de órdenes |
| `ESTADO_DIA` | `"C"` / `"A"` | Badge Cerrado/Abierto |
| `CIERRE_AUTOMATICO`, `PORCENTAJE_CIERRE` | flags | Reglas de cierre automático del polígono |

Patrón a replicar: **el backend entrega los porcentajes ya calculados**, no crudos; el componente Angular solo los mapea a ancho de barra y clase de color. Esto es clave para que un dashboard nuevo sea igual de simple: la lógica de negocio (umbrales, metas) vive en el Lambda, no en el frontend.

## Estructura de la interfaz

```
AppShell
├─ Header (logo, buscador global, avatar de cuenta)
├─ Sidebar (árbol de navegación, módulo activo resaltado)
└─ ContentArea
   ├─ Título de página ("DASHBOARD SEGUIMIENTO CUBICA+")
   ├─ FiltrosPanel (tarjeta con fondo oscuro en su header)
   │  ├─ Autocomplete "Código Bodega"
   │  ├─ DatePicker "Fecha"
   │  ├─ Botón buscar
   │  ├─ Toggle "Vista 30 días"
   │  ├─ Botón descargar reporte
   │  └─ Botón de acción masiva ("Gestionar servicios del día")
   └─ GridDeTarjetas (una IndicadorCard por polígono devuelto por la API)
```

Es el patrón clásico de dashboard operativo: **filtros arriba, resultados abajo en grilla de tarjetas**, sin gráficas complejas — cada tarjeta ya es en sí misma un mini-KPI visual. El grid es responsivo (Bootstrap `row`/`col`): dos tarjetas por fila en escritorio, una por fila en móvil.

## Anatomía de la tarjeta de indicador (`IndicadorCard`)

Cada tarjeta (`card mb-4`, fondo blanco, `border-radius: 12px`, sombra suave) tiene siempre el mismo orden de elementos:

1. **Badge de estado** (`estado-badge cerrado/abierto`) — esquina superior izquierda, rojo si está cerrado.
2. **Toggle** (esquina superior derecha) — abrir/cerrar el polígono manualmente.
3. **Título** (`poly-title`, `<h2>`) — nombre del polígono/bodega.
4. **Fila de métricas crudas** — dos columnas de texto: "Cubicaje: 78.06 / 160" y "Órdenes: 69 / 160".
5. **Dos barras de progreso** (`progress-bar` > `progress-fill`), una por métrica, cada una con: icono Material a la izquierda, etiqueta ("Cubicaje"/"Órdenes"), porcentaje a la derecha, y ancho = `PORC_AVANCE_*`.
6. **Acciones** — dos botones al pie: "Descargar Excel" (exporta esa fila) y "Ver detalle" (drill-down, probablemente un modal o navegación a vista detallada por polígono).

Este patrón —badge + título + fracción cruda + barra(s) de progreso + acciones— es el bloque reutilizable: para un dashboard nuevo basta con mapear las métricas propias del dominio a esos mismos cinco elementos.

## Sistema visual

| Elemento | Valor | Uso |
| --- | --- | --- |
| Fondo de página | `#F8F9FE` | Contraste sutil detrás de tarjetas blancas |
| Tarjeta | blanco, `border-radius: 12px`, sombra `0 8px 20px rgba(0,0,0,.15)`, `padding: 20px` | Contenedor de cada indicador |
| Badge "Cerrado" | fondo `#E53935` (rojo), texto blanco, `border-radius: 4px`, `700` | Estado negativo/alerta |
| Barra — estado bajo (`low`) | `#2196F3` (azul) | Avance por debajo del umbral esperado |
| Barra — estado normal (`normal`) | `#4CAF50` (verde) | Avance dentro de meta |
| Barra — estado alerta (`progress-alert`) | `#FFB300` (ámbar) | Zona de advertencia intermedia |
| Barras | `border-radius: 14px`, texto blanco `700` dentro del relleno | Ancho dinámico = % de avance |
| Iconografía | Material Icons vía `mat-icon` | `inventory_2`, `receipt_long`, `visibility`, `description`, `search`, `file_download` |
| Tipografía | `Karla`/`Poppins` (página), `Segoe UI` (dentro de tarjetas) | Jerarquía título/cuerpo |

La regla de color no es decorativa: **el color de cada barra codifica el estado del KPI** (bajo/normal/alerta), no el tipo de métrica — es el mismo semaforo aplicado a cubicaje y a órdenes por igual. Al replicar el patrón, conviene mantener esta misma tríada azul/verde/ámbar (más rojo para "cerrado"/error) en vez de inventar una paleta nueva, para que el usuario reconozca el lenguaje visual entre módulos.

## Patrones de interacción

- **Filtro obligatorio + búsqueda explícita:** el usuario elige bodega (autocomplete) y fecha (date picker, default hoy) y presiona el botón de lupa; no hay refresco automático. Cada búsqueda dispara un solo `POST` que trae todos los polígonos de esa bodega/fecha.
- **Toggle "Vista 30 días":** cambia el modo de la misma pantalla de "foto de un día" a una serie de 30 días, reutilizando el mismo layout de tarjetas/filtros.
- **Exportar:** dos niveles — "Descargar reporte" a nivel de toda la búsqueda, y "Descargar Excel" por tarjeta individual.
- **Drill-down ("Ver detalle"):** cada tarjeta tiene su propio botón de detalle, para pasar de la vista agregada por polígono a la vista granular (órdenes/registros individuales) sin salir del contexto del dashboard.
- **Acción masiva separada:** "Gestionar servicios del día" abre un flujo aparte para cerrar/abrir masivamente, en vez de mezclar esa acción dentro de cada tarjeta.
- **Toggle por tarjeta:** cada tarjeta trae su propio switch para abrir/cerrar ese polígono puntual, independiente de la acción masiva.

En conjunto, el dashboard sigue el patrón *filtrar → visualizar en tarjetas → accionar (exportar / detalle / cerrar)*, sin navegar fuera de la pantalla salvo para el detalle.

## Recomendaciones para replicar

1. **Define la métrica y su unidad natural de agrupación** (aquí: polígono/bodega). Cada tarjeta representa una unidad de negocio, no un registro individual.
2. **Pide al backend el porcentaje ya calculado**, no los valores crudos por separado — replica el contrato `{ocupado, total, porc_avance, estado}` por métrica en un endpoint Lambda propio (mismo patrón API Gateway + Lambda, stage `prd`, `api/v1/<recurso>`).
3. **Reutiliza el componente `IndicadorCard`** (badge + título + fracción + barra(s) + acciones) en vez de diseñar una tarjeta nueva; solo cambian las métricas que se mapean a cada barra.
4. **Mantén la paleta semáforo** (`#2196F3` bajo / `#4CAF50` normal / `#FFB300` alerta / `#E53935` cerrado-error) para que el usuario reconozca el mismo lenguaje visual entre dashboards de Jamar Admin.
5. **Panel de filtros consistente**: bodega + fecha + botón buscar como mínimo; agrega toggles o exportes solo si el módulo los necesita.
6. **Sigue el mismo stack**: Angular 12 + Angular Material (iconos/inputs) + Bootstrap (grid/cards), integrado a la SPA existente bajo una nueva ruta `#/admin/<modulo>/dashboard-<nombre>` y una entrada nueva en el sidebar.
7. **Antes de codificar**, define qué módulo/datos alimentarán el nuevo dashboard (aún pendiente en esta conversación) para diseñar el contrato del endpoint y las métricas de cada tarjeta.
