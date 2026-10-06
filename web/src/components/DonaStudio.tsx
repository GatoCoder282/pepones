"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useCallback, useState } from "react";
import { ArrowLeft, Layers, RotateCcw } from "lucide-react";
import manifest from "@/generated/dona-burger.json";
import type { Ingredient, IngredientKind, RecipeLayer } from "@/lib/content";
import styles from "./DonaStudio.module.css";

const Scene = dynamic(() => import("./BurgerScene"), { ssr: false });
const notes: Record<
  string,
  { name: string; kind: IngredientKind; color: string; description: string }
> = {
  "dona-bottom": {
    name: "Base de dona",
    kind: "bun-bottom",
    color: "#ce8d38",
    description:
      "Dona cortada horizontalmente, con la miga expuesta y glaseado que cae por el borde.",
  },
  "smash-beef": {
    name: "Doble carne smash",
    kind: "patty",
    color: "#68402b",
    description:
      "Dos carnes con costra tostada, bordes irregulares y relieve en la superficie.",
  },
  "american-cheese": {
    name: "Doble queso americano",
    kind: "cheese",
    color: "#edb426",
    description:
      "Dos láminas de queso americano con las esquinas fundidas sobre la carne.",
  },
  bacon: {
    name: "Tocino",
    kind: "bacon",
    color: "#a55c38",
    description: "Tiras onduladas con bordes tostados y vetas de grasa.",
  },
  "dona-top": {
    name: "Tapa glaseada",
    kind: "bun-top",
    color: "#db9b49",
    description:
      "La corona de la dona conserva su agujero central y una película irregular de glaseado.",
  },
};
const ingredients: Ingredient[] = manifest.assets.map((asset) => ({
  id: asset.id,
  ...notes[asset.id],
  short: notes[asset.id].name,
  modelUrl: asset.modelUrl,
}));
const recipe: RecipeLayer[] = manifest.recipe.map((layer) => ({
  ...layer,
  rotation: layer.rotation as [number, number, number],
}));

export default function DonaStudio() {
  const [expanded, setExpanded] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  const [ready, setReady] = useState(false);
  const [revision, setRevision] = useState(0);
  const handleReady = useCallback(() => setReady(true), []);
  const handleFailure = useCallback(() => setFailed(true), []);
  const choose = useCallback((id: string) => {
    setSelected((current) => (current === id ? null : id));
    setExpanded(true);
  }, []);
  const current = selected ? notes[selected] : null;

  function reset() {
    setSelected(null);
    setExpanded(false);
    setFailed(false);
    setReady(false);
    setRevision((v) => v + 1);
  }

  return (
    <main id="contenido" className={styles.studio}>
      <header className={styles.header}>
        <Link href="/">
          <ArrowLeft size={17} /> Volver a Pepones
        </Link>
        <span>ESTUDIO DE INGREDIENTES / 01</span>
      </header>
      <section className={styles.workspace} aria-labelledby="dona-title">
        <div className={styles.copy}>
          <p className={styles.eyebrow}>PEPONES · PRIMERA VERSIÓN 3D</p>
          <h1 id="dona-title">
            DONA
            <br />
            <em>BURGER.</em>
          </h1>
          <p className={styles.intro}>
            Dona glaseada. Doble carne. Doble queso americano. Tocino. Cada
            capa, de cerca.
          </p>
          <div className={styles.controls}>
            <button
              className={styles.primary}
              disabled={failed}
              aria-pressed={expanded}
              onClick={() => {
                setExpanded((v) => !v);
                setSelected(null);
              }}
            >
              <Layers size={18} />{" "}
              {expanded ? "Juntar las capas" : "Separar las capas"}
            </button>
            <button
              className={styles.reset}
              aria-label="Restablecer vista"
              onClick={reset}
            >
              <RotateCcw size={19} />
            </button>
          </div>
          <p className={styles.hint}>
            Arrastra para girar. Usa la rueda o dos dedos para acercarte.
          </p>
          <div
            className={styles.ingredients}
            role="group"
            aria-label="Explorar ingredientes"
          >
            {ingredients.map((ingredient, i) => (
              <button
                key={ingredient.id}
                aria-pressed={selected === ingredient.id}
                disabled={failed}
                onClick={() => choose(ingredient.id)}
              >
                <span>0{i + 1}</span>
                {ingredient.name}
                <i
                  style={{ background: ingredient.color }}
                  aria-hidden="true"
                />
              </button>
            ))}
          </div>
          <div className={styles.detail} aria-live="polite">
            <h2>
              {current?.name ?? (
                <>
                  Siete capas. <em>Un antojo.</em>
                </>
              )}
            </h2>
            <p>
              {current?.description ??
                "Selecciona un ingrediente para verlo separado. La carne y el queso aparecen dos veces en la receta."}
            </p>
          </div>
        </div>
        <div className={styles.visual}>
          <span className={styles.caption}>DONA BURGER / PEPONES</span>
          {failed ? (
            <div className={styles.fallback} role="status">
              <img
                src="/images/dona-burger/three-quarter.webp"
                alt="Render de Dona Burger con dona glaseada, doble carne, queso y tocino"
              />
              <p>
                La vista 3D no pudo cargar. Puedes revisar los renders o
                restablecer la vista.
              </p>
            </div>
          ) : (
            <>
              {!ready && (
                <p className={styles.loading} role="status">
                  Preparando los ingredientes…
                </p>
              )}
              <Scene
                key={revision}
                recipe={recipe}
                ingredients={ingredients}
                interactive
                studio
                spread={expanded ? 1 : 0}
                selected={selected}
                onSelect={choose}
                onReady={handleReady}
                onFailure={handleFailure}
              />
            </>
          )}
          <span className={styles.visualNote}>
            DONA GLASEADA + DOBLE SMASH + QUESO + TOCINO
          </span>
        </div>
      </section>
      <section className={styles.renders} aria-labelledby="renders-title">
        <div>
          <p className={styles.eyebrow}>LA MISMA BURGER, DESDE OTRO ÁNGULO</p>
          <h2 id="renders-title">
            MIRA <em>CADA CAPA.</em>
          </h2>
        </div>
        <div className={styles.renderGrid}>
          {[
            ["front", "De frente"],
            ["three-quarter", "Tres cuartos"],
            ["exploded", "Por ingredientes"],
          ].map(([file, label]) => (
            <figure key={file}>
              <a
                href={`/images/dona-burger/${file}.webp`}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={`Abrir render: ${label}`}
              >
                <img
                  src={`/images/dona-burger/${file}.webp`}
                  alt={`Dona Burger: ${label.toLowerCase()}`}
                  loading="lazy"
                />
              </a>
              <figcaption>{label}</figcaption>
            </figure>
          ))}
        </div>
        <p className={styles.reviewNote}>
          Modelo de revisión creado a partir de las fotos compartidas. Las
          proporciones y superficies ocultas se interpretaron para esta primera
          versión.
        </p>
      </section>
    </main>
  );
}
