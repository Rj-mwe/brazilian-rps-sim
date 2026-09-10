#!/usr/bin/env python3
"""
Testes Unitários do Adaptador Geoespacial 3D Cesium (rps_br.adapters.cesium).
Verifica a geração de pacotes CZML (documento, 7 satélites, órbitas e estações brasileiras)
e as rotas do visualizador 3D.
"""

import pytest
from fastapi.testclient import TestClient

from rps_br.adapters.api.server import app
from rps_br.adapters.cesium.czml_builder import CzmlConstellationBuilder


@pytest.fixture
def client():
    return TestClient(app)


def test_czml_builder_document_and_packets():
    """Verifica a geração de pacotes CZML para os 7 satélites e estações de solo."""
    builder = CzmlConstellationBuilder()
    packets = builder.generate_czml(epoch_iso="2026-09-09T00:00:00Z", duration_hours=2.0, sample_step_sec=1200.0)

    assert len(packets) > 1
    # 1º pacote deve ser o 'document'
    doc_packet = packets[0]
    assert doc_packet["id"] == "document"
    assert "Brazilian Regional Positioning System" in doc_packet["name"]
    assert "clock" in doc_packet

    # Verifica os pacotes dos satélites (7 satélites)
    sat_packets = [p for p in packets if p.get("id", "").startswith("SAT-")]
    assert len(sat_packets) == 7

    # Verifica presença de GEO e IGSO
    geo_packets = [p for p in sat_packets if "GEO" in p.get("description", "")]
    igso_packets = [p for p in sat_packets if "IGSO" in p.get("description", "")]
    assert len(geo_packets) == 3
    assert len(igso_packets) == 4

    # Cada satélite deve ter trajetória cartesiana WGS84
    for p in sat_packets:
        assert "position" in p
        assert "cartesian" in p["position"]
        assert len(p["position"]["cartesian"]) > 0
        assert "point" in p
        assert "path" in p

    # Verifica os pacotes das estações terrestres brasileiras (pelo menos 7)
    station_packets = [p for p in packets if p.get("id", "").startswith("STA-")]
    assert len(station_packets) >= 7
    assert any("ITA" in p["id"] or "São_José" in p["id"] for p in station_packets)


def test_cesium_routes(client):
    """Verifica se os endpoints de Cesium respondem com sucesso."""
    # 1. Visualizador 3D HTML
    res_viewer = client.get("/cesium/viewer")
    assert res_viewer.status_code == 200
    assert "Cesium.js" in res_viewer.text or "Cesium" in res_viewer.text
    assert "constellation.czml" in res_viewer.text

    # 2. Endpoint CZML
    res_czml = client.get("/cesium/constellation.czml")
    assert res_czml.status_code == 200
    czml_data = res_czml.json()
    assert isinstance(czml_data, list)
    assert len(czml_data) >= 8  # 1 doc + 7 sats + estações
    assert czml_data[0]["id"] == "document"
