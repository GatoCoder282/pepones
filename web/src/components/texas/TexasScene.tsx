"use client";

import { Canvas, useFrame, useThree } from "@react-three/fiber";
import {
  ContactShadows,
  Environment,
  Lightformer,
  OrbitControls,
  useGLTF,
  useProgress,
} from "@react-three/drei";
import {
  Component,
  Suspense,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
  type RefObject,
} from "react";
import * as THREE from "three";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import {
  TEXAS_LAYERS,
  TEXAS_MODEL,
  TEXAS_SIDE,
  ingredientById,
  ingredientNumber,
  type TexasIngredientId,
  type TexasLayer,
} from "@/lib/texas";
import styles from "./TexasStudio.module.css";

export interface ViewCommand {
  kind: "rotate" | "zoom";
  amount: number;
  id: number;
}

interface SceneProps {
  spread: number;
  selected: TexasIngredientId | null;
  showSide: boolean;
  resetKey: number;
  command: ViewCommand | null;
  reducedMotion: boolean;
  compact: boolean;
  onSelect: (id: TexasIngredientId) => void;
  onReady: () => void;
  onFailure: () => void;
  onProgress: (percent: number) => void;
}

interface Pointing {
  hovered: TexasIngredientId | null;
  setHovered: (id: TexasIngredientId | null) => void;
}

// Extra height between consecutive layers when fully separated.
const GAP = 0.27;
const HEIGHT = TEXAS_MODEL.height;
const LAST = TEXAS_LAYERS.length - 1;
const DEFAULT_THETA = 0.18;
const DEFAULT_PHI = 1.38;
const FOV = 30;
const BURGER_WIDTH = 2.7;
const SIDE_SHIFT = 1.15;
