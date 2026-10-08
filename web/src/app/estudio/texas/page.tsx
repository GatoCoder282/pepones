import type { Metadata } from "next";
import TexasStudio from "@/components/texas/TexasStudio";

export const metadata: Metadata = {
  title: "Texas · Estudio 3D",
  description:
    "Modelo 3D de Texas por capas: pan de papa, doble carne, doble queso americano, tocino, cebolla crispy, pepinillos, salsa barbacoa y salsa original.",
  robots: { index: false, follow: false },
};

export default function Page() {
  return <TexasStudio />;
}
