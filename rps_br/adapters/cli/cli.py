#!/usr/bin/env python3
"""
Adaptador CLI: rps_sim_cli
==========================
Interface de Linha de Comando (CLI) para controle e inspeção autônoma da simulação
do RPS-BR. Opera de forma 100% independente do Gazebo e do ROS 2, comunicando-se
diretamente com o Core do domínio ou com o servidor de telemetria ativo.
"""

import argparse
import json
import sys
import time
import urllib.request
import urllib.error
from typing import Any, Dict, Optional

from rps_br.infrastructure.config.config_loader import load_simulation_config, find_config_file
from rps_br.core.domain.astrodynamics.aggregates.ConstellationAggregate import ConstellationAggregate
from rps_br.core.domain.astrodynamics.services.CoordinateTransformService import CoordinateTransformService
from rps_br.core.application.services.CalculateGroundStationDopUseCase import (
    CalculateGroundStationDopUseCase,
    DEFAULT_BRAZILIAN_GROUND_STATIONS,
)
from rps_br.core.domain.navigation_pvt.strategies.ElevationMaskDopStrategy import ElevationMaskDopStrategy
from rps_br.core.domain.signal_propagation.services.TroposphereSaastamoinenService import TroposphereSaastamoinenService
from rps_br.core.domain.signal_propagation.value_objects.TroposphericWeatherVO import TroposphericWeatherVO
from rps_br.core.application.services.SimulationSessionService import SimulationSessionService
from rps_br.core.application.dtos.SimulationDTOs import (
    SimulationClockTickDTO,
    PauseSimulationRequestDTO,
    SetTimeMultiplierRequestDTO,
)


API_BASE_URL = "http://127.0.0.1:8000"


def _fetch_api(path: str, method: str = "GET", data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Tenta consultar a API REST local ativa do Web Dashboard."""
    url = f"{API_BASE_URL}{path}"
    try:
        req_data = json.dumps(data).encode("utf-8") if data else None
        headers = {"Content-Type": "application/json"} if data else {}
        req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=0.8) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def cmd_status(args):
    """Exibe o status consolidado da simulação e da constelação."""
    api_data = _fetch_api("/api/status")
    if api_data:
        sim = api_data.get("simulation", {})
        dop = api_data.get("dop", {})
        print("\n🛰️  SPR-BR / RPS-BR - Status da Simulação (Fonte: Web/Core Ativo)")
        print("=" * 65)
        print(f"  Modo Operacional:      {sim.get('mode', 'STANDALONE')}")
        print(f"  Tempo Virtual:         {sim.get('time_str', '00:00:00')} ({sim.get('time_sec', 0.0):.1f} s)")
        print(f"  Aceleração Temporal:   {sim.get('multiplier', 1.0)}x")
        print(f"  Estado de Execução:    {'⏸️ PAUSADO' if sim.get('is_paused') else '🟢 EM ANDAMENTO'}")
        print(f"  Estação Terrestre:     {sim.get('station_name', 'ITA')}")
        print(f"  Máscara de Elevação:   {sim.get('elevation_mask_deg', 5.0)}°")
        print(f"  Satélites em Visada:   {dop.get('visible_count', 0)} / 7")
        print(f"  Qualidade PVT (PDOP):  {dop.get('pdop', 99.9)} ({dop.get('status', 'N/A')})")
        print(f"  GDOP / HDOP / VDOP:    {dop.get('gdop', 99.9)} / {dop.get('hdop', 99.9)} / {dop.get('vdop', 99.9)}")
        print("=" * 65 + "\n")
        return

    # Fallback: Consulta direta ao Core
    session = SimulationSessionService.get_instance()
    state = session.get_state()
    hours = state.sim_time_sec / 3600.0
    time_str = f"{int(hours):02d}:{int((state.sim_time_sec % 3600) / 60):02d}:{int(state.sim_time_sec % 60):02d}"
    print("\n🛰️  SPR-BR / RPS-BR - Status do Core (Modo Autônomo Local)")
    print("=" * 65)
    print(f"  Modo Operacional:      {state.mode}")
    print(f"  Tempo Virtual:         {time_str} ({state.sim_time_sec:.1f} s)")
    print(f"  Aceleração Temporal:   {state.time_multiplier}x")
    print(f"  Estado de Execução:    {'⏸️ PAUSADO' if state.is_paused else '🟢 EM ANDAMENTO'}")
    print(f"  Estação Terrestre:     {state.selected_station_name}")
    print(f"  Máscara de Elevação:   {state.elevation_mask_deg}°")
    print("=" * 65 + "\n")


def cmd_satellites(args):
    """Lista as efemérides e visibilidade dos 7 satélites."""
    api_data = _fetch_api("/api/satellites")
    if api_data:
        sats = api_data
    else:
        # Computa diretamente do Core
        cfg = load_simulation_config(find_config_file())
        constellation = ConstellationAggregate.from_config(cfg)
        coord_service = CoordinateTransformService()
        session = SimulationSessionService.get_instance()
        state = session.get_state()
        constellation.propagate_all(state.sim_time_sec)

        station_vo = DEFAULT_BRAZILIAN_GROUND_STATIONS.get(
            state.selected_station_name,
            DEFAULT_BRAZILIAN_GROUND_STATIONS["São José dos Campos (ITA / SP)"]
        )
        sats = []
        for s in constellation.satellites:
            el, az, dist = coord_service.compute_topocentric_look_angles(
                s.r_ecef.to_numpy(), station_vo.latitude_deg, station_vo.longitude_deg
            )
            sats.append({
                "id": s.sat_id,
                "name": s.name,
                "type": s.sat_type,
                "lat": round(s.geodetic.latitude_deg, 2),
                "lon": round(s.geodetic.longitude_deg, 2),
                "alt_km": round(s.geodetic.altitude_km, 1),
                "azimuth_deg": round(az, 1),
                "elevation_deg": round(el, 1),
                "in_view": el >= state.elevation_mask_deg,
            })

    print(f"\n📡 Matriz Orbital dos 7 Satélites:")
    print("-" * 80)
    print(f"{'PRN':<4} {'Nome':<28} {'Tipo':<6} {'Lat (°)':<9} {'Lon (°)':<9} {'Alt (km)':<10} {'Az (°)':<8} {'El (°)':<8} {'Visada'}")
    print("-" * 80)
    for s in sats:
        vis = "✅ LOS" if s.get("in_view") else "❌ MASC"
        print(f"{s['id']:<4} {s['name']:<28} {s['type']:<6} {s['lat']:<9.2f} {s['lon']:<9.2f} {s['alt_km']:<10.1f} {s['azimuth_deg']:<8.1f} {s['elevation_deg']:<8.1f} {vis}")
    print("-" * 80 + "\n")


def cmd_dop(args):
    """Calcula e exibe a matriz de DOP para as principais capitais brasileiras."""
    cfg = load_simulation_config(find_config_file())
    constellation = ConstellationAggregate.from_config(cfg)
    session = SimulationSessionService.get_instance()
    state = session.get_state()
    constellation.propagate_all(state.sim_time_sec)
    sats_ecef = {sat.name: sat.r_ecef.to_numpy() for sat in constellation.satellites}

    dop_uc = CalculateGroundStationDopUseCase(
        strategy=ElevationMaskDopStrategy(mask_angle_deg=state.elevation_mask_deg),
        ground_stations=DEFAULT_BRAZILIAN_GROUND_STATIONS
    )
    dop_results = dop_uc.execute(sats_ecef, state.sim_time_sec)

    print(f"\n🎯 Qualidade Geométrica PVT (DOP) nas Estações Terrestres Brasileiras:")
    print(f"   (Tempo Virtual: {state.sim_time_sec:.1f}s | Máscara: {state.elevation_mask_deg}°)")
    print("-" * 75)
    print(f"{'Estação Terrestre':<32} {'Vis':<5} {'GDOP':<8} {'PDOP':<8} {'HDOP':<8} {'VDOP':<8}")
    print("-" * 75)
    for name, res in dop_results.items():
        pdop_str = f"{res.pdop:.2f}" if res.is_valid else "N/A"
        gdop_str = f"{res.gdop:.2f}" if res.is_valid else "N/A"
        hdop_str = f"{res.hdop:.2f}" if res.is_valid else "N/A"
        vdop_str = f"{res.vdop:.2f}" if res.is_valid else "N/A"
        print(f"{name:<32} {res.visible_satellites_count:<5} {gdop_str:<8} {pdop_str:<8} {hdop_str:<8} {vdop_str:<8}")
    print("-" * 75 + "\n")


def cmd_pause(args):
    """Pausa a simulação."""
    res = _fetch_api("/api/control/pause", method="POST", data={"paused": True})
    if res:
        print("⏸️  Simulação pausada com sucesso via Web API.")
    else:
        session = SimulationSessionService.get_instance()
        session.pause(PauseSimulationRequestDTO(paused=True))
        print("⏸️  Simulação pausada no Core local.")


def cmd_resume(args):
    """Retoma a simulação."""
    res = _fetch_api("/api/control/pause", method="POST", data={"paused": False})
    if res:
        print("▶️  Simulação retomada com sucesso via Web API.")
    else:
        session = SimulationSessionService.get_instance()
        session.pause(PauseSimulationRequestDTO(paused=False))
        print("▶️  Simulação retomada no Core local.")


def cmd_speed(args):
    """Ajusta o multiplicador de velocidade da simulação."""
    res = _fetch_api("/api/control/multiplier", method="POST", data={"multiplier": args.multiplier})
    if res:
        print(f"⚡ Aceleração ajustada para {args.multiplier}x via Web API.")
    else:
        session = SimulationSessionService.get_instance()
        session.set_time_multiplier(SetTimeMultiplierRequestDTO(multiplier=args.multiplier))
        print(f"⚡ Aceleração ajustada para {args.multiplier}x no Core local.")


def cmd_run(args):
    """Executa a simulação autônoma em loop no terminal com streaming textual a 1 Hz."""
    print(f"\n🚀 Iniciando Motor de Simulação Autônomo do RPS-BR (Multiplicador: {args.speed}x)")
    print("   Pressione Ctrl+C para encerrar.\n")
    session = SimulationSessionService.get_instance(initial_multiplier=args.speed)
    session.pause(PauseSimulationRequestDTO(paused=False))
    
    cfg = load_simulation_config(find_config_file())
    constellation = ConstellationAggregate.from_config(cfg)
    dop_uc = CalculateGroundStationDopUseCase(
        strategy=ElevationMaskDopStrategy(mask_angle_deg=session.get_state().elevation_mask_deg)
    )

    last_time = time.time()
    try:
        while True:
            time.sleep(1.0)
            now = time.time()
            dt = now - last_time
            last_time = now

            session.advance_standalone_clock(dt)
            state = session.get_state()
            constellation.propagate_all(state.sim_time_sec)

            sats_ecef = {sat.name: sat.r_ecef.to_numpy() for sat in constellation.satellites}
            dops = dop_uc.execute(sats_ecef, state.sim_time_sec)
            ita_dop = dops.get("São José dos Campos (ITA / SP)")

            hours = state.sim_time_sec / 3600.0
            time_str = f"{int(hours):02d}:{int((state.sim_time_sec % 3600) / 60):02d}:{int(state.sim_time_sec % 60):02d}"
            pdop_val = f"{ita_dop.pdop:.2f}" if ita_dop and ita_dop.is_valid else "--"
            vis_count = ita_dop.visible_satellites_count if ita_dop else 0

            print(f"\r⏱️  [{time_str}] | Vel: {state.time_multiplier:.0f}x | ITA Visíveis: {vis_count}/7 | PDOP: {pdop_val}   ", end="", flush=True)
    except KeyboardInterrupt:
        print("\n\n⏹️  Simulação autônoma finalizada.")


def main():
    parser = argparse.ArgumentParser(
        prog="rps-sim",
        description="🛰️ RPS-BR CLI: Controle e Monitoramento Autônomo da Constelação Regional Brasileira"
    )
    subparsers = parser.add_subparsers(dest="command", help="Comando a ser executado")

    # status
    subparsers.add_parser("status", help="Exibe o status consolidado da simulação e métricas")
    # satellites
    subparsers.add_parser("satellites", help="Lista efemérides e visibilidade dos 7 satélites")
    # dop
    subparsers.add_parser("dop", help="Exibe a matriz de DOP nas 7 estações terrestres brasileiras")
    # pause
    subparsers.add_parser("pause", help="Pausa a simulação")
    # resume
    subparsers.add_parser("resume", help="Retoma a simulação")
    # speed
    speed_p = subparsers.add_parser("speed", help="Ajusta o fator de aceleração temporal")
    speed_p.add_argument("multiplier", type=float, help="Multiplicador de tempo (ex: 1.0, 10.0, 60.0, 3600.0)")
    # run
    run_p = subparsers.add_parser("run", help="Executa o motor de simulação autônomo no terminal")
    run_p.add_argument("--speed", type=float, default=60.0, help="Velocidade de aceleração temporal (padrão: 60x)")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "status": cmd_status,
        "satellites": cmd_satellites,
        "dop": cmd_dop,
        "pause": cmd_pause,
        "resume": cmd_resume,
        "speed": cmd_speed,
        "run": cmd_run,
    }
    handler = dispatch.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
