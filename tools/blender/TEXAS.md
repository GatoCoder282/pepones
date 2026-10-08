# Texas: Blender → web

Modelo procedural interpretado a partir de la foto frontal `photos/texas_burguer_pepones.jpeg` y de la lista de ingredientes confirmada. No es un escaneo. El orden de las capas sigue la foto. Las medidas, las caras ocultas y la cantidad de tiras, rodajas y hebras son estimaciones visuales (detalle en `material/semanal/texas/ficha.txt`).

Este flujo es independiente del de Dona Burger: tiene su propio script, carpeta de salida, modelos web, imágenes y manifiesto.

## Regenerar

Desde `web/`, con Blender 5.2 instalado:

```sh
npm run models:build:texas    # Blender: geometría, horneado, GLB, renders y .blend
npm run models:import:texas   # valida los GLB y los copia a la web
```

