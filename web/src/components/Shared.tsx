"use client";

import Link from "next/link";
import {
  ArrowUpRight,
  Menu,
  X,
  Instagram,
  MessageCircle,
  ArrowRight,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { Burger, Restaurant } from "@/lib/content";
import { whatsappLink } from "@/lib/content";

export function Brand({ light = false }: { light?: boolean }) {
  return (
    <Link
      href="/"
      aria-label="Pepones, inicio"
      className={`brand ${light ? "brand-light" : ""}`}
    >
      Pepones<span>BURGER SHOP</span>
    </Link>
  );
}

export function Dialog({
  title,
  children,
  onClose,
  className = "",
}: {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
  className?: string;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const node = ref.current;
    const previousFocus = document.activeElement as HTMLElement | null;
    const priorOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    node?.showModal();
    return () => {
      node?.close();
      document.body.style.overflow = priorOverflow;
      previousFocus?.focus();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      aria-label={title}
      className={`dialog ${className}`}
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="dialog-inner">
        <button
          className="icon-button dialog-close"
          onClick={onClose}
          aria-label="Cerrar"
        >
          <X size={23} />
        </button>
        {children}
      </div>
    </dialog>
  );
}

export function ContactButton({
  restaurant,
  product,
  className = "button",
  children,
}: {
  restaurant: Restaurant;
  product?: string;
  className?: string;
  children?: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const href = whatsappLink(restaurant.whatsapp, product);
  return (
    <>
      {href ? (
        <a
          className={className}
          href={href}
          target="_blank"
          rel="noopener noreferrer"
        >
          {children ?? (
            <>
              Hablemos por WhatsApp <ArrowUpRight size={17} />
            </>
          )}
        </a>
      ) : (
        <button className={className} onClick={() => setOpen(true)}>
          {children ?? (
            <>
              Hablemos por WhatsApp <ArrowUpRight size={17} />
            </>
          )}
        </button>
      )}
      {open && (
        <Dialog title="Contactar a Pepones" onClose={() => setOpen(false)}>
          <div className="contact-dialog">
            <MessageCircle size={32} />
            <p className="eyebrow">Hablemos de burgers</p>
            <h2>
              El antojo
              <br />
              no espera.
            </h2>
            <p>
              El número de WhatsApp está pendiente de confirmación. Por ahora,
              consulta las novedades y la disponibilidad directamente en el
              Instagram de Pepones.
            </p>
            <a
              className="button"
              href={restaurant.instagram}
              target="_blank"
              rel="noopener noreferrer"
            >
              Ir a Instagram <Instagram size={18} />
            </a>
          </div>
        </Dialog>
      )}
    </>
  );
}

export function Header({
  restaurant,
  menuPage = false,
}: {
  restaurant: Restaurant;
  menuPage?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const links = [
    { label: "La semanal", href: "/#semanal" },
    { label: "El menú", href: "/menu/" },
    { label: "Somos Pepones", href: "/#pepones" },
    { label: "Encuéntranos", href: "/#encuentranos" },
  ];
  useEffect(() => {
    const close = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, []);
  return (
    <>
      <a className="skip-link" href="#contenido">
        Saltar al contenido
      </a>
      <div className="topline">
        <span>HECHAS CON PERSONALIDAD.</span>
        <span>
          COCHABAMBA, BOLIVIA <span aria-hidden="true">↗</span>
        </span>
      </div>
      <header className="header">
        <Brand />
        <nav className="desktop-nav" aria-label="Principal">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              aria-current={
                menuPage && l.href === "/menu/" ? "page" : undefined
              }
            >
              {l.label}
            </Link>
          ))}
        </nav>
        <ContactButton restaurant={restaurant} className="nav-contact">
          Hablemos <ArrowUpRight size={16} />
        </ContactButton>
        <button
          className="icon-button mobile-menu-toggle"
          aria-expanded={open}
          aria-controls="mobile-navigation"
          aria-label={open ? "Cerrar navegación" : "Abrir navegación"}
          onClick={() => setOpen(!open)}
        >
          {open ? <X /> : <Menu />}
        </button>
        {open && (
          <nav
            className="mobile-nav"
            id="mobile-navigation"
            aria-label="Principal móvil"
          >
            {links.map((l) => (
              <Link onClick={() => setOpen(false)} key={l.href} href={l.href}>
                {l.label}
                <ArrowUpRight size={20} />
              </Link>
            ))}
          </nav>
        )}
      </header>
    </>
  );
}

export function ProductImage({
  burger,
  className = "",
  priority = false,
}: {
  burger: Burger;
  className?: string;
  priority?: boolean;
}) {
  if (burger.image === "hero" || burger.image.startsWith("/"))
    return (
      <img
        className={`product-cutout ${className}`}
        src={
          burger.image === "hero" ? "/images/burger-hero.webp" : burger.image
        }
        alt={
          burger.name + (burger.image === "hero" ? " — imagen ilustrativa" : "")
        }
        loading={priority ? "eager" : "lazy"}
        fetchPriority={priority ? "high" : undefined}
        width={1200}
        height={800}
      />
    );
  const [collection, rawIndex] = burger.image.split("-");
  const index = Number(rawIndex);
  return (
    <div
      role="img"
      aria-label={`Campaña original de ${burger.name}`}
      className={`campaign-image ${className}`}
      style={{
        backgroundImage: `url(/images/${collection === "archive" ? "weekly-archive" : "campaigns"}.png)`,
        backgroundPosition: `${((index % 4) * 100) / 3}% ${index < 4 ? 0 : 100}%`,
      }}
    />
  );
}

export function Footer({ restaurant }: { restaurant: Restaurant }) {
  return (
    <footer className="footer">
      <div className="footer-top">
        <Brand light />
        <p>
          Una semana.
          <br />
          Otra buena razón para volver.
        </p>
        <a
          href={restaurant.instagram}
          target="_blank"
          rel="noopener noreferrer"
          className="footer-social"
        >
          Nos vemos en Instagram <ArrowUpRight size={22} />
        </a>
      </div>
      <div className="footer-bottom">
        <span>© {new Date().getFullYear()} Pepones Burger Shop</span>
        <span>Hecho para el antojo. Desde Cochabamba.</span>
        <a href="#contenido">Volver arriba ↑</a>
      </div>
    </footer>
  );
}

export function TextLink({
  href,
  children,
}: {
  href: string;
  children: React.ReactNode;
}) {
  return (
    <Link className="text-link" href={href}>
      {children}
      <ArrowRight size={18} />
    </Link>
  );
}
