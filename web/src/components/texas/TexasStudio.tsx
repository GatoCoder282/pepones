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
  return (
    <main id="contenido" className={styles.studio}>
      <header className={styles.header}>
        <Link href="/" className={styles.back}>
          <ArrowLeft size={18} aria-hidden="true" /> Volver a Pepones
        </Link>
        <span className={styles.headerLabel}>ESTUDIO 3D · TEXAS</span>
      </header>
    </main>
  );
}
