"""
Adaptador de Navegação e Protocolo NMEA 0183.
"""

from .nmea_streamer import router as nmea_router, NmeaSentenceFormatter, compute_nmea_checksum

__all__ = ["nmea_router", "NmeaSentenceFormatter", "compute_nmea_checksum"]
