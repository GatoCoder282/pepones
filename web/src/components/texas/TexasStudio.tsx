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
