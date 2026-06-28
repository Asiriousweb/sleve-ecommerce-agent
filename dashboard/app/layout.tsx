import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SLEVE · E-commerce Global",
  description: "Panel de control e-commerce SLEVE — consolidado multicanal y multi-país",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body className="font-sans">{children}</body>
    </html>
  );
}
