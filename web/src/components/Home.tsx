"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import {
  ArrowDown,
  ArrowUpRight,
  MoveUpRight,
  MapPin,
  Plus,
  Sparkles,
} from "lucide-react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { type Content, weeklyAvailability } from "@/lib/content";
import {
  ContactButton,
  Footer,
  Header,
  ProductImage,
  TextLink,
} from "./Shared";
import { IngredientExperience } from "./IngredientExperience";

gsap.registerPlugin(ScrollTrigger);

export function Home({ content }: { content: Content }) {
  const { weekly, restaurant, burgers, ingredients } = content;
  const burger = burgers.find((b) => b.id === weekly.burgerId)!;
  const root = useRef<HTMLDivElement>(null);
  const [availability, setAvailability] = useState(() =>
    weekly.demo ? "demo" : "unavailable",
  );
  useEffect(() => {
    const update = () => setAvailability(weeklyAvailability(weekly));
    update();
    const timer = window.setInterval(update, 30_000);
    return () => clearInterval(timer);
  }, [weekly]);
  useEffect(() => {
    const mm = gsap.matchMedia();
    mm.add(
      "(prefers-reduced-motion: no-preference)",
      () => {
        gsap.fromTo(
          ".hero-word",
          { yPercent: 108 },
          { yPercent: 0, duration: 1.05, ease: "power4.out", stagger: 0.12 },
        );
        gsap.fromTo(
          ".hero-burger",
          { y: 48, rotation: -5, opacity: 0 },
          {
            y: 0,
            rotation: -3,
            opacity: 1,
            duration: 1.25,
            delay: 0.22,
            ease: "power3.out",
          },
        );
        gsap.to(".hero-burger", {
          y: -45,
          rotation: 1,
          ease: "none",
          scrollTrigger: {
            trigger: ".hero",
            start: "top top",
            end: "bottom top",
            scrub: 1,
          },
        });
        gsap.utils.toArray<HTMLElement>("[data-reveal]").forEach((el) =>
          gsap.fromTo(
            el,
            { y: 35, opacity: 0 },
            {
              y: 0,
              opacity: 1,
              duration: 0.8,
              ease: "power3.out",
              scrollTrigger: { trigger: el, start: "top 92%", once: true },
            },
          ),
        );
      },
      root,
    );
    return () => mm.revert();
  }, []);
  const statusText = {
    demo: "EDICIÓN DE DEMOSTRACIÓN",
    available: "LA SEMANAL ESTÁ AQUÍ",
    "sold-out": "ESTA SEMANAL SE AGOTÓ",
    expired: "UNA SEMANAL PARA RECORDAR",
    upcoming: "MUY PRONTO",
    unavailable: "DESCUBRE NUESTRAS BURGERS",
  }[availability];
  const archive = ["fugazzeta", "pepmuffin", "caribena", "vaquera"].map((id) =>
    burgers.find((b) => b.id === id)!,
  );
  return (
    <div
      ref={root}
      style={{ "--weekly-accent": weekly.accent } as React.CSSProperties}
    >
      <Header restaurant={restaurant} />
      <main id="contenido">
        <section className="hero" id="semanal" aria-labelledby="hero-title">
          <div className="hero-kicker">
            <span className="status-dot" />
            {statusText}
          </div>
          <h1 id="hero-title">
            <span className="hero-line">
              <span className="hero-word">OTRA SEMANA.</span>
            </span>
            <span className="hero-line">
              <span className="hero-word">
                OTRA <em>OBSESIÓN.</em>
              </span>
            </span>
          </h1>
          <div className="hero-side hero-side-left">
            <span className="tiny-label">EL ANTOJO DE HOY</span>
            <h2>{burger.name}</h2>
            <p>{burger.tagline}</p>
            {burger.price !== null && (
              <p className="hero-price">Bs {burger.price}</p>
            )}
            {weekly.startsAt && weekly.endsAt && (
              <p className="hero-dates">
                {new Intl.DateTimeFormat("es-BO", {
                  day: "numeric",
                  month: "short",
                  timeZone: "America/La_Paz",
                }).format(new Date(weekly.startsAt))}{" "}
                —{" "}
                {new Intl.DateTimeFormat("es-BO", {
                  day: "numeric",
                  month: "short",
                  timeZone: "America/La_Paz",
                }).format(new Date(weekly.endsAt))}
              </p>
            )}
            <a
              className="circle-link"
              href="#ingredientes"
              aria-label="Descubrir los ingredientes"
            >
              <ArrowDown size={25} />
            </a>
          </div>
          <div className="hero-product">
            <div className="hero-orbit" />
            <ProductImage burger={burger} className="hero-burger" priority />
            {burger.image === "hero" && (
              <span className="hero-image-caption">IMAGEN ILUSTRATIVA</span>
            )}
          </div>
          <div className="hero-seal" aria-label="Burger de la semana">
            <span>LA BURGER</span>
            <strong>
              de la
              <br />
              semana
            </strong>
            <Sparkles size={20} />
          </div>
          <div className="hero-side hero-side-right">
            <span className="handwritten">
              hecha para
              <br />
              romper la rutina.
            </span>
            <svg viewBox="0 0 90 70" aria-hidden="true">
              <path
                d="M75 5C80 50 32 18 10 59m0 0 3-21m-3 21 22-3"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              />
            </svg>
          </div>
          <div className="hero-bottom">
            <p>
              Las semanas cambian.
              <br />
              <strong>Las ganas de Pepones, nunca.</strong>
            </p>
            <div className="hero-actions">
              <a className="button" href="#ingredientes">
                Descubre qué lleva <Plus size={19} />
              </a>
              {availability === "available" ? (
                <ContactButton
                  restaurant={restaurant}
                  product={burger.name}
                  className="hero-order"
                />
              ) : (
                <Link className="hero-order" href="/menu/">
                  Explorar el menú <ArrowUpRight size={17} />
                </Link>
              )}
            </div>
            <span className="scroll-hint">
              SIGUE EL ANTOJO <ArrowDown size={16} />
            </span>
          </div>
        </section>
        <div className="brand-ribbon" aria-hidden="true">
          <div>
            {Array.from({ length: 4 }, (_, i) => (
              <span key={i}>
                NUNCA LA MISMA. SIEMPRE PEPONES.{" "}
                <span className="ribbon-flower">✳</span>
              </span>
            ))}
          </div>
        </div>
        <IngredientExperience burger={burger} ingredients={ingredients} />
        <section
          className="archive-section section-pad"
          aria-labelledby="archive-title"
        >
          <div className="section-heading" data-reveal>
            <div>
              <p className="eyebrow">01 / EL ARCHIVO DEL ANTOJO</p>
              <h2 id="archive-title">
                Pasaron por aquí.
                <br />
                <em>Se quedaron contigo.</em>
              </h2>
            </div>
            <p>
              Cada semanal tiene su historia.
              <br />
              Estas son algunas de las nuestras.
            </p>
          </div>
          <div className="archive-grid">
            {archive.map((b, i) => (
              <Link
                href={`/menu/?burger=${b.id}`}
                className="archive-card"
                key={b.id}
                data-reveal
              >
                <div className={`archive-art archive-art-${i}`}>
                  <ProductImage burger={b} />
                  <span className="card-arrow">
                    <ArrowUpRight size={24} />
                  </span>
                </div>
                <div className="archive-card-caption">
                  <span className="tiny-label">
                    EDICIÓN DEL ARCHIVO · 0{i + 1}
                  </span>
                  <h3>{b.name}</h3>
                </div>
              </Link>
            ))}
          </div>
          <div className="archive-note">
            <span>Hay burgers que merecen un bis.</span>
            <TextLink href="/menu/?category=archivo">
              Explorar las ediciones
            </TextLink>
          </div>
        </section>
        <section className="story-section" id="pepones">
          <div className="story-checks" aria-hidden="true" />
          <div className="story-copy" data-reveal>
            <p className="eyebrow">02 / MUY DE AQUÍ. MUY PEPONES.</p>
            <h2>
              No hacemos
              <br />
              semanas
              <br />
              <em>iguales.</em>
            </h2>
            <div className="story-bottom">
              <span className="story-star" aria-hidden="true">
                ✳
              </span>
              <div>
                <p>
                  Tenemos nuestros clásicos. Y tenemos esa idea nueva que no nos
                  deja tranquilos hasta ponerla entre dos panes.
                </p>
                <p>
                  Así nace la semanal. Una excusa para probar, sorprender y
                  volver a encontrarnos. Desde Cochabamba, con mucho antojo.
                </p>
                <a
                  className="light-link"
                  href={restaurant.instagram}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Conoce el mundo Pepones <ArrowUpRight size={18} />
                </a>
              </div>
            </div>
          </div>
          <div className="story-poster">
            <span className="poster-small">BURGER SHOP · COCHABAMBA</span>
            <div className="poster-type">
              BUENA
              <br />
              CARNE.
              <br />
              <em>BUENAS</em>
              <br />
              IDEAS.
            </div>
            <div className="poster-stamp">
              P
              <span>
                HECHAS CON
                <br />
                PERSONALIDAD
              </span>
            </div>
          </div>
        </section>
        <section className="menu-teaser section-pad">
          <div data-reveal>
            <p className="eyebrow">03 / LOS QUE SIEMPRE VUELVEN</p>
            <h2>
              Lo nuestro
              <br />
              es <em>hambre.</em>
            </h2>
            <p>
              Para los fieles a su favorita.
              <br />
              Para los que piden «algo diferente».
            </p>
            <Link className="button" href="/menu/">
              Encuentra tu próxima burger <ArrowUpRight size={19} />
            </Link>
          </div>
          <div className="menu-teaser-visual">
            <div className="teaser-checks" />
            <img
              src="/images/burger-hero.webp"
              width={1200}
              height={800}
              alt="Ilustración de una hamburguesa doble de Pepones"
              loading="lazy"
            />
            <span className="teaser-caption">DOBLE CARNE. DOBLE SONRISA.</span>
          </div>
        </section>
        <section className="location section-pad" id="encuentranos">
          <div data-reveal>
            <p className="eyebrow">04 / NOS VEMOS EN PEPONES</p>
            <h2>
              Tu antojo
              <br />
              tiene <em>dirección.</em>
            </h2>
          </div>
          <div className="location-details">
            <MapPin size={28} />
            <h3>{restaurant.address}</h3>
            <p>{restaurant.city}</p>
            <div className="location-rule" />
            <div className="location-meta">
              <span>HORARIOS</span>
              <p>
                {restaurant.hours ??
                  "Consulta los horarios de hoy en Instagram."}
              </p>
            </div>
            <div className="location-actions">
              <a
                className="button"
                href={
                  restaurant.mapsUrl ??
                  `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent("Pepones Burger Avenida Potosí Juan Capriles Cochabamba Bolivia")}`
                }
                target="_blank"
                rel="noopener noreferrer"
              >
                {restaurant.mapsUrl ? "Cómo llegar" : "Buscar en Maps"}{" "}
                <MoveUpRight size={18} />
              </a>
              <ContactButton restaurant={restaurant} className="text-link">
                Hablemos <ArrowUpRight size={18} />
              </ContactButton>
            </div>
          </div>
        </section>
        <div className="closing-line">
          Nos vemos en el próximo <em>bocado.</em>
          <span>↗</span>
        </div>
      </main>
      <Footer restaurant={restaurant} />
    </div>
  );
}
