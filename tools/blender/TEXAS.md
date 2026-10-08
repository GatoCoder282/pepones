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

