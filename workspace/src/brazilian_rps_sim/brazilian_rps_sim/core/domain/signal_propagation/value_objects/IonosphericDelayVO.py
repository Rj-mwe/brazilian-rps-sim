"""
Value Object: IonosphericDelayVO
=================================
Representa o resultado imutável do cálculo de retardo ionosférico
em tempo de trânsito e em metros de pseudodistância.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class IonosphericDelayVO:
    """
    Métricas de retardo ionosférico calculadas para uma dada linha de visada (LOS).
    """
    vertical_delay_s: float
    slant_delay_s: float
    slant_delay_m: float
    obliquity_factor: float
    pierce_point_lat_deg: float
    pierce_point_lon_deg: float
    geomagnetic_lat_deg: float
    is_nighttime: bool
    frequency_hz: float

    def __post_init__(self) -> None:
        if self.vertical_delay_s < 0.0:
            raise ValueError(f"Retardo vertical não pode ser negativo: {self.vertical_delay_s}")
        if self.slant_delay_s < 0.0:
            raise ValueError(f"Retardo oblíquo não pode ser negativo: {self.slant_delay_s}")
        if self.obliquity_factor < 1.0:
            raise ValueError(f"Fator de obliquidade não pode ser menor que 1.0: {self.obliquity_factor}")
        if self.frequency_hz <= 0.0:
            raise ValueError(f"Frequência portadora deve ser positiva: {self.frequency_hz}")
