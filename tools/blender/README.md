# Dona Burger: Blender → web

Modelo procedural interpretado a partir de las cinco referencias de Dona Burger en `photos/`. No es un escaneo de la hamburguesa. Las fotos nuevas permiten definir la dona partida horizontalmente, la costra de la carne, el queso y las tiras de tocino. Las superficies ocultas y las medidas son interpretadas.

## Generar la escena

Ejecutar desde la raíz del repositorio en PowerShell. Se usó Blender 5.2.2 LTS instalado en este equipo. No requiere plugins, servicios externos ni Python adicional.

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --factory-startup --python-exit-code 1 --python tools/blender/generate_dona.py -- --mode build
```

El script crea cinco ingredientes reutilizables y siete capas, hornea color, rugosidad y normales, exporta GLB y genera tres renders. Usa Cycles con GPU cuando está disponible y conserva una alternativa CPU. Los materiales fuente se guardan en una colección oculta de originales procedurales.

Para iterar formas y acabados sin hornear ni exportar:

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --factory-startup --python-exit-code 1 --python tools/blender/generate_dona.py -- --mode preview --resolution 1100 --samples 48
```

Parámetros opcionales: `--texture-size 2048`, `--web-texture-size 1024`, `--resolution 1600`, `--samples 96`, `--output <carpeta>`. La semilla de geometría está fijada en el script para repetir las formas.

## Archivos generados

En `material/semanal/dona-burger/modelos/`:

- `dona-burger.blend`: escena editable con imágenes empaquetadas, iluminación y cámara.
- `glb/`: cinco ingredientes individuales con texturas de 1024 px y una hamburguesa ensamblada con texturas de 2048 px.
- `textures/`: mapas de trabajo de 2048 px; `textures/web/`: versiones para la web.
- `renders/front.png`, `three-quarter.png`, `exploded.png`: revisiones transparentes de 1600 px.
- `manifest.json`: receta, tamaños, conteo de triángulos y referencias usadas.

Las exportaciones individuales están centradas en el origen y usan Y vertical de glTF. La receta define altura y rotación; carne y queso reutilizan sus GLB en dos capas. El archivo ensamblado es para intercambio y no se descarga en la web.

## Importar y abrir la web

Desde `web/`:

```powershell
npm.cmd run models:import:dona
npm.cmd run dev
```

Abrir **http://127.0.0.1:3000/estudio/dona/**. El importador comprueba la estructura de los GLB y sus mapas integrados, copia los modelos y convierte los renders a WebP. Los recursos web se versionan; la escena de trabajo y sus exportaciones intermedias permanecen locales y pueden regenerarse.

El estudio permite girar, acercar, separar y seleccionar ingredientes, con renders de respaldo ante un fallo de carga 3D. La receta de la semanal principal se gestiona por separado. Para publicar el resultado: `npm.cmd run build` genera también esta ruta estática.

## Dirección artística

Abrir `dona-burger.blend` en Blender y guardar una copia antes de editar a mano: volver a ejecutar el generador reemplaza sus archivos de salida. Para un cambio reproducible, editar las funciones `donut`, `patty`, `cheese`, `bacon`, las paletas de materiales o la lista `recipe` del script y regenerar.

Revisar el glaseado, grosor de las carnes, caída del queso y distribución del tocino. El render de Cycles y Three.js tienen iluminaciones distintas. Esta entrega prioriza la revisión artística; el manifiesto registra su peso real. Antes de usarla como protagonista de la portada en móviles, conviene reducir geometría y comprimir texturas según el presupuesto de descarga aprobado.
