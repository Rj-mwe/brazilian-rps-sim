#!/usr/bin/env python3
"""
Testes Unitários para o Padrão Observer de Notificação de Métricas DOP.
"""

import pytest
from brazilian_rps_sim.core.domain.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO
from brazilian_rps_sim.core.domain.value_objects.DopResultVO import DopResultVO
from brazilian_rps_sim.core.domain.observers.DopSubject import DopSubject
from brazilian_rps_sim.core.domain.observers.DopLoggingObserver import DopLoggingObserver
from brazilian_rps_sim.core.domain.observers.DopAlertThresholdObserver import DopAlertThresholdObserver
from brazilian_rps_sim.core.domain.observers.DopTelemetryBufferObserver import DopTelemetryBufferObserver


def test_dop_subject_attach_detach():
    """Testa o registro e remoção de observadores no DopSubject."""
    subject = DopSubject()
    obs1 = DopLoggingObserver(verbose=False)
    obs2 = DopTelemetryBufferObserver()

    assert subject.observer_count == 0
    subject.attach(obs1)
    subject.attach(obs2)
    assert subject.observer_count == 2

    subject.detach(obs1)
    assert subject.observer_count == 1


def test_dop_alert_threshold_observer_triggers_on_high_pdop():
    """Garante que o observador sentinela dispare alerta quando PDOP > limiar."""
    alerts_received = []

    def handle_alert(msg, dop):
        alerts_received.append((msg, dop))

    sentinel = DopAlertThresholdObserver(max_allowed_pdop=5.0, alert_callback=handle_alert)
    station = GeodeticCoordinatesVO(-15.7975, -47.8633, 1.0)
    
    # 1. DOP Excelente (PDOP = 1.8) -> Não deve gerar alerta
    good_dop = DopResultVO(gdop=2.1, pdop=1.8, hdop=1.1, vdop=1.4, tdop=1.0, visible_satellites_count=5, is_valid=True)
    sentinel.on_dop_calculated("Brasília", station, good_dop, 0.0)
    assert len(sentinel.active_alerts) == 0
    assert len(alerts_received) == 0

    # 2. DOP Degradado (PDOP = 8.5 > 5.0) -> Deve gerar alerta
    bad_dop = DopResultVO(gdop=9.5, pdop=8.5, hdop=4.0, vdop=7.5, tdop=4.2, visible_satellites_count=4, is_valid=True)
    sentinel.on_dop_calculated("Brasília", station, bad_dop, 3600.0)
    assert len(sentinel.active_alerts) == 1
    assert len(alerts_received) == 1
    assert "Geometria degradada" in alerts_received[0][0]


def test_dop_telemetry_buffer_observer_statistics():
    """Testa o acúmulo de série temporal e estatísticas no DopTelemetryBufferObserver."""
    buffer_obs = DopTelemetryBufferObserver()
    station = GeodeticCoordinatesVO(-15.7975, -47.8633, 1.0)

    dop1 = DopResultVO(gdop=2.0, pdop=1.5, hdop=1.0, vdop=1.1, tdop=1.0, visible_satellites_count=6, is_valid=True)
    dop2 = DopResultVO(gdop=3.0, pdop=2.5, hdop=1.5, vdop=2.0, tdop=1.6, visible_satellites_count=5, is_valid=True)

    buffer_obs.on_dop_calculated("Brasília", station, dop1, 0.0)
    buffer_obs.on_dop_calculated("Brasília", station, dop2, 3600.0)

    avg_pdop = buffer_obs.get_average_pdop("Brasília")
    assert pytest.approx(avg_pdop, 0.01) == 2.0 # (1.5 + 2.5) / 2
    assert buffer_obs.get_coverage_availability_percentage("Brasília", max_pdop=3.0) == 100.0
