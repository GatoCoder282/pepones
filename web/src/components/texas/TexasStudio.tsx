"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";
import {
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  Info,
  Layers,
  Minus,
  Plus,
  RefreshCcw,
  RotateCcw,
  RotateCw,
  Square,
} from "lucide-react";
import {
  TEXAS_INGREDIENTS,
  TEXAS_MODEL,
  TEXAS_SIDE,
  ingredientById,
  ingredientNumber,
  layerText,
  type TexasIngredientId,
} from "@/lib/texas";
import type { ViewCommand } from "./TexasScene";
import styles from "./TexasStudio.module.css";

const Scene = dynamic(() => import("./TexasScene"), { ssr: false });

type Status = "checking" | "loading" | "ready" | "failed" | "unsupported";
const pad = (n: number) => String(n).padStart(2, "0");
const IDS = TEXAS_INGREDIENTS.map((i) => i.id);

function webglAvailable() {
  try {
    const canvas = document.createElement("canvas");
    return !!(canvas.getContext("webgl2") ?? canvas.getContext("webgl"));
  } catch {
    return false;
  }
}

export default function TexasStudio() {
  const [spread, setSpread] = useState(0);
  const [selected, setSelected] = useState<TexasIngredientId | null>(null);
  const [showSide, setShowSide] = useState(false);
  const [status, setStatus] = useState<Status>("checking");
  const [resetKey, setResetKey] = useState(0);
  const [command, setCommand] = useState<ViewCommand | null>(null);
  const [reducedMotion, setReducedMotion] = useState(false);
  const [compact, setCompact] = useState(false);
  const [revision, setRevision] = useState(0);
  const [progress, setProgress] = useState(0);
  const items = useRef<(HTMLButtonElement | null)[]>([]);
  const stage = useRef<HTMLElement>(null);
  const layered = spread >= 0.5;
  const current = selected ? ingredientById(selected) : null;

  useEffect(() => {
    setStatus(webglAvailable() ? "loading" : "unsupported");
    const motion = matchMedia("(prefers-reduced-motion: reduce)");
    const narrow = matchMedia("(max-width: 899px)");
    const sync = () => {
      setReducedMotion(motion.matches);
      setCompact(narrow.matches);
    };
    sync();
    motion.addEventListener("change", sync);
    narrow.addEventListener("change", sync);
    // Deep links: ?ingrediente=pepinillos&vista=capas
    const params = new URLSearchParams(location.search);
    const id = params.get("ingrediente") as TexasIngredientId | null;
    if (id && IDS.includes(id)) {
      setSelected(id);
      setSpread(1);
    } else if (params.get("vista") === "capas") setSpread(1);
    return () => {
      motion.removeEventListener("change", sync);
      narrow.removeEventListener("change", sync);
    };
  }, []);

  useEffect(() => {
    if (status === "checking") return;
    const params = new URLSearchParams();
    if (selected) params.set("ingrediente", selected);
    else if (layered) params.set("vista", "capas");
    const query = params.toString();
    history.replaceState(null, "", query ? `?${query}` : location.pathname);
  }, [selected, layered, status]);

  const handleReady = useCallback(() => setStatus("ready"), []);
  const handleFailure = useCallback(() => setStatus("failed"), []);

  const choose = useCallback((id: TexasIngredientId) => {
    setSelected((value) => (value === id ? null : id));
    // A layer is easier to read with the stack apart; keep any separation already chosen.
    setSpread((value) => (value < 0.35 ? 1 : value));
  }, []);
  const chooseFromList = (id: TexasIngredientId) => {
    choose(id);
    // On phones the list sits below the model: bring the highlighted layer into view.
    if (compact)
      stage.current?.scrollIntoView({ behavior: reducedMotion ? "auto" : "smooth", block: "start" });
  };
  const step = (direction: number) => {
    const index = selected ? IDS.indexOf(selected) : -1;
    const next = IDS[(index + direction + IDS.length) % IDS.length];
    setSelected(next);
    setSpread((value) => (value < 0.35 ? 1 : value));
  };
  const assemble = () => {
    setSelected(null);
    setSpread(0);
  };
  const reset = () => {
    assemble();
    setShowSide(false);
    setResetKey((k) => k + 1);
    if (status === "failed") {
      setStatus(webglAvailable() ? "loading" : "unsupported");
      setRevision((v) => v + 1);
    }
  };
  const send = (kind: ViewCommand["kind"], amount: number) =>
    setCommand((previous) => ({ kind, amount, id: (previous?.id ?? 0) + 1 }));

  const onViewportKey = (event: KeyboardEvent<HTMLDivElement>) => {
    const actions: Record<string, () => void> = {
      ArrowLeft: () => send("rotate", -0.45),
      ArrowRight: () => send("rotate", 0.45),
      "+": () => send("zoom", 0.82),
      "=": () => send("zoom", 0.82),
      "-": () => send("zoom", 1.22),
      Home: reset,
      Escape: () => setSelected(null),
    };
    const action = actions[event.key];
    if (action) {
      event.preventDefault();
      action();
    }
  };
  const onListKey = (event: KeyboardEvent<HTMLOListElement>) => {
    const index = items.current.findIndex((el) => el === document.activeElement);
    if (index < 0) return;
    const keys: Record<string, number> = {
      ArrowDown: index + 1,
      ArrowUp: index - 1,
      Home: 0,
      End: IDS.length - 1,
    };
    if (!(event.key in keys)) return;
    event.preventDefault();
    items.current[(keys[event.key] + IDS.length) % IDS.length]?.focus();
  };

  const live = status === "loading" || status === "ready";
  const percent = Math.round(spread * 100);

  return (
    <main id="contenido" className={styles.studio}>
      <header className={styles.header}>
        <Link href="/" className={styles.back}>
          <ArrowLeft size={18} aria-hidden="true" /> Volver a Pepones
        </Link>
        <span className={styles.headerLabel}>ESTUDIO 3D · TEXAS</span>
      </header>

      <div className={styles.workspace}>
        <section className={styles.panel} aria-labelledby="texas-title">
          <div className={styles.intro}>
            <p className={styles.eyebrow}>PEPONES · ESTUDIO 3D</p>
            <h1 id="texas-title">TEXAS</h1>
            <p className={styles.summary}>
              Pan de papa, doble carne, doble queso americano, tocino, cebolla
              crispy, pepinillos, salsa barbacoa y salsa original.
            </p>
            <p className={styles.sideNote}>Acompañamiento: papas Cajun.</p>
          </div>

          <div className={styles.listBlock}>
            <h2 id="ingredientes-title" className={styles.listTitle}>
              Ingredientes <span>{TEXAS_INGREDIENTS.length}</span>
            </h2>
            <ol
              className={styles.list}
              aria-labelledby="ingredientes-title"
              onKeyDown={onListKey}
            >
              {TEXAS_INGREDIENTS.map((ingredient, i) => (
                <li key={ingredient.id}>
                  <button
                    ref={(el) => {
                      items.current[i] = el;
                    }}
                    type="button"
                    aria-pressed={selected === ingredient.id}
                    aria-controls="texas-detalle"
                    onClick={() => chooseFromList(ingredient.id)}
                  >
                    <span className={styles.number}>{pad(i + 1)}</span>
                    <span className={styles.name}>
                      {ingredient.name}
                      <small>{layerText(ingredient.id)}</small>
                    </span>
                    {ingredient.quantity && (
                      <span className={styles.quantity}>{ingredient.quantity}</span>
                    )}
                    <i style={{ background: ingredient.color }} aria-hidden="true" />
                  </button>
                </li>
              ))}
            </ol>
          </div>

          <div className={styles.sideCard}>
            <div>
              <p className={styles.eyebrow}>ACOMPAÑAMIENTO</p>
              <h2>{TEXAS_SIDE.name}</h2>
              <p>
                {TEXAS_SIDE.description} {TEXAS_SIDE.estimate}
              </p>
            </div>
            <button
              type="button"
              className={styles.secondary}
              aria-pressed={showSide}
              disabled={!live}
              onClick={() => setShowSide((v) => !v)}
            >
              {showSide ? "Ocultar de la escena" : "Mostrar en la escena"}
            </button>
          </div>
        </section>

        <section ref={stage} className={styles.stage} aria-label="Visor 3D de Texas">
          <div
            className={styles.viewport}
            tabIndex={0}
            role="group"
            aria-roledescription="visor 3D"
            aria-label="Modelo 3D de Texas"
            aria-describedby="texas-ayuda"
            aria-busy={status === "loading" || status === "checking"}
            onKeyDown={onViewportKey}
          >
            {live ? (
              <Scene
                key={revision}
                spread={spread}
                selected={selected}
                showSide={showSide}
                resetKey={resetKey}
                command={command}
                reducedMotion={reducedMotion}
                compact={compact}
                onSelect={choose}
                onReady={handleReady}
                onFailure={handleFailure}
                onProgress={setProgress}
              />
            ) : status !== "checking" ? (
              <div className={styles.fallback} role="status">
                <img
                  src={layered ? TEXAS_MODEL.renders.exploded.src : TEXAS_MODEL.photo.src}
                  width={layered ? TEXAS_MODEL.renders.exploded.width : TEXAS_MODEL.photo.width}
                  height={layered ? TEXAS_MODEL.renders.exploded.height : TEXAS_MODEL.photo.height}
                  alt={
                    layered
                      ? "Render de las capas de Texas, de la base a la tapa"
                      : "Foto de Texas"
                  }
                />
                <p>
                  {status === "unsupported"
                    ? "Este navegador no puede mostrar la vista 3D. Puedes revisar la foto, el render por capas y cada ingrediente."
                    : "La vista 3D se interrumpió. Puedes revisar la foto y los ingredientes, o intentarlo de nuevo."}
                </p>
                {status === "failed" && (
                  <button type="button" className={styles.secondary} onClick={reset}>
                    Reintentar la vista 3D
                  </button>
                )}
              </div>
            ) : null}
            {(status === "loading" || status === "checking") && (
              <div className={styles.loading} role="status">
                <span className={styles.spinner} aria-hidden="true" />
                <span>Preparando el modelo 3D… {Math.round(progress)} %</span>
                <span className={styles.progress} aria-hidden="true">
                  <span style={{ transform: `scaleX(${progress / 100})` }} />
                </span>
              </div>
            )}
          </div>

          <div className={styles.viewBar}>
            <div className={styles.segmented} role="group" aria-label="Vista de la hamburguesa">
              <button type="button" aria-pressed={spread === 0} onClick={assemble}>
                <Square size={15} aria-hidden="true" /> Armada
              </button>
              <button
                type="button"
                aria-pressed={spread === 1}
                onClick={() => setSpread(1)}
              >
                <Layers size={15} aria-hidden="true" /> Por capas
              </button>
            </div>
            <label className={styles.slider}>
              <span>Separación</span>
              <input
                type="range"
                min={0}
                max={100}
                step={1}
                value={percent}
                aria-valuetext={`${percent} % de separación`}
                onChange={(e) => setSpread(Number(e.target.value) / 100)}
              />
            </label>
          </div>

          <div className={styles.toolbar} role="toolbar" aria-label="Cámara">
            <button type="button" onClick={reset} className={styles.resetButton} disabled={status === "checking"}>
              <RefreshCcw size={16} aria-hidden="true" />
              <span className={styles.resetLabel}>Restablecer vista</span>
            </button>
            <div className={styles.iconRow}>
              <button type="button" aria-label="Girar a la izquierda" title="Girar a la izquierda" disabled={!live} onClick={() => send("rotate", -0.45)}>
                <RotateCcw size={17} aria-hidden="true" />
              </button>
              <button type="button" aria-label="Girar a la derecha" title="Girar a la derecha" disabled={!live} onClick={() => send("rotate", 0.45)}>
                <RotateCw size={17} aria-hidden="true" />
              </button>
              <button type="button" aria-label="Acercar" title="Acercar" disabled={!live} onClick={() => send("zoom", 0.82)}>
                <Plus size={17} aria-hidden="true" />
              </button>
              <button type="button" aria-label="Alejar" title="Alejar" disabled={!live} onClick={() => send("zoom", 1.22)}>
                <Minus size={17} aria-hidden="true" />
              </button>
            </div>
          </div>

          <p id="texas-ayuda" className={styles.hint}>
            Arrastra para girar y usa la rueda o dos dedos para acercarte. Con
            el teclado: flechas para girar, + y − para el zoom.
          </p>

          <div id="texas-detalle" className={styles.detail} aria-live="polite">
            {current ? (
              <>
                <p className={styles.detailMeta}>
                  {pad(ingredientNumber(current.id))} · {layerText(current.id)} de {TEXAS_MODEL.layers}
                </p>
                <h2>{current.name}</h2>
                {current.quantity && <p className={styles.detailQuantity}>{current.quantity}</p>}
                <p>{current.description}</p>
                {current.estimate && (
                  <p className={styles.estimate}>
                    <Info size={14} aria-hidden="true" /> {current.estimate}
                  </p>
                )}
                <div className={styles.detailActions}>
                  <button type="button" aria-label="Ingrediente anterior" title="Ingrediente anterior" onClick={() => step(-1)}>
                    <ChevronLeft size={18} aria-hidden="true" />
                  </button>
                  <button type="button" aria-label="Ingrediente siguiente" title="Ingrediente siguiente" onClick={() => step(1)}>
                    <ChevronRight size={18} aria-hidden="true" />
                  </button>
                  <button type="button" className={styles.whole} onClick={assemble}>
                    Ver la hamburguesa completa
                  </button>
                </div>
              </>
            ) : (
              <>
                <p className={styles.detailMeta}>
                  {TEXAS_MODEL.layers} capas · {TEXAS_INGREDIENTS.length} ingredientes
                </p>
                <h2>Elige un ingrediente</h2>
                <p>
                  Toca un ingrediente de la lista o una capa del modelo para
                  verla separada y resaltada.
                </p>
              </>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}
