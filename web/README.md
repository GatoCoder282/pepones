# Pepones web

Node 24+. `npm ci`, `npm run dev` para desarrollo. `npm run build` genera `out/` estático y `npm start` lo sirve.

## Contenido

Editar `data/content.json`, luego `npm run content:sync` y compilar. La sincronización reemplaza los bloques de SQLite. Los builds normales leen la base sin reiniciarla. La base local no se publica.

`burger.image` admite una ruta `/images/foto.webp`; `hero` es la imagen provisional. Los identificadores `campaign-N` y `archive-N` muestran las campañas de las capturas. Para una semanal real, entregar una foto individual y receta con ingredientes existentes. `ingredient.modelUrl` admite un GLB local. `recipe` define la posición vertical, escala y rotación de cada capa.

La semanal real requiere `demo: false`, `status: "available"` y fechas ISO con zona horaria. Hasta entonces el contenido es de demostración. Contacto y precios ausentes se muestran explícitamente como pendientes.

## Verificación

`npm run check:domain`: vigencia, agotado, borrador y URL de WhatsApp.

`npm run check:browser`: requiere la exportación servida en `http://127.0.0.1:3000` y Chrome; usa el Chrome instalado en Windows. Capturas y resultados se guardan en `reports/` (ignorado). Incluye escritorio, viewport móvil, menú, selección de ingredientes y movimiento reducido. La emulación móvil no sustituye pruebas en dispositivos iOS/Android físicos.

## Recursos

Imagen protagonista generada e ilustrativa; modelos de ingredientes procedurales provisionales. Campañas originales de las capturas del usuario. Fuentes autohospedadas Bebas Neue y DM Sans. Sustituir por logo, fotografías y modelos profesionales aprobados antes del lanzamiento público.

Demostración privada de Sites, con indexación deshabilitada en `src/app/layout.tsx`. No incluye pedidos, pagos ni panel.
