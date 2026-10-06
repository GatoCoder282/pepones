import type { Metadata } from "next";
import DonaStudio from "@/components/DonaStudio";

export const metadata: Metadata = {
  title: "Dona Burger · Estudio 3D · Pepones",
  robots: { index: false, follow: false },
};

export default function Page() {
  return <DonaStudio />;
}
