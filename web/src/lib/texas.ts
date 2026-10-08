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
