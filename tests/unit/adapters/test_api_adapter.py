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
