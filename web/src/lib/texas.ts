import manifest from "@/generated/texas.json";

export type TexasIngredientId =
  | "pan-de-papa"
  | "carne"
  | "queso-americano"
  | "tocino"
  | "cebolla-crispy"
  | "pepinillos"
  | "salsa-barbacoa"
  | "salsa-original";

export interface TexasIngredient {
  id: TexasIngredientId;
  name: string;
  /** Quantity stated in the confirmed recipe, when there is one. */
  quantity?: string;
  color: string;
  description: string;
  /** Present when the placement or the modelled amount is a visual estimate. */
  estimate?: string;
  /** Labels for ingredients that appear in more than one layer. */
  parts?: Record<string, string>;
}

export interface TexasLayer {
  index: number;
  assetId: string;
  ingredientId: TexasIngredientId;
  y: number;
  rotation: [number, number, number];
  url: string;
  label: string;
}

// Order and names follow the confirmed ingredient list; descriptions only restate it
// and what the reference photo shows.
export const TEXAS_INGREDIENTS: TexasIngredient[] = [
  {
    id: "pan-de-papa",
    name: "Pan de papa",
    quantity: "Base y tapa",
    color: "#dd962d",
    description:
      "Va en dos piezas: la base sostiene las capas y la tapa cierra la hamburguesa.",
    parts: { "pan-base": "base", "pan-tapa": "tapa" },
  },
  {
    id: "carne",
    name: "Doble carne",
    quantity: "×2",
    color: "#7a4a31",
    description: "Dos carnes, cada una representada como una capa independiente.",
  },
  {
    id: "queso-americano",
    name: "Doble queso americano",
    quantity: "×2",
    color: "#f2b11a",
    description:
      "Dos láminas de queso americano. En la foto se ve una sobre cada carne.",
  },
  {
    id: "tocino",
    name: "Tocino",
    color: "#a8432f",
    description: "Tiras de tocino sobre la carne superior.",
    estimate: "La cantidad de tiras del modelo es ilustrativa.",
  },
  {
    id: "cebolla-crispy",
    name: "Cebolla crispy",
    color: "#dcb36e",
    description: "Cebolla crispy sobre el tocino, debajo de la tapa.",
    estimate: "La cantidad del modelo es ilustrativa.",
  },
  {
    id: "pepinillos",
    name: "Pepinillos",
    color: "#868033",
    description: "Pepinillos entre la base y la primera carne.",
    estimate: "La cantidad de rodajas del modelo es ilustrativa.",
  },
  {
    id: "salsa-barbacoa",
    name: "Salsa barbacoa",
    color: "#7e2d1e",
    description: "Salsa barbacoa sobre el tocino.",
    estimate: "Ubicación estimada a partir de la foto.",
  },
  {
    id: "salsa-original",
    name: "Salsa original",
    color: "#e6a064",
    description: "Salsa original sobre la base y debajo de la tapa.",
    estimate: "Ubicación estimada a partir de la foto.",
    parts: { "salsa-original-base": "base", "salsa-original-tapa": "tapa" },
  },
];

export const TEXAS_SIDE = {
  id: "papas-cajun",
  name: "Papas Cajun",
  description: "Se muestra aparte, fuera de las capas de la hamburguesa.",
  estimate: "La forma y la cantidad del modelo son ilustrativas.",
  url: manifest.assets.find((a) => a.id === manifest.side.assetId)!.modelUrl,
  position: manifest.side.position as [number, number, number],
  rotation: manifest.side.rotation as [number, number, number],
};

const byId = new Map(TEXAS_INGREDIENTS.map((i) => [i.id, i]));
export const ingredientById = (id: TexasIngredientId) => byId.get(id)!;
export const ingredientNumber = (id: TexasIngredientId) =>
  TEXAS_INGREDIENTS.findIndex((i) => i.id === id) + 1;

export const TEXAS_LAYERS: TexasLayer[] = manifest.recipe.map((layer, index) => {
  const ingredient = ingredientById(layer.ingredientId as TexasIngredientId);
  const part = ingredient.parts?.[layer.assetId];
  return {
    index,
    assetId: layer.assetId,
    ingredientId: ingredient.id,
    y: layer.y,
    rotation: layer.rotation as [number, number, number],
    url: manifest.assets.find((a) => a.id === layer.assetId)!.modelUrl,
    label: part ? `${ingredient.name} · ${part}` : ingredient.name,
  };
});

/** 1-based layer positions, counted from the bottom bun. */
export const layersOf = (id: TexasIngredientId) =>
  TEXAS_LAYERS.filter((l) => l.ingredientId === id).map((l) => l.index + 1);
