/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Export estático: el build produce HTML plano en dashboard/out → Vercel lo sirve
  // como sitio estático (sin runtime), evitando cualquier detección de framework rara.
  output: "export",
  images: { unoptimized: true },
};

export default nextConfig;
