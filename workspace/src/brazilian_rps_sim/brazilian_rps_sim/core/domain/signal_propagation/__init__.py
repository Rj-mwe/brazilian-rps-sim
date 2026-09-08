"""
Subdomínio: Propagação de Sinais GNSS e Meio Físico
===================================================
Modelagem de efeitos atmosféricos (ionosfera de Klobuchar, troposfera de Saastamoinen),
efeitos relativísticos e atenuações de sinal na transmissão espacial.
"""

from .services.IonosphereKlobucharService import IonosphereKlobucharService
from .services.TroposphereSaastamoinenService import TroposphereSaastamoinenService
from .value_objects.KlobucharCoefficientsVO import KlobucharCoefficientsVO
from .value_objects.IonosphericDelayVO import IonosphericDelayVO
from .value_objects.TroposphericWeatherVO import TroposphericWeatherVO
from .value_objects.TroposphericDelayVO import TroposphericDelayVO

__all__ = [
    "IonosphereKlobucharService",
    "TroposphereSaastamoinenService",
    "KlobucharCoefficientsVO",
    "IonosphericDelayVO",
    "TroposphericWeatherVO",
    "TroposphericDelayVO",
]
