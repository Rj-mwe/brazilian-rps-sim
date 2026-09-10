#!/usr/bin/env python3
"""
Rotas do Adaptador Cesium 3D: routes
=====================================
Disponibiliza o visualizador fotorrealista WGS84 (/cesium/viewer)
e o endpoint de dados de efemérides em formato oficial CZML (/cesium/constellation.czml).
"""

from pathlib import Path
from typing import Any, Dict, List
from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

from .czml_builder import CzmlConstellationBuilder

router = APIRouter(prefix="/cesium", tags=["Visualização Geoespacial 3D (Cesium / CZML)"])

VIEWER_HTML_PATH = Path(__file__).resolve().parent / "viewer.html"
builder = CzmlConstellationBuilder()


@router.get("/viewer", summary="Visualizador 3D WGS84 em tela cheia (CesiumJS)")
def serve_cesium_viewer():
    """Entrega a Single-Page Application do globo 3D fotorrealista da constelação."""
    if VIEWER_HTML_PATH.exists():
        return FileResponse(str(VIEWER_HTML_PATH))
    return JSONResponse(status_code=404, content={"detail": "Viewer HTML não encontrado"})


@router.get("/constellation.czml", summary="Efemérides no formato oficial Cesium Language (CZML)")
def get_constellation_czml() -> List[Dict[str, Any]]:
    """Gera dinamicamente o fluxo de pacotes CZML da constelação (3 GEO + 4 IGSO + Estações)."""
    return builder.generate_czml()


@router.get("/data", summary="Alias JSON para constellation.czml")
def get_constellation_czml_alias() -> List[Dict[str, Any]]:
    return get_constellation_czml()
