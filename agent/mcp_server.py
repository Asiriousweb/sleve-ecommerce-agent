#!/usr/bin/env python3
"""
MCP server READ-ONLY del agente E-commerce — para que otros agentes SLEVE (ej. el
orquestador Comercial / Trade) consulten su estado y sus briefs. Mismo rol que el
mcp_server.py de Sleve-Trade-Marketing.

Gateado a propósito: solo arranca si MCP_ENABLED está seteado (liga al puerto público).
Protegerlo con bearer token (MCP_BEARER_TOKEN) + Cloudflare Access delante.
Transport: streamable HTTP (FastMCP + uvicorn).
"""
import os

# Solo expone LECTURA (briefs/estado). Nunca acciones que muevan dinero/datos.
try:
    from mcp.server.fastmcp import FastMCP
    _HAS_MCP = True
except Exception:  # noqa: BLE001
    _HAS_MCP = False


def _build():
    import orchestrator
    mcp = FastMCP("sleve-ecommerce")

    @mcp.tool()
    def estado() -> str:
        """Estado del sistema E-commerce (qué fuentes están conectadas)."""
        return orchestrator.estado()

    @mcp.tool()
    def brief() -> str:
        """Brief consolidado E-commerce (todos los dominios)."""
        return orchestrator.build_daily_brief()

    @mcp.tool()
    def especialista(nombre: str) -> str:
        """Detalle de un especialista: ads, marketplaces, organico, cro, social, retencion."""
        return orchestrator.specialist_brief(nombre)

    return mcp


def main():
    if not os.environ.get("MCP_ENABLED"):
        print("[mcp] MCP_ENABLED no seteado → no arranco (gateado).", flush=True)
        return
    if not _HAS_MCP:
        print("[mcp] paquete 'mcp' no disponible → no arranco.", flush=True)
        return
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    mcp = _build()
    print("[mcp] arrancando MCP server (streamable-http)…", flush=True)
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
