/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Sin `output: export`: Vercel corre el runtime de Next → habilita middleware.ts
  // (el "portero" con PIN protege el HTML antes de servirlo). El dashboard sigue
  // siendo client-side (fetch al robot), pero ahora pasa por el gate de acceso.
  images: { unoptimized: true },
};

export default nextConfig;
