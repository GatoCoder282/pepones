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
    const changing =
      Math.abs(g.position.y - targetY) > 1e-4 ||
      Math.abs(g.position.x - toViewer.x * pull) > 1e-4 ||
      Math.abs(g.position.z - toViewer.z * pull) > 1e-4 ||
      Math.abs(g.scale.x - scale) > 1e-4 ||
      Math.abs(materials[0].userData.dim - dim) > 1e-3;
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
    if (changing) state.invalidate();
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

/** Moves the DOM labels to their projected anchors after every rendered frame. */
function LabelProjector({
  anchors,
  labels,
}: {
  anchors: RefObject<(THREE.Object3D | null)[]>;
  labels: RefObject<(HTMLElement | null)[]>;
}) {
  const point = useMemo(() => new THREE.Vector3(), []);
  useFrame(({ camera, size }) => {
    anchors.current.forEach((anchor, i) => {
      const label = labels.current[i];
      if (!anchor || !label) return;
      anchor.getWorldPosition(point).project(camera);
      const x = (point.x * 0.5 + 0.5) * size.width;
      const y = (-point.y * 0.5 + 0.5) * size.height;
      label.style.transform = `translate3d(${x.toFixed(1)}px, ${y.toFixed(1)}px, 0) translateY(-50%)`;
    });
  });
  return null;
}

function Side({ visible, reducedMotion }: { visible: boolean; reducedMotion: boolean }) {
  const { object } = useAsset(TEXAS_SIDE.url);
  const group = useRef<THREE.Group>(null);
  useFrame((state, delta) => {
    const g = group.current;
    if (!g) return;
    const target = visible ? 1 : 0.001;
    const next = approach(g.scale.x, target, reducedMotion ? 60 : 6, delta);
    g.scale.setScalar(next);
    g.visible = next > 0.01;
    if (Math.abs(next - target) > 1e-3) state.invalidate();
  });
  return (
    <group ref={group} position={TEXAS_SIDE.position} rotation={TEXAS_SIDE.rotation} scale={0.001}>
      <primitive object={object} />
    </group>
  );
}

function framing(spread: number, showSide: boolean, aspect: number) {
  const top = HEIGHT + LAST * GAP * spread;
  const height = top + 0.25;
  const width = BURGER_WIDTH + (showSide ? 2.4 : 0);
  const v = THREE.MathUtils.degToRad(FOV) / 2;
  const h = Math.atan(Math.tan(v) * aspect);
  const distance = Math.max(height / 2 / Math.tan(v), width / 2 / Math.tan(h)) * 1.3 + 1.3;
  return {
    target: new THREE.Vector3(showSide ? SIDE_SHIFT : 0, top / 2 - 0.05, showSide ? -0.35 : 0),
    radius: Math.min(Math.max(distance, 5.2), 17),
  };
}

function CameraRig({
  controls,
  spread,
  showSide,
  resetKey,
  command,
  reducedMotion,
  compact,
}: {
  controls: RefObject<OrbitControlsImpl | null>;
  spread: number;
  showSide: boolean;
  resetKey: number;
  command: ViewCommand | null;
  reducedMotion: boolean;
  compact: boolean;
}) {
  const { camera, size, invalidate } = useThree();
  const goal = useRef<{ target: THREE.Vector3; radius: number; theta?: number; phi?: number } | null>(null);
  const spherical = useMemo(() => new THREE.Spherical(), []);
  const offset = useMemo(() => new THREE.Vector3(), []);
  const aspect = size.width / Math.max(size.height, 1);

  useEffect(() => {
    // Panels cover part of the canvas: shift the projection, not the orbit target.
    const perspective = camera as THREE.PerspectiveCamera;
    const [x, y] = compact ? [0, 0.06] : [-0.06, 0.035];
    perspective.setViewOffset(size.width, size.height, size.width * x, size.height * y, size.width, size.height);
    perspective.updateProjectionMatrix();
    invalidate();
  }, [camera, size.width, size.height, compact, invalidate]);
  useEffect(() => {
    goal.current = framing(spread, showSide, aspect);
    invalidate();
  }, [spread, showSide, aspect, invalidate]);
  useEffect(() => {
    if (resetKey === 0) return;
    goal.current = { ...framing(0, false, aspect), theta: DEFAULT_THETA, phi: DEFAULT_PHI };
    invalidate();
    // Only a reset restores the default angle; aspect changes keep the user's view.
  }, [resetKey]);
  useEffect(() => {
    const c = controls.current;
    if (!command || !c) return;
    spherical.setFromVector3(offset.copy(camera.position).sub(c.target));
    goal.current = {
      target: (goal.current?.target ?? c.target).clone(),
      radius:
        command.kind === "zoom"
          ? THREE.MathUtils.clamp(spherical.radius * command.amount, c.minDistance, c.maxDistance)
          : (goal.current?.radius ?? spherical.radius),
      theta: command.kind === "rotate" ? spherical.theta + command.amount : undefined,
      phi: spherical.phi,
    };
    invalidate();
  }, [command, camera, controls, spherical, offset, invalidate]);
  useEffect(() => {
    const c = controls.current;
    if (!c) return;
    // Dragging hands the camera angle to the user; framing still follows the layers.
    const stop = () => {
      if (goal.current) goal.current = { ...goal.current, theta: undefined, phi: undefined };
    };
    c.addEventListener("start", stop);
    return () => c.removeEventListener("start", stop);
  }, [controls]);
  useFrame((state, delta) => {
    const c = controls.current;
    const g = goal.current;
    if (!c || !g) return;
    const rate = reducedMotion ? 60 : 4.5;
    c.target.set(
      approach(c.target.x, g.target.x, rate, delta),
      approach(c.target.y, g.target.y, rate, delta),
      approach(c.target.z, g.target.z, rate, delta),
    );
    spherical.setFromVector3(offset.copy(camera.position).sub(c.target));
    spherical.radius = approach(spherical.radius, g.radius, rate, delta);
    if (g.theta !== undefined) {
      const d = Math.atan2(Math.sin(g.theta - spherical.theta), Math.cos(g.theta - spherical.theta));
      spherical.theta = approach(spherical.theta, spherical.theta + d, rate, delta);
    }
    if (g.phi !== undefined) spherical.phi = approach(spherical.phi, g.phi, rate, delta);
    camera.position.copy(c.target).add(offset.setFromSpherical(spherical));
    c.update();
    const settled =
      c.target.distanceTo(g.target) < 1e-3 &&
      Math.abs(spherical.radius - g.radius) < 1e-3 &&
      (g.theta === undefined || Math.abs(Math.sin(g.theta - spherical.theta)) < 1e-3) &&
      (g.phi === undefined || Math.abs(g.phi - spherical.phi) < 1e-3);
    if (settled) goal.current = null;
    else state.invalidate();
  });
  return null;
}

function SceneContents(
  props: SceneProps &
    Pointing & {
      anchors: RefObject<(THREE.Object3D | null)[]>;
      labels: RefObject<(HTMLElement | null)[]>;
    },
) {
  const { gl } = useThree();
  const controls = useRef<OrbitControlsImpl>(null);
  const [sideRequested, setSideRequested] = useState(false);
  const { onReady, onFailure, hovered, anchors, showSide } = props;
  useEffect(() => {
    if (showSide) setSideRequested(true);
  }, [showSide]);
  useEffect(() => {
    controls.current?.target.set(0, HEIGHT * 0.47, 0);
    controls.current?.update();
    onReady();
  }, [onReady]);
  useEffect(() => {
    const fail = (event: Event) => {
      event.preventDefault();
      onFailure();
    };
    gl.domElement.addEventListener("webglcontextlost", fail);
    return () => gl.domElement.removeEventListener("webglcontextlost", fail);
  }, [gl, onFailure]);
  useEffect(() => {
    gl.domElement.style.cursor = hovered ? "pointer" : "";
  }, [gl, hovered]);
  return (
    <>
      <hemisphereLight args={["#fff3dc", "#6b4a2c", 0.55]} />
      <directionalLight
        position={[-3.2, 7.5, 5]}
        intensity={2.3}
        color="#fff1dc"
        castShadow
        shadow-mapSize={[2048, 2048]}
        shadow-bias={-0.0004}
        shadow-normalBias={0.025}
        shadow-camera-left={-4.5}
        shadow-camera-right={4.5}
        shadow-camera-top={6.5}
        shadow-camera-bottom={-2}
        shadow-camera-near={1}
        shadow-camera-far={22}
      />
      <directionalLight position={[4.5, 2.5, 2]} intensity={0.6} color="#fff1e0" />
      <directionalLight position={[1.5, 4.5, -5]} intensity={1.1} color="#ffd9a8" />
      <Environment resolution={256} frames={1}>
        <Lightformer intensity={2.2} position={[-3, 4, 4]} rotation={[0, -0.6, 0]} scale={[5, 4, 1]} color="#fff2de" />
        <Lightformer intensity={0.9} position={[4, 1.5, 2]} rotation={[0, 1.1, 0]} scale={[4, 3, 1]} color="#fff4e8" />
        <Lightformer intensity={1.6} position={[1, 3, -4]} rotation={[0, Math.PI, 0]} scale={[4, 2, 1]} color="#ffdcb0" />
        <Lightformer intensity={0.5} position={[0, -2, 3]} rotation={[0.6, 0, 0]} scale={[6, 2, 1]} color="#fff5e6" />
      </Environment>
      <group>
        {TEXAS_LAYERS.map((layer) => (
          <Layer
            key={`${layer.assetId}-${layer.index}`}
            layer={layer}
            spread={props.spread}
            selected={props.selected}
            hovered={hovered}
            setHovered={props.setHovered}
            onSelect={props.onSelect}
            reducedMotion={props.reducedMotion}
            compact={props.compact}
            anchor={(g) => {
              anchors.current[layer.index] = g;
            }}
          />
        ))}
        {sideRequested && (
          <Suspense fallback={null}>
            <Side visible={showSide} reducedMotion={props.reducedMotion} />
          </Suspense>
        )}
      </group>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.002, 0]} receiveShadow>
        <circleGeometry args={[7, 48]} />
        <shadowMaterial transparent opacity={0.16} />
      </mesh>
      <ContactShadows position={[0, 0.001, 0]} opacity={0.42} scale={9} blur={2.6} far={1.4} resolution={512} color="#3b2414" />
      <OrbitControls
        ref={controls}
        makeDefault
        enablePan={false}
        enableDamping
        dampingFactor={0.08}
        minDistance={3.2}
        maxDistance={18}
        minPolarAngle={0.2}
        maxPolarAngle={1.62}
      />
    </>
  );
}
