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
];
