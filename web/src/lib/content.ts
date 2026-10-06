import data from "@/generated/content.json";

export type IngredientKind =
  "bun-bottom" | "bun-top" | "sauce" | "patty" | "cheese" | "greens";
export interface Ingredient {
  id: string;
  name: string;
  short: string;
  description: string;
  kind: IngredientKind;
  color: string;
  modelUrl?: string;
}
export interface RecipeLayer {
  ingredientId: string;
  y: number;
  scale?: [number, number, number];
  rotation?: [number, number, number];
}
export interface Burger {
  id: string;
  name: string;
  category: string;
  tagline: string;
  description: string;
  price: number | null;
  image: string;
  ingredients: string[];
  recipe: RecipeLayer[];
}
export interface Weekly {
  burgerId: string;
  demo: boolean;
  status: string;
  startsAt: string | null;
  endsAt: string | null;
  accent: string;
}
export interface Restaurant {
  name: string;
  city: string;
  address: string;
  whatsapp: string | null;
  instagram: string;
  mapsUrl: string | null;
  hours: string | null;
}
export interface Content {
  restaurant: Restaurant;
  weekly: Weekly;
  ingredients: Ingredient[];
  burgers: Burger[];
}

export function getContent(): Content {
  return data as Content;
}
export { weeklyAvailability, whatsappLink } from "./availability";
