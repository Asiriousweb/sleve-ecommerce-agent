#!/usr/bin/env python3
"""
Persistencia del agente E-commerce — DuckDB sobre el VOLUMEN de Railway.
Mismo enfoque que Sleve-Trade-Marketing (DB analítica liviana en disco).

El volumen se monta en DATA_DIR (configurar en Railway, ej. /data). Local: agent/data/.
Aquí guardamos snapshots de ventas/ads/tráfico para tendencias y para que el brief
no dependa de llamar las APIs en cada consulta.
"""
import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("DATA_DIR", str(Path(__file__).resolve().parent / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "ecommerce.duckdb"


def get_conn():
    """Devuelve una conexión DuckDB al archivo en el volumen. Crea tablas base si faltan."""
    import duckdb
    con = duckdb.connect(str(DB_PATH))
    con.execute("""
        CREATE TABLE IF NOT EXISTS ventas_diarias (
            fecha DATE, pais VARCHAR, canal VARCHAR,
            pedidos INTEGER, ventas_clp DOUBLE, unidades INTEGER
        );
        CREATE TABLE IF NOT EXISTS ads_diarias (
            fecha DATE, pais VARCHAR, plataforma VARCHAR,
            spend DOUBLE, conversiones DOUBLE, valor DOUBLE
        );
    """)
    return con


if __name__ == "__main__":
    c = get_conn()
    print(f"DuckDB OK en {DB_PATH}")
    print(c.execute("SELECT table_name FROM information_schema.tables").fetchall())
