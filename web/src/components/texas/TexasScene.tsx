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

// The side dish downloads only when someone asks to see it.
for (const url of new Set(TEXAS_LAYERS.map((l) => l.url))) useGLTF.preload(url, false, true);

class SceneBoundary extends Component<
  { onFailure: () => void; children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch() {
    this.props.onFailure();
  }
  render() {
    return this.state.failed ? null : this.props.children;
  }
}

/** Frame-rate independent exponential approach towards a target. */
function approach(current: number, target: number, rate: number, delta: number) {
  return current + (target - current) * (1 - Math.exp(-rate * delta));
}

function useAsset(url: string) {
  const { scene } = useGLTF(url, false, true);
  return useMemo(() => {
    const clone = scene.clone(true);
    const materials: THREE.MeshStandardMaterial[] = [];
    clone.traverse((child) => {
      const mesh = child as THREE.Mesh;
      if (!mesh.isMesh) return;
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      // Each layer owns its materials so it can be dimmed on its own.
      const material = (mesh.material as THREE.MeshStandardMaterial).clone();
      material.userData.baseColor = material.color.clone();
      material.userData.dim = 1;
      material.envMapIntensity = 0.9;
      mesh.material = material;
      materials.push(material);
    });
    // Labels sit at the visual middle of each layer, not at its resting plane.
    const box = new THREE.Box3().setFromObject(clone);
    return { object: clone, materials, middle: (box.min.y + box.max.y) / 2 };
  }, [scene]);
}

function Layer({
  layer,
  spread,
  selected,
  hovered,
  setHovered,
  onSelect,
  reducedMotion,
  compact,
  anchor,
}: Pointing & {
  layer: TexasLayer;
  spread: number;
  selected: TexasIngredientId | null;
  onSelect: (id: TexasIngredientId) => void;
  reducedMotion: boolean;
  compact: boolean;
  anchor: (group: THREE.Group | null) => void;
}) {
  const { object, materials, middle } = useAsset(layer.url);
  const group = useRef<THREE.Group>(null);
  const tag = useRef<THREE.Group>(null);
  const chosen = selected === layer.ingredientId;
  const pointed = hovered === layer.ingredientId;
  const toViewer = useMemo(() => new THREE.Vector3(), []);
  const right = useMemo(() => new THREE.Vector3(), []);
  useFrame((state, delta) => {
    const g = group.current;
    if (!g) return;
    const rate = reducedMotion ? 60 : 7;
    const camera = state.camera;
    toViewer.set(camera.position.x, 0, camera.position.z).normalize();
    const pull = chosen ? 0.34 : 0;
    const targetY = layer.y + layer.index * GAP * spread;
    const scale = chosen ? 1.035 : pointed ? 1.02 : 1;
    const dim = selected && !chosen ? 0.45 : 1;
    g.position.y = approach(g.position.y, targetY, rate, delta);
    g.position.x = approach(g.position.x, toViewer.x * pull, rate, delta);
    g.position.z = approach(g.position.z, toViewer.z * pull, rate, delta);
    g.scale.setScalar(approach(g.scale.x, scale, rate, delta));
    for (const material of materials) {
      material.userData.dim = approach(material.userData.dim, dim, rate, delta);
      material.color.copy(material.userData.baseColor).multiplyScalar(material.userData.dim);
    }
    if (tag.current) {
      // The label anchor stays on the viewer's right of the layer, whatever the orbit.
      right.setFromMatrixColumn(camera.matrixWorld, 0).setY(0).normalize();
      const reach = compact ? 1.3 : 1.6;
      tag.current.position.set(right.x * reach, middle, right.z * reach);
    }
  });
  return (
    <group
      ref={group}
      position={[0, layer.y, 0]}
      onClick={(e) => {
        e.stopPropagation();
        onSelect(layer.ingredientId);
      }}
      onPointerOver={(e) => {
        e.stopPropagation();
        setHovered(layer.ingredientId);
      }}
      onPointerOut={() => setHovered(null)}
    >
      <group rotation={layer.rotation}>
        <primitive object={object} />
      </group>
      <group
        ref={(g) => {
          tag.current = g;
          anchor(g);
        }}
      />
    </group>
  );
}
