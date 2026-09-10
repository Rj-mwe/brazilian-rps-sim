#!/usr/bin/env python3
"""
Adaptador NMEA 0183: nmea_streamer
==================================
Converte a telemetria, posições e métricas de DOP da constelação RPS-BR
no protocolo padrão NMEA 0183 ($GNGGA, $GNGSA, $GPGSV), permitindo integração
direta com receptores de navegação comerciais (ex: u-blox u-center).
"""

import math
import time
from typing import Any, Dict, List
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from rps_br.adapters.api.telemetry_hub import TelemetryHub

router = APIRouter(prefix="/api/nmea", tags=["Navegação NMEA 0183"])


def compute_nmea_checksum(sentence_content: str) -> str:
    """Calcula o checksum XOR hexadecimal de dois dígitos da sentença NMEA (entre $ e *)."""
    csum = 0
    for char in sentence_content:
        csum ^= ord(char)
    return f"{csum:02X}"


def format_lat_lon_nmea(lat_deg: float, lon_deg: float):
    """Converte coordenadas decimais em formato NMEA (ddmm.mmmmm, N/S e dddmm.mmmmm, E/W)."""
    lat_abs = abs(lat_deg)
    lat_d = int(lat_abs)
    lat_m = (lat_abs - lat_d) * 60.0
    lat_dir = "N" if lat_deg >= 0 else "S"
    lat_str = f"{lat_d:02d}{lat_m:07.4f}"

    lon_abs = abs(lon_deg)
    lon_d = int(lon_abs)
    lon_m = (lon_abs - lon_d) * 60.0
    lon_dir = "E" if lon_deg >= 0 else "W"
    lon_str = f"{lon_d:03d}{lon_m:07.4f}"

    return lat_str, lat_dir, lon_str, lon_dir


class NmeaSentenceFormatter:
    """Formata os tensores analíticos da simulação em sentenças oficiais NMEA 0183."""

    @staticmethod
    def format_all(snapshot: Dict[str, Any]) -> List[str]:
        sentences = []
        sim_state = snapshot.get("simulation", {})
        dop_state = snapshot.get("dop", {})
        sats = snapshot.get("satellites", [])

        # Tempo UTC formatado (hhmmss.ss)
        t_sec = sim_state.get("time_sec", 0.0)
        h = int((t_sec / 3600.0) % 24)
        m = int((t_sec % 3600) / 60)
        s = t_sec % 60
        utc_str = f"{h:02d}{m:02d}{s:05.2f}"

        # Coordenadas da estação de solo
        lat = sim_state.get("station_lat", -23.2128)
        lon = sim_state.get("station_lon", -45.8755)
        alt = sim_state.get("station_alt_km", 0.6) * 1000.0  # metros
        lat_str, lat_dir, lon_str, lon_dir = format_lat_lon_nmea(lat, lon)

        vis_sats = [sat for sat in sats if sat.get("in_view")]
        vis_count = len(vis_sats)

        # 1. $GNGGA: Fix Data
        # Formato: $GNGGA,time,lat,NS,lon,EW,quality,numSV,HDOP,alt,M,sep,M,diffAge,diffRef
        hdop = dop_state.get("hdop", 1.0)
        quality = 1 if vis_count >= 4 else 0  # 1 = GPS Fix
        gga_body = f"GNGGA,{utc_str},{lat_str},{lat_dir},{lon_str},{lon_dir},{quality},{vis_count:02d},{hdop:.2f},{alt:.1f},M,0.0,M,,"
        sentences.append(f"${gga_body}*{compute_nmea_checksum(gga_body)}")

        # 2. $GNGSA: Active Satellites and DOP
        # Formato: $GNGSA,mode,fixType,prn1..prn12,PDOP,HDOP,VDOP
        pdop = dop_state.get("pdop", 1.0)
        vdop = dop_state.get("vdop", 1.0)
        fix_type = 3 if vis_count >= 4 else 1  # 3 = 3D Fix
        prn_slots = [f"{sat['id']:02d}" for sat in vis_sats[:12]]
        while len(prn_slots) < 12:
            prn_slots.append("")
        prn_str = ",".join(prn_slots)
        gsa_body = f"GNGSA,A,{fix_type},{prn_str},{pdop:.2f},{hdop:.2f},{vdop:.2f}"
        sentences.append(f"${gsa_body}*{compute_nmea_checksum(gsa_body)}")

        # 3. $GPGSV: Satellites in View (grupos de até 4 satélites por sentença)
        total_sats = len(sats)
        total_msgs = math.ceil(total_sats / 4.0) if total_sats > 0 else 1
        for msg_num in range(1, total_msgs + 1):
            chunk = sats[(msg_num - 1) * 4 : msg_num * 4]
            gsv_parts = [f"GPGSV,{total_msgs},{msg_num},{total_sats:02d}"]
            for sat in chunk:
                prn = sat["id"]
                el = max(0, int(sat.get("elevation_deg", 0)))
                az = int(sat.get("azimuth_deg", 0)) % 360
                snr = 45 if sat.get("in_view") else 20  # dB-Hz simulado
                gsv_parts.append(f"{prn:02d},{el:02d},{az:03d},{snr:02d}")
            gsv_body = ",".join(gsv_parts)
            sentences.append(f"${gsv_body}*{compute_nmea_checksum(gsv_body)}")

        return sentences


@router.get("/sentences", summary="Retorna as sentenças NMEA 0183 atuais ($GNGGA, $GNGSA, $GPGSV)")
def get_current_nmea_sentences() -> List[str]:
    """Gera e retorna as sentenças NMEA 0183 em tempo real para o instante atual."""
    hub = TelemetryHub.get_instance()
    snapshot = hub.get_snapshot()
    return NmeaSentenceFormatter.format_all(snapshot)


@router.get("/raw", response_class=PlainTextResponse, summary="Retorna o bloco NMEA 0183 em texto puro")
def get_raw_nmea_stream() -> str:
    """Retorna o fluxo textual formatado pronto para serial/socket."""
    sentences = get_current_nmea_sentences()
    return "\r\n".join(sentences) + "\r\n"
