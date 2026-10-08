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
];
