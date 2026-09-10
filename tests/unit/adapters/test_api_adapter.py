#!/usr/bin/env python3
"""
Testes Unitários do Adaptador de API Gateway (rps_br.adapters.api).
Valida as rotas RESTful, gerador de sentenças NMEA 0183 ($GNGGA, $GNGSA, $GPGSV),
cálculo de checksum XOR e sincronização com o domínio.
"""

import pytest
from fastapi.testclient import TestClient

from rps_br.adapters.api.server import app
from rps_br.adapters.api.telemetry_hub import TelemetryHub
from rps_br.adapters.api.nmea.nmea_streamer import compute_nmea_checksum, format_lat_lon_nmea


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def hub():
    return TelemetryHub.get_instance()


def test_api_gateway_status_endpoint(client):
    """Verifica se o endpoint principal /api/status responde corretamente."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["active_satellites_count"] == 7


def test_api_satellites_list_and_details(client):
    """Verifica a listagem de todos os satélites e busca de satélite específico."""
    res_list = client.get("/api/satellites")
    assert res_list.status_code == 200
    sats = res_list.json()
    assert len(sats) == 7

    sat_id = sats[0]["id"]
    res_detail = client.get(f"/api/satellites/{sat_id}")
    assert res_detail.status_code == 200
    assert res_detail.json()["id"] == sat_id


def test_api_dop_and_ground_stations(client):
    """Verifica consulta de DOP e listagem das estações de solo brasileiras."""
    res_dop = client.get("/api/dop")
    assert res_dop.status_code == 200
    dop = res_dop.json()
    assert "dop" in dop
    assert "gdop" in dop["dop"]
    assert "pdop" in dop["dop"]
    assert "hdop" in dop["dop"]
    assert "vdop" in dop["dop"]

    res_sta = client.get("/api/stations")
    assert res_sta.status_code == 200
    stations = res_sta.json()
    assert len(stations) >= 7
    assert any("ITA" in s for s in stations)


def test_api_simulation_control(client, hub):
    """Verifica os comandos interativos de pause, velocidade e máscara de elevação."""
    # Pausar simulação
    res_pause = client.post("/api/control/pause", json={"paused": True})
    assert res_pause.status_code == 200
    assert hub.is_paused is True

    # Despausar simulação
    res_unpause = client.post("/api/control/pause", json={"paused": False})
    assert res_unpause.status_code == 200
    assert hub.is_paused is False

    # Definir velocidade
    res_speed = client.post("/api/control/speed", json={"multiplier": 5.0})
    assert res_speed.status_code == 200
    assert hub.time_multiplier == 5.0

    # Definir máscara de elevação
    res_mask = client.post("/api/control/mask", json={"mask_deg": 10.0})
    assert res_mask.status_code == 200
    assert hub.elevation_mask_deg == 10.0


def test_nmea_checksum_calculation():
    """Valida o cálculo do checksum XOR hexadecimal padrão NMEA 0183."""
    test_body = "GNGGA,000000.00,2312.7680,S,04552.5300,W,1,07,1.20,600.0,M,0.0,M,,"
    checksum = compute_nmea_checksum(test_body)
    assert len(checksum) == 2
    assert all(c in "0123456789ABCDEF" for c in checksum)


def test_nmea_lat_lon_formatting():
    """Valida a conversão de coordenadas decimais para notação NMEA (ddmm.mmmm)."""
    lat_str, lat_dir, lon_str, lon_dir = format_lat_lon_nmea(-23.2128, -45.8755)
    assert lat_dir == "S"
    assert lon_dir == "W"
    assert lat_str.startswith("23")
    assert lon_str.startswith("045")


def test_nmea_sentences_generation(client, hub):
    """Verifica se os endpoints NMEA geram as sentenças $GNGGA, $GNGSA e $GPGSV válidas."""
    res = client.get("/api/nmea/sentences")
    assert res.status_code == 200
    sentences = res.json()
    assert len(sentences) >= 3

    assert any(s.startswith("$GNGGA") for s in sentences)
    assert any(s.startswith("$GNGSA") for s in sentences)
    assert any(s.startswith("$GPGSV") for s in sentences)

    for s in sentences:
        assert s.startswith("$")
        assert "*" in s
        parts = s[1:].split("*")
        content = parts[0]
        csum = parts[1]
        assert compute_nmea_checksum(content) == csum


def test_nmea_raw_stream(client):
    """Verifica se o endpoint /api/nmea/raw retorna texto puro com quebras CRLF."""
    res = client.get("/api/nmea/raw")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/plain")
    text = res.text
    assert "\r\n" in text
    assert "$GNGGA" in text


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
            assert sat["tropo_m"] > 1.0
            assert sat["tropo_ns"] > 3.0


def test_api_atmospheric_delays_endpoint(client):
    """Verifica se o endpoint de atrasos atmosféricos expõe o modelo de Saastamoinen."""
    response = client.get("/api/delays")
    assert response.status_code == 200
    data = response.json()
    assert "Saastamoinen" in data["model_troposphere"]
    assert "delays_by_satellite" in data
    assert len(data["delays_by_satellite"]) == 7


def test_frontend_index_serving(client):
    """Verifica se a página HTML do painel é servida com sucesso na raiz."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "RPS-BR" in response.text


def test_internal_clock_synchronization(client, hub):
    """Verifica se o endpoint POST /api/internal/clock sincroniza o tempo Master do Gazebo."""
    res_tick = client.post("/api/internal/clock", json={"sim_time": 1234.5, "is_paused": True})
    assert res_tick.status_code == 200
    data = res_tick.json()
    assert data["status"] == "synchronized"
    assert data["sim_time"] == 1234.5
    assert data["is_paused"] is True
    assert data["mode"] == "MASTER_GAZEBO"

    # Confirma que o snapshot do Hub reflete o relógio Master
    snapshot = hub.get_snapshot()
    assert snapshot["simulation"]["time_sec"] == 1234.5
    assert snapshot["simulation"]["is_paused"] is True
    assert snapshot["simulation"]["mode"] == "MASTER_GAZEBO"


def test_simulation_session_service_hexagonal_port():
    """Verifica o padrão Hexagonal: SimulationSessionService notificando portas externas."""
    from rps_br.core.application.services.SimulationSessionService import SimulationSessionService
    from rps_br.core.domain.interfaces.ISimulationControlOutboundPort import ISimulationControlOutboundPort
    from rps_br.core.application.dtos.SimulationDTOs import PauseSimulationRequestDTO

    class MockControlPort(ISimulationControlOutboundPort):
        def __init__(self):
            self.paused = False
            self.stepped = False

        def pause_simulation(self) -> bool:
            self.paused = True
            return True

        def resume_simulation(self) -> bool:
            self.paused = False
            return True

        def step_simulation(self, steps: int = 1) -> bool:
            self.stepped = True
            return True

        def set_simulation_rate(self, multiplier: float) -> bool:
            return True

    service = SimulationSessionService.get_instance()
    mock_port = MockControlPort()
    service.register_control_outbound_port(mock_port)

    # Pausar
    service.pause(PauseSimulationRequestDTO(paused=True))
    assert mock_port.paused is True

    # Retomar
    service.pause(PauseSimulationRequestDTO(paused=False))
    assert mock_port.paused is False

    service.unregister_control_outbound_port(mock_port)

