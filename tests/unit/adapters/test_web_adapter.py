#!/usr/bin/env python3
"""
Testes Unitários do Adaptador Web (FastAPI, TelemetryHub e REST API).
Garante que a interface web e a API de telemetria operam estritamente
em conformidade com o domínio astrodinâmico e PVT.
"""

import pytest
from fastapi.testclient import TestClient

from rps_br.adapters.web.server import app
from rps_br.adapters.web.telemetry_hub import TelemetryHub


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def hub():
    return TelemetryHub.get_instance()


def test_telemetry_hub_initial_snapshot(hub):
    """Verifica se o snapshot inicial do TelemetryHub contém os 7 satélites e métricas DOP."""
    snapshot = hub.get_snapshot()
    assert "simulation" in snapshot
    assert "dop" in snapshot
    assert "satellites" in snapshot
    assert len(snapshot["satellites"]) == 7

    # Verifica os 3 GEOs e 4 IGSOs
    geo_count = sum(1 for s in snapshot["satellites"] if s["type"] == "GEO")
    igso_count = sum(1 for s in snapshot["satellites"] if s["type"] == "IGSO")
    assert geo_count == 3
    assert igso_count == 4


def test_telemetry_hub_step_propagation(hub):
    """Verifica se o avanço do tempo (step) propaga a simulação e calcula o retardo troposférico."""
    hub.set_paused(False)
    initial_time = hub.sim_time_sec
    hub.step(1.0)
    assert hub.sim_time_sec > initial_time

    snapshot = hub.get_snapshot()
    for sat in snapshot["satellites"]:
        if sat["in_view"]:
            assert sat["tropo_m"] > 1.0  # Retardo troposférico típico > 1 metro
            assert sat["tropo_ns"] > 3.0


def test_api_status_endpoint(client):
    """Verifica se o endpoint GET /api/status retorna o estado online."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["active_satellites_count"] == 7


def test_api_satellites_endpoints(client):
    """Verifica a listagem dos 7 satélites e busca por ID."""
    # Listagem completa
    res_list = client.get("/api/satellites")
    assert res_list.status_code == 200
    sats = res_list.json()
    assert len(sats) == 7

    # Busca específica PRN 1
    res_sat1 = client.get("/api/satellites/1")
    assert res_sat1.status_code == 200
    sat1 = res_sat1.json()
    assert sat1["id"] == 1
    assert "RPS-GEO-1" in sat1["name"]

    # Busca de PRN inexistente
    res_err = client.get("/api/satellites/99")
    assert res_err.status_code == 404


def test_api_dop_and_stations_endpoint(client):
    """Verifica os endpoints de PVT/DOP e estações disponíveis."""
    res_dop = client.get("/api/dop")
    assert res_dop.status_code == 200
    data_dop = res_dop.json()
    assert "station" in data_dop
    assert "pdop" in data_dop["dop"]
    assert "gdop" in data_dop["dop"]

    res_stations = client.get("/api/stations")
    assert res_stations.status_code == 200
    stations = res_stations.json()
    assert "São José dos Campos (ITA / SP)" in stations
    assert "Brasília (DF - Centro)" in stations


def test_api_atmospheric_delays_endpoint(client):
    """Verifica se o endpoint de atrasos atmosféricos expõe o modelo de Saastamoinen."""
    response = client.get("/api/delays")
    assert response.status_code == 200
    data = response.json()
    assert "Saastamoinen" in data["model_troposphere"]
    assert "delays_by_satellite" in data
    assert len(data["delays_by_satellite"]) == 7


def test_api_control_endpoints(client):
    """Verifica os comandos interativos de controle da simulação."""
    # Pausar
    res_pause = client.post("/api/control/pause", json={"paused": True})
    assert res_pause.status_code == 200
    assert res_pause.json()["paused"] is True

    # Multiplicador
    res_mult = client.post("/api/control/multiplier", json={"multiplier": 60.0})
    assert res_mult.status_code == 200
    assert res_mult.json()["multiplier"] == 60.0

    # Máscara de Elevação
    res_mask = client.post("/api/control/mask", json={"elevation_mask_deg": 15.0})
    assert res_mask.status_code == 200
    assert res_mask.json()["elevation_mask_deg"] == 15.0

    # Troca de Estação
    res_sta = client.post("/api/control/station", json={"station_name": "Brasília (DF - Centro)"})
    assert res_sta.status_code == 200
    assert res_sta.json()["station"] == "Brasília (DF - Centro)"

    # Troca de Estação Inválida
    res_sta_err = client.post("/api/control/station", json={"station_name": "Estação Inexistente"})
    assert res_sta_err.status_code == 404


def test_frontend_index_serving(client):
    """Verifica se a página HTML do painel é servida com sucesso na raiz."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "RPS-BR" in response.text
