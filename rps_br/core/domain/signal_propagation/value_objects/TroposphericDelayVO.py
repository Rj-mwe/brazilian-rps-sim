"""
Value Object: TroposphericDelayVO
==================================
Encapsula os resultados da modelagem do retardo troposférico (Saastamoinen),
discriminando as parcelas hidrostática (seca) e úmida tanto no zênite quanto
ao longo da linha de visada oblíqua (slant delay).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TroposphericDelayVO:
    """
    Retardo de propagação troposférica nas componentes zenital e oblíqua.

    Atributos:
        zhd_m: Retardo Hidrostático Zenital em metros (Zenith Hydrostatic Delay).
        zwd_m: Retardo Úmido Zenital em metros (Zenith Wet Delay).
        zenith_total_delay_m: Retardo total no zênite em metros (ZHD + ZWD).
        slant_hydrostatic_delay_m: Retardo hidrostático na linha de visada em metros.
        slant_wet_delay_m: Retardo úmido na linha de visada em metros.
        slant_total_delay_m: Retardo total na linha de visada oblíqua em metros.
        slant_total_delay_sec: Retardo temporal na linha de visada em segundos (Δt = Δ / c).
        mapping_factor: Fator de escala da função de mapeamento oblíquo m(el).
        elevation_deg: Ângulo de elevação do satélite em graus.
    """

    zhd_m: float
    zwd_m: float
    zenith_total_delay_m: float
    slant_hydrostatic_delay_m: float
    slant_wet_delay_m: float
    slant_total_delay_m: float
    slant_total_delay_sec: float
    mapping_factor: float
    elevation_deg: float
