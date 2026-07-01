import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// "Portero" del dashboard: bloquea el HTML antes de servirlo si no se ingresó el PIN.
// Seguridad real (no se saltea viendo el código fuente). PIN en env DASH_PIN (Vercel).
// Al acertar, deja una cookie httpOnly por 30 días → no vuelve a pedirlo.

const COOKIE = "sleve_dash";
const MAX_AGE = 60 * 60 * 24 * 30; // 30 días

export function middleware(req: NextRequest) {
  const pin = process.env.DASH_PIN;
  if (!pin) return NextResponse.next(); // sin PIN configurado → abierto (cargá DASH_PIN en Vercel)

  // ¿Ya autenticado por cookie?
  if (req.cookies.get(COOKIE)?.value === pin) return NextResponse.next();

  // ¿Trae Basic Auth con el PIN correcto? (el PIN sirve en usuario o contraseña)
  const auth = req.headers.get("authorization") || "";
  if (auth.startsWith("Basic ")) {
    try {
      const [user, pass] = atob(auth.slice(6)).split(":");
      if (user === pin || pass === pin) {
        const res = NextResponse.next();
        res.cookies.set(COOKIE, pin, {
          maxAge: MAX_AGE, httpOnly: true, sameSite: "lax", secure: true, path: "/",
        });
        return res;
      }
    } catch {
      /* header malformado → cae al 401 */
    }
  }

  // Pide credenciales (el navegador muestra el prompt; el PIN va en cualquiera de los dos campos)
  return new NextResponse("🔒 SLEVE E-commerce — acceso restringido. Ingresá el PIN.", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="SLEVE Dashboard", charset="UTF-8"' },
  });
}

// Aplica a todo salvo assets estáticos internos de Next
export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:png|jpg|jpeg|svg|ico|webp)$).*)"],
};
