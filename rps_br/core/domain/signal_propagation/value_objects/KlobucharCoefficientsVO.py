"""
Value Object: KlobucharCoefficientsVO
======================================
Representa os 8 coeficientes de broadcast transmitidos na mensagem de navegação
GNSS (Subframe 4, Page 18 do GPS) conforme especificado no IS-GPS-200 e RTCA DO-229.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class KlobucharCoefficientsVO:
    """
    Coeficientes do modelo ionosférico de Klobuchar.
    
    alpha: Coeficientes de amplitude da curva diurna (segundos / semi-círculos^n).
           alpha_0 (s), alpha_1 (s/sc), alpha_2 (s/sc^2), alpha_3 (s/sc^3)
    beta:  Coeficientes do período da curva diurna (segundos / semi-círculos^n).
           beta_0 (s), beta_1 (s/sc), beta_2 (s/sc^2), beta_3 (s/sc^3)
    """
    alpha: Tuple[float, float, float, float]
    beta: Tuple[float, float, float, float]

    def __post_init__(self) -> None:
        if len(self.alpha) != 4:
            raise ValueError(f"alpha deve conter exatamente 4 coeficientes, recebido {len(self.alpha)}")
        if len(self.beta) != 4:
            raise ValueError(f"beta deve conter exatamente 4 coeficientes, recebido {len(self.beta)}")

    @classmethod
    def default_gps_broadcast(cls) -> "KlobucharCoefficientsVO":
        """Vetor de teste padrão oficial do IS-GPS-200 / RTCA DO-229."""
        return cls(
            alpha=(0.1397e-07, -0.7451e-08, -0.5960e-07, 0.1192e-06),
            beta=(0.1106e06, -0.1311e06, -0.2621e06, 0.7864e06),
        )

    @classmethod
    def brazilian_equatorial_high_solar(cls) -> "KlobucharCoefficientsVO":
        """
        Calibração para a Anomalia de Ionização Equatorial (EIA) sobre o Brasil
        em período de alta atividade solar (F10.7 > 150).
        """
        return cls(
            alpha=(3.82e-08, 1.49e-08, -5.96e-08, -1.19e-07),
            beta=(1.25e05, 3.28e04, -1.97e05, -3.93e05),
        )

    @classmethod
    def brazilian_equatorial_low_solar(cls) -> "KlobucharCoefficientsVO":
        """
        Calibração para a região equatorial brasileira em período de baixa atividade solar.
        """
        return cls(
            alpha=(1.12e-08, 0.0, -2.98e-08, 0.0),
            beta=(9.00e04, 0.0, -1.31e05, 0.0),
        )
