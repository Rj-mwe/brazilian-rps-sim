#!/usr/bin/env python3
"""
Testes Unitários do Adaptador CLI (rps-sim / rps_br.adapters.cli).
Valida os comandos de status, matriz de satélites, cálculo de DOP e controle
de execução (pausa, retomada e velocidade) operando diretamente sobre o Core.
"""

import argparse
import pytest

from rps_br.adapters.cli.cli import (
    cmd_status,
    cmd_satellites,
    cmd_dop,
    cmd_pause,
    cmd_resume,
    cmd_speed,
    main,
)
from rps_br.core.application.services.SimulationSessionService import SimulationSessionService


@pytest.fixture(autouse=True)
def reset_session():
    """Garante estado limpo do SimulationSessionService antes e depois de cada teste."""
    session = SimulationSessionService.get_instance()
    session.reset()
    yield session
    session.reset()


def test_cli_status_command(capsys):
    """Valida se o comando 'status' exibe as métricas essenciais da sessão."""
    args = argparse.Namespace()
    cmd_status(args)
    captured = capsys.readouterr()

    assert "Status do Core" in captured.out
    assert "Tempo Virtual:" in captured.out
    assert "Aceleração Temporal:" in captured.out
    assert "Estado de Execução:" in captured.out
    assert "Estação Terrestre:" in captured.out


def test_cli_satellites_command(capsys):
    """Valida se o comando 'satellites' lista os 7 satélites da constelação."""
    args = argparse.Namespace()
    cmd_satellites(args)
    captured = capsys.readouterr()

    assert "Matriz Orbital dos 7 Satélites:" in captured.out
    assert "RPS-GEO-1" in captured.out
    assert "RPS-GEO-2" in captured.out
    assert "RPS-GEO-3" in captured.out
    assert "RPS-IGSO-1" in captured.out
    assert "RPS-IGSO-4" in captured.out
    assert "LOS" in captured.out or "MASC" in captured.out


def test_cli_dop_command(capsys):
    """Valida se o comando 'dop' calcula e imprime métricas para as estações brasileiras."""
    args = argparse.Namespace()
    cmd_dop(args)
    captured = capsys.readouterr()

    assert "Qualidade Geométrica PVT (DOP)" in captured.out
    assert "São José dos Campos (ITA / SP)" in captured.out
    assert "Brasília (DF - Centro)" in captured.out
    assert "Alcântara (CLA / MA)" in captured.out
    assert "GDOP" in captured.out
    assert "PDOP" in captured.out


def test_cli_pause_and_resume_commands(capsys):
    """Valida se os comandos 'pause' e 'resume' alternam o estado no SimulationSessionService."""
    session = SimulationSessionService.get_instance()
    assert not session.get_state().is_paused

    cmd_pause(argparse.Namespace())
    captured = capsys.readouterr()
    assert "pausada" in captured.out.lower()
    assert session.get_state().is_paused

    cmd_resume(argparse.Namespace())
    captured = capsys.readouterr()
    assert "retomada" in captured.out.lower()
    assert not session.get_state().is_paused


def test_cli_speed_command(capsys):
    """Valida se o comando 'speed' ajusta o multiplicador de velocidade no Core."""
    session = SimulationSessionService.get_instance()
    cmd_speed(argparse.Namespace(multiplier=50.0))
    captured = capsys.readouterr()

    assert "50.0x" in captured.out
    assert session.get_state().time_multiplier == 50.0


def test_cli_main_entrypoint(monkeypatch, capsys):
    """Valida o despachante principal (main) via argumentos de linha de comando."""
    monkeypatch.setattr("sys.argv", ["rps-sim", "status"])
    main()
    captured = capsys.readouterr()
    assert "Status do Core" in captured.out
