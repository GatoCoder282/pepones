"use client";

import { Canvas, useFrame, useThree } from "@react-three/fiber";
import {
  ContactShadows,
  Environment,
  Lightformer,
  OrbitControls,
  useGLTF,
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
import type { Ingredient, RecipeLayer } from "@/lib/content";

interface SceneProps {
  recipe: RecipeLayer[];
  ingredients: Ingredient[];
  progress?: RefObject<{ value: number }>;
  selected?: string | null;
  onSelect?: (id: string) => void;
  interactive?: boolean;
  spread?: number;
  studio?: boolean;
  onReady?: () => void;
  onFailure: () => void;
}
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

function ImportedIngredient({ url }: { url: string }) {
  const { scene } = useGLTF(url);
  const clone = useMemo(() => scene.clone(true), [scene]);
  return <primitive object={clone} />;
}

function Bun({ top }: { top: boolean }) {
  const points = useMemo(
    () =>
      top
        ? [
            new THREE.Vector2(0, -0.03),
            new THREE.Vector2(0.92, -0.03),
            ...Array.from({ length: 25 }, (_, i) => {
              const angle = ((i / 24) * Math.PI) / 2;
              return new THREE.Vector2(
                1.12 * Math.cos(angle),
                0.09 + 0.6 * Math.sin(angle),
              );
            }),
          ]
        : [
            new THREE.Vector2(0, -0.15),
            new THREE.Vector2(0.85, -0.15),
            new THREE.Vector2(1.05, -0.08),
            new THREE.Vector2(1.08, 0.09),
            new THREE.Vector2(0.98, 0.19),
            new THREE.Vector2(0, 0.19),
          ],
    [top],
  );
  return (
    <group>
      <mesh castShadow receiveShadow>
        <latheGeometry args={[points, 64]} />
        <meshStandardMaterial
          color={top ? "#c98432" : "#dca451"}
          roughness={0.48}
        />
      </mesh>
      {top &&
        Array.from({ length: 62 }, (_, i) => {
          const a = i * 2.39996;
          const r = Math.sqrt((i + 0.5) / 62) * 0.96;
          const y = 0.09 + 0.6 * Math.sqrt(1 - Math.pow(r / 1.12, 2));
          return (
            <mesh
              key={i}
              position={[Math.cos(a) * r, y + 0.014, Math.sin(a) * r]}
              rotation={[r * 0.5 * Math.sin(a), a, -r * 0.5 * Math.cos(a)]}
              scale={[0.025, 0.014, 0.068]}
            >
              <sphereGeometry args={[1, 6, 5]} />
              <meshStandardMaterial color="#f8deb0" roughness={0.8} />
            </mesh>
          );
        })}
    </group>
  );
}

function Patty() {
  const geometry = useMemo(() => {
    const g = new THREE.CylinderGeometry(1.04, 1.08, 0.25, 64, 4);
    const p = g.attributes.position;
    for (let i = 0; i < p.count; i++) {
      const x = p.getX(i),
        y = p.getY(i),
        z = p.getZ(i);
      const theta = Math.atan2(z, x);
      const bump = Math.sin(theta * 17) * 0.027 + Math.sin(theta * 31) * 0.018;
      p.setXYZ(
        i,
        x * (1 + bump),
        y + Math.sin(x * 19 + z * 23) * 0.022,
        z * (1 + bump),
      );
    }
    g.computeVertexNormals();
    return g;
  }, []);
  useEffect(() => () => geometry.dispose(), [geometry]);
  return (
    <group>
      <mesh geometry={geometry} castShadow receiveShadow>
        <meshStandardMaterial color="#583020" roughness={0.94} />
      </mesh>
      {Array.from({ length: 32 }, (_, i) => {
        const a = i * 2.39996;
        return (
          <mesh
            key={i}
            position={[
              Math.cos(a) * 1.02,
              Math.sin(i * 7) * 0.05,
              Math.sin(a) * 1.02,
            ]}
            scale={[0.09, 0.065, 0.085]}
          >
            <dodecahedronGeometry args={[1, 1]} />
            <meshStandardMaterial
              color={i % 3 === 0 ? "#a25c33" : "#412219"}
              roughness={0.95}
            />
          </mesh>
        );
      })}
    </group>
  );
}

function Cheese() {
  const geometry = useMemo(() => {
    const g = new THREE.PlaneGeometry(1.9, 1.9, 16, 16);
    const p = g.attributes.position;
    for (let i = 0; i < p.count; i++) {
      const x = p.getX(i),
        z = p.getY(i);
      const d = Math.sqrt(x * x + z * z);
      p.setXYZ(
        i,
        x,
        -0.02 - Math.max(0, d - 0.83) * 0.65 + Math.sin(x * 4 + z * 3) * 0.025,
        z,
      );
    }
    g.computeVertexNormals();
    return g;
  }, []);
  useEffect(() => () => geometry.dispose(), [geometry]);
  return (
    <mesh geometry={geometry} rotation={[0, 0.25, 0]} castShadow>
      <meshStandardMaterial
        color="#ffc12a"
        side={THREE.DoubleSide}
        roughness={0.35}
      />
    </mesh>
  );
}

function Greens() {
  return (
    <group>
      {Array.from({ length: 13 }, (_, i) => {
        const a = i * 2.39996;
        return (
          <mesh
            key={i}
            position={[
              Math.cos(a) * 0.72,
              Math.sin(i) * 0.045,
              Math.sin(a) * 0.72,
            ]}
            rotation={[0, a, Math.sin(i) * 0.2]}
            scale={[0.43, 0.04, 0.28]}
          >
            <sphereGeometry args={[1, 10, 6]} />
            <meshStandardMaterial
              color={i % 3 === 0 ? "#52722c" : "#96b94e"}
              roughness={0.58}
            />
          </mesh>
        );
      })}
      {[0, 1, 2].map((i) => (
        <mesh
          key={i}
          position={[Math.cos(i * 2) * 0.5, 0.09, Math.sin(i * 2) * 0.5]}
        >
          <cylinderGeometry args={[0.25, 0.26, 0.05, 22]} />
          <meshStandardMaterial color="#94a44e" roughness={0.45} />
        </mesh>
      ))}
    </group>
  );
}

function IngredientMesh({ ingredient }: { ingredient: Ingredient }) {
  if (ingredient.modelUrl)
    return <ImportedIngredient url={ingredient.modelUrl} />;
  switch (ingredient.kind) {
    case "bun-top":
      return <Bun top />;
    case "bun-bottom":
      return <Bun top={false} />;
    case "patty":
      return <Patty />;
    case "cheese":
      return <Cheese />;
    case "greens":
      return <Greens />;
    case "bacon":
      return <Bacon />;
    default:
      return (
        <mesh scale={[1.01, 0.045, 1.01]}>
          <sphereGeometry args={[1, 40, 12]} />
          <meshStandardMaterial color="#ecc386" roughness={0.4} />
        </mesh>
      );
  }
}

function Bacon() {
  const geometry = useMemo(() => {
    const g = new THREE.PlaneGeometry(2.1, 0.25, 32, 4);
    const p = g.attributes.position;
    for (let i = 0; i < p.count; i++) {
      const x = p.getX(i),
        z = p.getY(i);
      p.setXYZ(i, x, Math.sin(x * 9 + z * 3) * 0.055, z);
    }
    g.computeVertexNormals();
    return g;
  }, []);
  useEffect(() => () => geometry.dispose(), [geometry]);
  return (
    <group>
      {[-0.45, -0.15, 0.15, 0.45].map((z, i) => (
        <mesh
          key={i}
          geometry={geometry}
          position={[0, i * 0.016, z]}
          rotation={[0, i % 2 ? 0.12 : -0.1, 0]}
        >
          <meshStandardMaterial
            color={i % 2 ? "#9c4727" : "#bd7641"}
            side={THREE.DoubleSide}
            roughness={0.45}
          />
        </mesh>
      ))}
    </group>
  );
}

function Layer({
  layer,
  index,
  ingredient,
  ...props
}: { layer: RecipeLayer; index: number; ingredient: Ingredient } & SceneProps) {
  const group = useRef<THREE.Group>(null);
  const [hovered, setHovered] = useState(false);
  useFrame((_, delta) => {
    if (!group.current) return;
    const spread =
      props.spread ??
      (props.interactive
        ? props.selected
          ? 0.62
          : 0.08
        : (props.progress?.current.value ?? 0));
    const chosen = props.selected === ingredient.id;
    group.current.position.y = THREE.MathUtils.damp(
      group.current.position.y,
      layer.y +
        (index - (props.recipe.length - 1) / 2) *
          (props.studio ? 0.34 : 0.42) *
          spread,
      8,
      delta,
    );
    group.current.position.x = THREE.MathUtils.damp(
      group.current.position.x,
      chosen ? 0.45 : 0,
      8,
      delta,
    );
    const scale = hovered || chosen ? 1.04 : 1;
    group.current.scale.lerp(
      new THREE.Vector3(scale, scale, scale),
      Math.min(1, delta * 8),
    );
  });
  return (
    <group
      ref={group}
      position={[0, layer.y, 0]}
      onClick={
        props.interactive
          ? (e) => {
              e.stopPropagation();
              props.onSelect?.(ingredient.id);
            }
          : undefined
      }
      onPointerOver={
        props.interactive
          ? (e) => {
              e.stopPropagation();
              setHovered(true);
            }
          : undefined
      }
      onPointerOut={() => setHovered(false)}
    >
      <group
        scale={layer.scale ?? [1, 1, 1]}
        rotation={layer.rotation ?? [0, 0, 0]}
      >
        <IngredientMesh ingredient={ingredient} />
      </group>
    </group>
  );
}

function SceneContents(props: SceneProps) {
  const root = useRef<THREE.Group>(null);
  const { gl, invalidate, camera } = useThree();
  useEffect(() => {
    props.onReady?.();
  }, [props.onReady]);
  useEffect(() => {
    const fail = (event: Event) => {
      event.preventDefault();
      props.onFailure();
    };
    gl.domElement.addEventListener("webglcontextlost", fail);
    return () => gl.domElement.removeEventListener("webglcontextlost", fail);
  }, [gl, props.onFailure]);
  useFrame(({ clock }, delta) => {
    if (!props.interactive) {
      camera.position.z = THREE.MathUtils.damp(
        camera.position.z,
        8 +
          (props.progress?.current.value ?? 0) * 1.5 +
          Math.max(0, props.recipe.length - 8) * 0.5,
        5,
        delta,
      );
      camera.lookAt(0, 0, 0);
    }
    if (root.current && !props.interactive)
      root.current.rotation.y = THREE.MathUtils.damp(
        root.current.rotation.y,
        -0.22 + Math.sin(clock.elapsedTime * 0.23) * 0.045,
        2,
        delta,
      );
  });
  useEffect(() => {
    invalidate();
  }, [props.selected, invalidate]);
  return (
    <>
      <ambientLight intensity={props.studio ? 0.35 : 1.15} />
      <hemisphereLight
        args={["#fff1d1", "#765233", props.studio ? 0.6 : 1.3]}
      />
      <directionalLight
        position={[3, 6, 5]}
        intensity={props.studio ? 2 : 3.2}
        color="#fff0db"
      />
      <directionalLight
        position={[-4, 2, -2]}
        intensity={props.studio ? 1 : 1.6}
        color="#ffdfac"
      />
      {props.studio && (
        <Environment resolution={256} frames={1}>
          <Lightformer
            intensity={2.5}
            position={[-3, 4, 3]}
            rotation={[0, -Math.PI / 4, 0]}
            scale={[4, 4, 1]}
          />
          <Lightformer
            intensity={1.5}
            position={[3, 2, -3]}
            rotation={[0, Math.PI * 0.75, 0]}
            scale={[3, 3, 1]}
          />
        </Environment>
      )}
      <group ref={root} rotation={[0.08, -0.22, 0]}>
        {props.recipe.map((layer, index) => (
          <Layer
            key={`${layer.ingredientId}-${index}`}
            layer={layer}
            index={index}
            ingredient={props.ingredients.find(
              (i) => i.id === layer.ingredientId,
            )!}
            {...props}
          />
        ))}
      </group>
      {!props.studio && (
        <ContactShadows
          position={[0, -2.8, 0]}
          opacity={0.24}
          scale={7}
          blur={2.5}
          far={5}
          resolution={128}
          frames={1}
        />
      )}
      {props.interactive && (
        <OrbitControls
          enableZoom={!!props.studio}
          enablePan={false}
          minDistance={3.8}
          maxDistance={11}
          minPolarAngle={props.studio ? 0.15 : Math.PI / 3}
          maxPolarAngle={props.studio ? Math.PI * 0.75 : Math.PI / 1.9}
          minAzimuthAngle={props.studio ? -Infinity : -0.65}
          maxAzimuthAngle={props.studio ? Infinity : 0.65}
        />
      )}
    </>
  );
}

export default function BurgerScene(props: SceneProps) {
  const host = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState(true);
  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) =>
      setActive(entry.isIntersecting),
    );
    if (host.current) observer.observe(host.current);
    const change = () => setActive(!document.hidden);
    document.addEventListener("visibilitychange", change);
    return () => {
      observer.disconnect();
      document.removeEventListener("visibilitychange", change);
    };
  }, []);
  return (
    <div ref={host} className="burger-scene" aria-hidden="true">
      <SceneBoundary onFailure={props.onFailure}>
        <Canvas
          fallback={<span>Explora los ingredientes con los botones.</span>}
          camera={{ position: [0, 0.5, props.studio ? 6.6 : 8], fov: 36 }}
          dpr={[1, 1.5]}
          frameloop={active ? "always" : "never"}
          gl={{ antialias: true, alpha: true, powerPreference: "low-power" }}
        >
          <Suspense fallback={null}>
            <SceneContents {...props} />
          </Suspense>
        </Canvas>
      </SceneBoundary>
    </div>
  );
}
