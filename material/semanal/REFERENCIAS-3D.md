# Referencias para modelado 3D de Pepones

## Estado

Se revisaron las referencias de hamburguesas y las nuevas fotos individuales de Dona Burger en `photos/`. Son suficientes para iniciar modelos interpretados a partir de fotografías; las superficies ocultas y las medidas reales requieren decisiones artísticas. Dona Burger es el primer piloto generado con Blender, con escena editable, GLB por ingrediente y renders.

Las imágenes no confirman cuál es la semanal vigente, fechas ni precios.

## Ingredientes confirmados por los textos de las imágenes

| Hamburguesa | Archivo | Receta escrita |
| --- | --- | --- |
| Bourbon Bacon | `photos/bourbon bacon.png` | Pan de papa hecho en casa, doble carne, doble queso americano, tocino, salteado de pimentón y champiñones, salsa bourbon, pepinillos, tomate y lechuga. |
| Dona Burger | `photos/dona burger.png` | Dona glaseada, doble carne, doble queso americano y tocino. |
| Pancake | `photos/pancake.png` | Panqueques hechos en casa, doble carne, doble queso americano, tocino, huevos revueltos y una porción de miel de maple. |
| Swiss Bacon | `photos/swiss bacon.png` | Pan de papa hecho en casa, doble carne, doble queso mozzarella, tocino, cebolla caramelizada, champiñones al ajillo y alioli. |
| Picanha | `photos/picanha.png` | La imagen no contiene una lista de ingredientes. El nombre y los componentes visibles no bastan para confirmar la receta o identificar la salsa verde. |

## Piloto seleccionado: Dona Burger

Es una referencia clara con pocos tipos de ingredientes. Carne, queso y tocino podrán reutilizarse como base artística en otras recetas, ajustando sus variantes cuando corresponda.

Orden visible propuesto, de abajo hacia arriba:

1. Base de dona glaseada.
2. Carne inferior.
3. Queso americano inferior.
4. Carne superior.
5. Queso americano superior.
6. Tocino en tiras onduladas.
7. Tapa de dona glaseada.

Las nuevas fotos `dona ingrediente.png` y `dona ingredientes dona.png` muestran una dona con agujero central cortada horizontalmente: una base con miga expuesta y una tapa glaseada. Las fotos `dona ingredientes carne.png` y `dona ingredientes carne con tocino.png` muestran el tostado, el queso y las tiras de tocino. El modelo usa proporciones relativas hasta disponer de medidas.

Acabados a reproducir: glaseado blanco irregular, masa dorada, bordes de carne tostados y desiguales, queso fundido que cae sobre la carne y tocino con variación de color y grosor. Revisar estos detalles en renders de frente, tres cuartos y desde arriba.

## Información que permite mejorar la fidelidad

- Una foto superior y otra de tres cuartos o lateral, preferiblemente originales sin texto. Ayudan a definir volumen, profundidad y zonas ocultas.
- Diámetro aproximado de la dona/pan y altura de la hamburguesa. Son opcionales para la primera versión.
- Para mayor fidelidad de Dona Burger: foto lateral de la hamburguesa ensamblada y medidas aproximadas. Son mejoras opcionales; las referencias actuales bastan para la primera versión.
- Para Pancake: confirmar si la miel de maple se entrega aparte o se vierte encima. El texto menciona una porción; no asumir una capa interna.
- Para Picanha: receta escrita completa, incluyendo pan, carne, queso y salsa verde.

Las fotos individuales de ingredientes ayudan al acabado, pero no bloquean la primera versión.

## Requisito para ejecutar el flujo

Blender 5.2.2 LTS está instalado en `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`. Se generó la escena mediante Python y se renderizó con Cycles y GPU.

El generador y sus comandos están documentados en `tools/blender/README.md`.

## Entrega del piloto

Guardar en `material/semanal/dona-burger/modelos/`:

- `dona-burger.blend`: escena editable ensamblada y recursos incluidos.
- Un GLB por ingrediente reutilizable, con base y tapa de dona independientes.
- Renders PNG de revisión y una imagen de respaldo para la web.

La escena de trabajo puede usar el eje Z vertical habitual de Blender. La exportación debe convertir al eje Y vertical de glTF y mantener escala y orígenes coherentes. Cada ingrediente exportado debe quedar centrado para que la web controle su posición por capa.

Los materiales procedurales que no se traduzcan a glTF deben hornearse a texturas. El render de Blender y el modelo visto en la web requieren revisión visual porque sus motores de iluminación difieren.

La vista `/estudio/dona/` reutiliza el visor de la web con GLB, rotación, zoom, selección y separación de capas. La receta del piloto y sus asociaciones `modelUrl` se generan con el importador. La semanal de demostración conserva su configuración hasta definir la publicación de la receta real.
