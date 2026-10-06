import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Pepones — Una semana. Otra obsesión.",
    template: "%s · Pepones",
  },
  description:
    "Hamburguesas con personalidad en Cochabamba. Descubre el universo de las semanales de Pepones, sus ingredientes y su menú.",
  icons: { icon: "/favicon.svg" },
  robots: { index: false, follow: false },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
