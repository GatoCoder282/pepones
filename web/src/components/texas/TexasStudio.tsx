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
