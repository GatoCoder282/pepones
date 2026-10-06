"use client";

import { useEffect, useState } from "react";
import { ArrowUpRight, Search, X } from "lucide-react";
import type { Content, Burger } from "@/lib/content";
import { ContactButton, Dialog, Footer, Header, ProductImage } from "./Shared";

export function MenuPage({ content }: { content: Content }) {
  const [category, setCategory] = useState("Todas");
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Burger | null>(null);
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("category") === "archivo")
      setCategory("Semanales anteriores");
    const burger = content.burgers.find((b) => b.id === params.get("burger"));
    if (burger) setSelected(burger);
  }, [content.burgers]);
  const normalize = (value: string) =>
    value
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();
  const filtered = content.burgers.filter(
    (b) =>
      (category === "Todas" || b.category === category) &&
      normalize(`${b.name} ${b.description}`).includes(normalize(query)),
  );
  return (
    <>
      <Header restaurant={content.restaurant} menuPage />
      <main id="contenido" className="menu-main">
        <div className="menu-page-heading">
          <p className="eyebrow">PEPONES BURGER SHOP / EL MENÚ</p>
          <h1>
            Elige tu
            <br />
            <em>obsesión.</em>
            <span>✳</span>
          </h1>
          <p>Clásicos que se quedan. Semanales que hacen historia.</p>
        </div>
        <div className="menu-disclaimer">
          <span className="status-dot" />
          Carta de referencia · Precios y disponibilidad pendientes de
          confirmación.
        </div>
        <div className="menu-controls">
          <div
            className="category-tabs"
            role="group"
            aria-label="Categoría de hamburguesas"
          >
            {["Todas", "Clásicas", "Semanales anteriores"].map((c) => (
              <button
                key={c}
                aria-pressed={category === c}
                onClick={() => setCategory(c)}
              >
                {c === "Semanales anteriores" ? "El archivo" : c}
              </button>
            ))}
          </div>
          <label className="menu-search">
            <Search size={18} />
            <span className="sr-only">Buscar hamburguesa o ingrediente</span>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="¿Qué se te antoja?"
            />
            {query && (
              <button onClick={() => setQuery("")} aria-label="Borrar búsqueda">
                <X size={15} />
              </button>
            )}
          </label>
        </div>
        <p className="result-count" aria-live="polite">
          {filtered.length} {filtered.length === 1 ? "burger" : "burgers"} para
          descubrir
        </p>
        <div className="menu-grid">
          {filtered.map((b) => (
            <button
              className="menu-card"
              key={b.id}
              onClick={() => setSelected(b)}
            >
              <div
                className={`menu-card-image ${b.image === "hero" ? "menu-card-cutout" : ""}`}
              >
                <ProductImage burger={b} />
                <span className="card-arrow">
                  <ArrowUpRight size={24} />
                </span>
              </div>
              <div className="menu-card-copy">
                <span className="tiny-label">
                  {b.category === "Semanales anteriores"
                    ? "EDICIÓN ANTERIOR"
                    : "UN CLÁSICO PEPONES"}
                </span>
                <div>
                  <h2>{b.name}</h2>
                  <span>
                    {b.price === null ? "Consultar" : `Bs ${b.price}`}
                  </span>
                </div>
                <p>{b.tagline}</p>
              </div>
            </button>
          ))}
        </div>
        {!filtered.length && (
          <div className="empty-state">
            <h2>Ese antojo aún no aparece.</h2>
            <p>Prueba con otro nombre o explora todas las burgers.</p>
            <button
              className="button"
              onClick={() => {
                setQuery("");
                setCategory("Todas");
              }}
            >
              Ver todas
            </button>
          </div>
        )}
        <div className="menu-bottom-note">
          <span>¿El antojo ya tiene nombre?</span>
          <ContactButton restaurant={content.restaurant} />
        </div>
      </main>
      <Footer restaurant={content.restaurant} />
      {selected && (
        <Dialog
          title={selected.name}
          onClose={() => setSelected(null)}
          className="product-dialog"
        >
          <div className="product-dialog-art">
            <ProductImage burger={selected} />
          </div>
          <div className="product-dialog-copy">
            <p className="eyebrow">{selected.category}</p>
            <h2>{selected.name}</h2>
            <p>{selected.description}</p>
            {selected.category === "Semanales anteriores" ? (
              <p className="product-availability">
                Esta burger pertenece al archivo. No implica disponibilidad
                actual.
              </p>
            ) : (
              <p className="product-availability">
                {selected.price === null
                  ? "Precio y disponibilidad por confirmar."
                  : `Bs ${selected.price}`}
              </p>
            )}
            <ContactButton
              restaurant={content.restaurant}
              product={selected.name}
            >
              Consultar {selected.name} <ArrowUpRight size={18} />
            </ContactButton>
          </div>
        </Dialog>
      )}
    </>
  );
}
