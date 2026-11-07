"""Dos pruebas de la herramienta propia episodios_fuera_de_rango, por el cliente MCP y con datos reales."""
import asyncio
import time

import httpx
import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from server import mcp

API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"


def llamar(**args):
    async def correr():
        async with Client(mcp) as c:
            return await c.call_tool("episodios_fuera_de_rango", args)
    return asyncio.run(correr()).data


def control_directo():
    for espera in (3, 6, 12, 24, 0):  # con pedidos seguidos la API responde HTML un rato
        try:
            return httpx.get(f"{API}/PN01273PM/json/2020-1/2024-12", timeout=60, follow_redirects=True).json()
        except ValueError:
            if not espera:
                raise
            time.sleep(espera)


def test_episodios_coinciden_con_la_api_oficial():
    r = llamar(codigo="PN01273PM", desde="2020-01", hasta="2024-12", minimo=1, maximo=3)
    # La cuenta de control va directo a la API del BCRP, sin pasar por el servidor.
    valores = [float(p["values"][0]) for p in control_directo()["periods"]]
    assert r["n_observaciones"] == len(valores) == 60
    assert r["n_sobre"] == sum(v > 3 for v in valores) == 34
    assert r["n_bajo"] == sum(v < 1 for v in valores)
    assert r["n_dentro"] == 60 - r["n_sobre"] - r["n_bajo"]
    assert r["pct_fuera"] == pytest.approx(100 * 34 / 60)
    largo = r["episodio_mas_largo"]
    assert (largo["tipo"], largo["desde"], largo["hasta"], largo["n"]) == ("sobre", "2021-06", "2024-03", 34)
    assert largo["extremo"] == pytest.approx(max(valores))
    assert r["fuente"].startswith("https://estadisticas.bcrp.gob.pe")


def test_episodios_rechaza_rango_invalido_y_codigo_inexistente():
    with pytest.raises(ToolError, match="Rango invalido"):
        llamar(codigo="PN01273PM", desde="2020-01", hasta="2024-12", minimo=3, maximo=1)
    with pytest.raises(ToolError, match="XX999"):
        llamar(codigo="XX999", desde="2020-01", hasta="2024-12", minimo=1, maximo=3)
