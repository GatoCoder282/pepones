"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";
import {
  ArrowDown,
  ArrowUpRight,
  Box,
  Minus,
  Plus,
  RotateCcw,
} from "lucide-react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import type { Burger, Ingredient } from "@/lib/content";
import { Dialog, ProductImage } from "./Shared";

const Scene = dynamic(() => import("./BurgerScene"), {
  ssr: false,
  loading: () => (
    <div className="scene-loading">
      <img src="/images/burger-hero.webp" alt="Hamburguesa completa" />
      <span>Preparando cada capa…</span>
    </div>
  ),
});
gsap.registerPlugin(ScrollTrigger);

export function IngredientExperience({
  burger,
  ingredients,
}: {
  burger: Burger;
  ingredients: Ingredient[];
}) {
  const section = useRef<HTMLElement>(null);
  const stage = useRef<HTMLDivElement>(null);
  const progress = useRef({ value: 0 });
  const [visible, setVisible] = useState(false);
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [reduced, setReduced] = useState(false);
  const [fallback, setFallback] = useState(false);
  const [mobileSpread, setMobileSpread] = useState(false);
  const [chapter, setChapter] = useState(0);
  const [focusIndex, setFocusIndex] = useState(0);
  const hasRecipe = burger.recipe.length > 0;
  const recipeIngredients = burger.ingredients.map((id) =>
    ingredients.find((i) => i.id === id)!,
  );
  const current = recipeIngredients.find((i) => i.id === selected);
  const scrollIngredient = recipeIngredients[focusIndex];
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: "300px" },
    );
    if (section.current) observer.observe(section.current);
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const change = () => setReduced(media.matches);
    change();
    media.addEventListener("change", change);
    return () => {
      observer.disconnect();
      media.removeEventListener("change", change);
    };
  }, []);
  useEffect(() => {
    if (!hasRecipe || fallback) return;
    const mm = gsap.matchMedia();
    mm.add(
      "(min-width: 900px) and (prefers-reduced-motion: no-preference)",
      () => {
        progress.current.value = 0;
        const timeline = gsap.timeline({
          scrollTrigger: {
            trigger: section.current,
            pin: stage.current,
            start: "top top",
            end: "+=2000",
            scrub: 0.7,
            invalidateOnRefresh: true,
            onUpdate: (self) => {
              const p = self.progress;
              setChapter(p < 0.25 ? 0 : p > 0.75 ? 2 : 1);
              setFocusIndex(
                Math.min(
                  recipeIngredients.length - 1,
                  Math.max(
                    0,
                    Math.floor(((p - 0.25) / 0.5) * recipeIngredients.length),
                  ),
                ),
              );
            },
          },
        });
        timeline
          .to(progress.current, {
            value: 1,
            duration: 0.25,
            ease: "power1.inOut",
          })
          .to(progress.current, { value: 1, duration: 0.5 })
          .to(progress.current, {
            value: 0,
            duration: 0.25,
            ease: "power1.inOut",
          });
        return () => {
          progress.current.value = 0;
        };
      },
    );
    return () => mm.revert();
  }, [burger.id, recipeIngredients.length, hasRecipe, fallback]);
  useEffect(() => {
    if (window.matchMedia("(max-width: 899px)").matches)
      progress.current.value = mobileSpread ? 1 : 0;
  }, [mobileSpread]);
  return (
    <section
      id="ingredientes"
      ref={section}
      className="ingredients-section"
      aria-labelledby="ingredients-title"
    >
      <div ref={stage} className="ingredient-stage">
        <div className="ingredient-heading">
          <p className="eyebrow">EL ANTOJO, CAPA POR CAPA</p>
          <h2 id="ingredients-title">
            Nada sobra.
            <br />
            <em>Todo provoca.</em>
          </h2>
          <p>
            Hay mucho entre estos dos panes.
            <br />
            Vamos a conocernos por dentro.
          </p>
          <button className="outline-button" onClick={() => setOpen(true)}>
            Explorar ingredientes <Plus size={18} />
          </button>
        </div>
        <div className="ingredient-canvas-wrap">
          {visible && !reduced && !fallback && hasRecipe ? (
            <Scene
              recipe={burger.recipe}
              ingredients={ingredients}
              progress={progress}
              onFailure={() => setFallback(true)}
            />
          ) : (
            <ProductImage burger={burger} className="ingredient-fallback" />
          )}
          <div className="scene-floor-label">
            <Box size={14} />
            <span>ESTUDIO DE INGREDIENTES · {burger.name.toUpperCase()}</span>
          </div>
        </div>
        <div className="ingredient-side">
          <span className="ingredient-step">
            {chapter === 1 ? String(focusIndex + 1).padStart(2, "0") : "✳"}
            <span>
              {chapter === 1
                ? `/ ${String(recipeIngredients.length).padStart(2, "0")}`
                : "PEPONES"}
            </span>
          </span>
          <h3>
            {
              [
                "Todo empieza con una buena idea.",
                scrollIngredient?.name ?? "Cada capa tiene algo que decir.",
                "Juntos, mucho mejor.",
              ][chapter]
            }
          </h3>
          <p>
            {
              [
                "Doble carne, queso y ese toque que lo cambia todo.",
                scrollIngredient?.description ?? "Descubre cada ingrediente.",
                "La mezcla que te hace pensar en el próximo bocado.",
              ][chapter]
            }
          </p>
          <div className="chapter-dots" aria-hidden="true">
            {[0, 1, 2].map((i) => (
              <span className={chapter === i ? "active" : ""} key={i} />
            ))}
          </div>
        </div>
        <div className="ingredient-bottom">
          <span>
            <ArrowDown size={16} /> DESLIZA PARA DESCUBRIR
          </span>
          <span>UNA BUENA BURGER SE NOTA POR DENTRO.</span>
        </div>
        <button
          className="mobile-spread outline-button"
          onClick={() => setMobileSpread(!mobileSpread)}
        >
          {mobileSpread ? "Juntar las capas" : "Separar las capas"}
          {mobileSpread ? <Minus size={18} /> : <Plus size={18} />}
        </button>
      </div>
      <div className="ingredient-accessible-list">
        <p className="eyebrow">TODO LO QUE LLEVA</p>
        <div>
          {recipeIngredients.map((i) => (
            <button
              key={i.id}
              onClick={() => {
                setSelected(i.id);
                setOpen(true);
              }}
            >
              <span style={{ background: i.color }} />
              {i.name}
              <Plus size={14} />
            </button>
          ))}
        </div>
      </div>
      {open && (
        <Dialog
          title={`Explorar los ingredientes de ${burger.name}`}
          onClose={() => {
            setOpen(false);
            setSelected(null);
          }}
          className="explorer-dialog"
        >
          <div className="explorer-visual">
            {!reduced && !fallback && hasRecipe ? (
              <Scene
                recipe={burger.recipe}
                ingredients={ingredients}
                selected={selected}
                onSelect={setSelected}
                interactive
                onFailure={() => setFallback(true)}
              />
            ) : (
              <ProductImage burger={burger} />
            )}
            <button className="reset-view" onClick={() => setSelected(null)}>
              <RotateCcw size={15} /> Volver a juntar
            </button>
          </div>
          <div className="explorer-copy">
            <p className="eyebrow">{burger.name} / POR DENTRO</p>
            <h2>{current ? current.name : "Cada capa cuenta."}</h2>
            <p className="ingredient-description" aria-live="polite">
              {current
                ? current.description
                : "Selecciona un ingrediente y descubre su parte de la historia."}
            </p>
            <div className="ingredient-buttons">
              {recipeIngredients.map((i) => (
                <button
                  aria-pressed={selected === i.id}
                  key={i.id}
                  onClick={() => setSelected(selected === i.id ? null : i.id)}
                >
                  <span style={{ background: i.color }} />
                  {i.name}
                  <ArrowUpRight size={16} />
                </button>
              ))}
            </div>
            <p className="prototype-note">
              Representación ilustrativa de los ingredientes.
            </p>
          </div>
        </Dialog>
      )}
    </section>
  );
}
