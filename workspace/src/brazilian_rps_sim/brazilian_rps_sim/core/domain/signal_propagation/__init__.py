"""
Subdomínio: Propagação de Sinais GNSS e Meio Físico
===================================================
Modelagem de efeitos atmosféricos (ionosfera de Klobuchar, troposfera de Saastamoinen),
efeitos relativísticos e atenuações de sinal na transmissão espacial.
"""

from .services.IonosphereKlobucharService import IonosphereKlobucharService
from .value_objects.KlobucharCoefficientsVO import KlobucharCoefficientsVO
from .value_objects.IonosphericDelayVO import IonosphericDelayVO

__all__ = [
    "IonosphereKlobucharService",
    "KlobucharCoefficientsVO",
    "IonosphericDelayVO",
]
