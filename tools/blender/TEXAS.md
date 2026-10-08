# Texas: Blender → web

Modelo procedural interpretado a partir de la foto frontal `photos/texas_burguer_pepones.jpeg` y de la lista de ingredientes confirmada. No es un escaneo. El orden de las capas sigue la foto. Las medidas, las caras ocultas y la cantidad de tiras, rodajas y hebras son estimaciones visuales (detalle en `material/semanal/texas/ficha.txt`).

Este flujo es independiente del de Dona Burger: tiene su propio script, carpeta de salida, modelos web, imágenes y manifiesto.

## Regenerar

Desde `web/`, con Blender 5.2 instalado:

```sh
npm run models:build:texas    # Blender: geometría, horneado, GLB, renders y .blend
npm run models:import:texas   # valida los GLB y los copia a la web
```

`models:build:texas` busca Blender en la ruta habitual de macOS (`/Applications/Blender.app`) o Windows (`C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`). Para otra ubicación, define `BLENDER` con la ruta del ejecutable. Los argumentos extra pasan al script: `npm run models:build:texas -- --samples 32`.

Ejecución directa desde la raíz del repositorio:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
  --python-exit-code 1 --python tools/blender/generate_texas.py -- --mode build
```

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --factory-startup `
  --python-exit-code 1 --python tools/blender/generate_texas.py -- --mode build
```

Para iterar formas y materiales sin hornear ni exportar (unos dos minutos):

```sh
… generate_texas.py -- --mode preview --resolution 900 --samples 32 --views front,three-quarter,exploded
```

Parámetros: `--texture-size 2048` (horneado), `--resolution 1600` y `--samples 96` (renders), `--views front,three-quarter,exploded,top` y `--output <carpeta>`. `--only carne,queso-americano` hornea y exporta solo esas piezas y conserva sus entradas anteriores en el manifiesto. Sirve para iterar; antes de importar, ejecuta una compilación completa para que los renders y la escena ensamblada coincidan. Las formas usan semillas fijas: dos ejecuciones dan el mismo resultado.

## Qué hace el script

- Construye 11 objetos con nombre propio: `pan-base`, `salsa-original-base`, `pepinillos`, `carne`, `queso-americano`, `tocino`, `salsa-barbacoa`, `cebolla-crispy`, `salsa-original-tapa`, `pan-tapa` y `papas-cajun` (acompañamiento, fuera de las capas).
- Las dos carnes y los dos quesos son capas independientes que reutilizan un GLB. Cada queso comparte el giro de su carne porque se drapea sobre ella.
- La carne se modela en alta resolución (remallado por vóxeles) y se hornea sobre una malla reducida. El resto se hornea sobre sí mismo.
- Hornea color, rugosidad, normales y oclusión ambiental con Cycles: usa GPU (Metal, OptiX, CUDA, HIP u oneAPI) si existe y, si no, la CPU.
- Exporta un GLB por pieza con texturas WebP, oclusión, rugosidad y metal en una sola imagen (ORM), compresión `EXT_meshopt_compression` y `KHR_materials_clearcoat`. Three.js los decodifica sin descargas externas.
- Genera tres renders de revisión, una escena ensamblada de intercambio y el archivo editable `texas.blend`.

## Archivos generados

En `material/semanal/texas/modelos/` (ignorado por Git; se regenera con el comando anterior):

- `texas.blend`: escena ensamblada con imágenes empaquetadas, luces y cámara. Los materiales procedurales originales quedan en la colección oculta «Procedural originals».
- `glb/`: un GLB por pieza y `texas-assembled.glb` con las 12 capas en su sitio.
- `textures/`: mapas de 2048 px; `textures/web/`: los tamaños de la web.
- `renders/front.png`, `three-quarter.png`, `exploded.png` y, en modo vista previa, `preview-*.png`.
- `manifest.json`: receta con altura y giro de cada capa, triángulos, peso y referencias.

`models:import:texas` comprueba cada GLB (cabecera, una malla, texturas WebP incrustadas, color, ORM, normales y oclusión, meshopt), lo copia a `web/public/models/texas/`, convierte los renders y la foto de referencia a WebP en `web/public/images/texas/` y escribe `web/src/generated/texas.json`.

## Capas

De abajo hacia arriba: pan de papa (base), salsa original, pepinillos, carne, queso americano, carne, queso americano, tocino, salsa barbacoa, cebolla crispy, salsa original y pan de papa (tapa). La foto muestra todas las capas salvo la identidad de las salsas: la salsa color melocotón (base y tapa) se asignó a la salsa original y el brillo rojizo sobre el tocino a la barbacoa.

## Presupuesto web

Resultado de la última importación: 12 capas con 99 812 triángulos y 2,55 MiB para la hamburguesa; 2,66 MiB con las papas (Dona Burger: 13,3 MiB). Texturas de 1024 px en pan y carne, 768 px en tocino y cebolla, y 512 px en las demás piezas. El importador imprime estas cifras en cada ejecución.

## Dirección artística

Para cambios reproducibles, edita en `generate_texas.py`:

- Formas: `bun_bottom`, `bun_top`, `sauce_base`, `pickles`, `patty_high`, `cheese`, `bacon`, `bbq`, `onions`, `sauce_top`, `fries`.
- Materiales: funciones `mat_*` (colores en hexadecimal y ruido procedural).
- Acabado web y tamaño de textura por pieza: diccionario `ASSETS`.

