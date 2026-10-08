# Pepones · Una semana. Otra obsesión.

MVP visual en español. Aplicación en `web/`, material de entrega en [material/README.md](material/README.md).

Vista privada publicada: https://pepones-burger-experience.diegomvaldez19.chatgpt.site

Validación: compilación y tipos aprobados, 8 comprobaciones de dominio y 12 escenarios en Chrome (escritorio y móvil emulado), sin errores JavaScript. Incluye scroll reversible, recuperación ante pérdida de WebGL y movimiento reducido. Pendientes las pruebas en dispositivos físicos y la medición de Core Web Vitals en condiciones reales.

## Ejecutar

Requiere **Node.js 24 o posterior** para SQLite integrado.

```sh
cd web
npm ci
npm run dev
```

Abrir la dirección que imprime Next.js, normalmente `http://127.0.0.1:3000`.

En tu equipo Windows puedes ejecutar desde PowerShell:

```powershell
cd "C:\Users\USER\Documents\FREE LANCER\PEPONES\web"
node --version
npm.cmd ci
npm.cmd run dev
```

`npm.cmd` evita el bloqueo de `npm.ps1` cuando PowerShell restringe scripts. Instalar dependencias con `ci` es necesario al clonar el proyecto o cuando cambia el lockfile; para las siguientes sesiones basta `npm.cmd run dev`. Mantener esa terminal abierta; `Ctrl+C` detiene el servidor. Los cambios de interfaz se actualizan en el navegador durante el desarrollo.

```sh
npm run build       # genera out/, exportación estática
npm run start       # sirve out/
npm run typecheck
```

## Estudio 3D de Dona Burger

Abrir `http://127.0.0.1:3000/estudio/dona/` con el servidor local encendido. Incluye modelos GLB por ingrediente, rotación, zoom, separación de capas y renders de revisión. El flujo de Blender y los comandos para regenerar los recursos están en [tools/blender/README.md](tools/blender/README.md).

## Estudio 3D de Texas

Abrir `http://127.0.0.1:3000/estudio/texas/`, o usar «Texas en 3D» en la navegación y el bloque «Texas, capa por capa» de la portada. El estudio muestra la hamburguesa armada o por capas con un control gradual. Incluye:

- lista numerada de ingredientes sincronizada con el modelo, con etiquetas en cada capa;
- papas Cajun como acompañamiento opcional;
- controles de cámara con teclado y botones;

El modelo y sus estimaciones se documentan en [tools/blender/TEXAS.md](tools/blender/TEXAS.md) y [material/semanal/texas/ficha.txt](material/semanal/texas/ficha.txt). Para regenerarlo, desde `web/`: `npm run models:build:texas` y `npm run models:import:texas`.

## Arquitectura

Next.js App Router, React, TypeScript, CSS y fuentes locales. GSAP/ScrollTrigger controla el recorrido. Three.js, React Three Fiber y Drei componen la hamburguesa modular y admiten GLB por ingrediente. Rutas `/` y `/menu/`, búsqueda, filtros, detalle, navegación móvil y visor accesible mediante botones.

SQLite es local y se lee al compilar; la base no se publica. La primera ejecución la crea desde `web/data/content.json`. Las siguientes compilaciones respetan el contenido de la base.

## Actualizar la semanal

Editar `web/data/content.json` y ejecutar desde `web/`:

```sh
npm run content:sync
npm run build
```

`content:sync` reemplaza los bloques de SQLite por el JSON. Respaldar antes cualquier cambio hecho directamente en la base. `src/generated/content.json` es una instantánea pública generada; no editar a mano ni incluir datos privados.

Cambiar `weekly.burgerId`, registrar `startsAt`/`endsAt` en ISO con `-04:00`, poner `demo: false` y `status: "available"`. Para agotada usar `sold-out`. La disponibilidad se reevalúa al abrir y cada 30 segundos. No hay panel ni publicación programada en el MVP.

El WhatsApp debe ser el número real con país y solo dígitos. Si está vacío, un diálogo explica que falta confirmarlo y enlaza al Instagram recibido. Sin pin exacto, Maps realiza una búsqueda de la dirección. Precios ausentes: «Consultar».

La interfaz `src/lib/content.ts` separa los datos de los componentes para incorporar un panel más adelante. Cada ingrediente admite `modelUrl`; la receta admite posición vertical, escala y rotación.

## Interacción

El scroll separa/ensambla en escritorio. En móvil un botón controla las capas. El visor independiente permite selección con ratón, tacto y teclado; Escape cierra y devuelve el foco. Movimiento reducido o fallo 3D conservan imagen y descripciones. El render se pausa fuera de vista.

## Publicación y material

**ChatGPT Sites es el alojamiento de la demostración privada.** El proyecto es una aplicación Next.js que puedes desarrollar y compilar en tu equipo sin entrar a ChatGPT ni usar una clave de OpenAI. La exportación `web/out/` también se puede alojar en otro servidor de archivos estáticos.

El repositorio principal es `https://github.com/GatoCoder282/pepones`, rama `main`. La publicación de Sites usa una copia y un repositorio de despliegue separados. No hay un flujo automático configurado que publique en Sites al hacer push a GitHub. Los cambios locales y los commits nuevos se ven en la web alojada después de una nueva publicación.

Documentación oficial de Sites: https://learn.chatgpt.com/docs/sites

Exportación en `web/out/`, manifest de Sites en `web/.openai/hosting.json`. La demostración empieza privada y sin indexación. Para lanzamiento público: datos reales, recursos aprobados y actualización de `robots` en `src/app/layout.tsx`.

El repositorio de publicación está aislado en `web/.sites-runtime/publish`; el repositorio original no fue reemplazado. En Windows el empaquetador de Sites necesita Git Bash en PATH antes de WSL y `TAR_OPTIONS=--force-local`. Las credenciales temporales se solicitan al conector y no se guardan en archivos.

Big Peps no está confirmada como semanal vigente. Imagen protagonista ilustrativa y geometría 3D provisional; consultar [la guía de material](material/README.md) para sustituirlas. No incluye pedidos, pagos ni administración.
