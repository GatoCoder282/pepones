# Material de Pepones

Deja aquí los originales, en subcarpetas por hamburguesa. El sitio usa copias optimizadas dentro de `web/public/`.

| Carpeta | Material |
| --- | --- |
| `marca/` | Logo SVG o PDF vectorial; PNG transparente si no existe vector. Manual PDF. Fuentes WOFF2 con licencia web. |
| `semanal/nombre/fotos/` | JPG/PNG originales, idealmente ≥2500 px, sin textos: frontal, tres cuartos, laterales y superior. |
| `semanal/nombre/ingredientes/` | Fotos individuales, cantidades, medidas aproximadas y orden de abajo hacia arriba. |
| `semanal/nombre/modelos/` | GLB por ingrediente + escena ensamblada de referencia + editable Blender. |
| `menu/` | Carta vigente PDF/documento, categorías, productos, ingredientes y precios en Bs. |
| `local/` | Fotos originales, historia confirmada, horarios, WhatsApp con país y enlace al pin de Maps. |
| `referencias/` | Reels MP4 o grabaciones de pantalla de interacciones. |

## Primera semanal

Copia `semanal/plantilla/ficha.txt` y completa los datos. Usa fechas con hora de Bolivia, por ejemplo `2026-10-05T12:00:00-04:00`. Las capturas no confirman vigencia.

## Encargo para el artista 3D

- Cada ingrediente debe ser un objeto separado y nombrado; no fusionar la hamburguesa.
- Entregar `.blend` con texturas incluidas y `.glb` con materiales PBR compatibles con glTF.
- Hornear materiales procedurales a texturas. Incluir caras que se revelarán al separar capas.
- Un GLB por ingrediente reutilizable y una escena completa de referencia. Piezas centradas en X/Z, eje Y vertical y transformaciones aplicadas.
- El prototipo usa panes de radio aproximado 1 y una hamburguesa de altura aproximada 2.2. Usar escala consistente entre piezas.
- Nombres estables asociados con `ingredients[].id`; carne y queso se reutilizan en capas repetidas.
- Objetivo inicial: hasta 100 000 triángulos por hamburguesa, texturas hasta 2K y alrededor de 5 MB en móvil; validar el acabado antes de reducir detalles.
- Entregar también foto/render de respaldo y registrar procedencia y licencia.

## Conectar un GLB

1. Copiar la versión web a `web/public/models/ingrediente.glb`.
2. Añadir `"modelUrl": "/models/ingrediente.glb"` al ingrediente en `web/data/content.json`.
3. Ajustar `recipe[].y`, `scale: [x,y,z]` y `rotation: [x,y,z]` en radianes.
4. Ejecutar `npm run content:sync` y `npm run build` desde `web/`.

La selección y la animación siguen usando los mismos identificadores. No hace falta rehacer la interacción.

## Provisional en esta entrega

Big Peps es una edición de demostración. La imagen protagonista es generada e ilustrativa; las piezas 3D son geometría procedural. El archivo usa las dos capturas entregadas. El logotipo es tipográfico provisional y las fuentes locales son Bebas Neue y DM Sans. Faltan precios, horarios, WhatsApp, pin exacto, fechas y modelos profesionales.
