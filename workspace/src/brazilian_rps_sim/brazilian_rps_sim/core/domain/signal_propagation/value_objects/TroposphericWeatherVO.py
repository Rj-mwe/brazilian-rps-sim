"""
Value Object: TroposphericWeatherVO
====================================
Representa as grandezas meteorológicas locais da camada troposférica
(Pressão, Temperatura Absoluta e Umidade Relativa) necessárias para o cálculo
do retardo de propagação troposférico em frequências de rádio e GNSS.
"""

from dataclasses import dataclass, field
import math


@dataclass(frozen=True)
class TroposphericWeatherVO:
    """
    Condições meteorológicas superficiais na antena do receptor.

    Atributos:
        pressure_hpa: Pressão atmosférica total em hectopascais (hPa ou mbar).
        temperature_k: Temperatura absoluta em Kelvin (K).
        relative_humidity_pct: Umidade relativa do ar em percentagem [0.0, 100.0]%.
        water_vapor_pressure_hpa: Pressão parcial de vapor d'água calculada em hPa.
    """

    pressure_hpa: float
    temperature_k: float
    relative_humidity_pct: float = 50.0
    water_vapor_pressure_hpa: float = field(init=False)

    def __post_init__(self) -> None:
        if self.pressure_hpa <= 0.0:
            raise ValueError(f"Pressão atmosférica deve ser estritamente positiva (> 0 hPa). Valor: {self.pressure_hpa}")
        if self.temperature_k <= 0.0:
            raise ValueError(f"Temperatura absoluta deve ser superior ao zero absoluto (> 0 K). Valor: {self.temperature_k}")
        if not (0.0 <= self.relative_humidity_pct <= 100.0):
            raise ValueError(f"Umidade relativa deve situar-se no intervalo [0, 100]%. Valor: {self.relative_humidity_pct}")

        # Cálculo da pressão de saturação de vapor d'água (Fórmula de Magnus-Tetens para a troposfera)
        t_celsius = self.temperature_k - 273.15
        e_sat_hpa = 6.1121 * math.exp((17.502 * t_celsius) / (t_celsius + 240.97))
        e_0 = (self.relative_humidity_pct / 100.0) * e_sat_hpa

        object.__setattr__(self, "water_vapor_pressure_hpa", e_0)

    @classmethod
    def standard_at_altitude(cls, altitude_m: float = 0.0) -> "TroposphericWeatherVO":
        """
        Gera o perfil de atmosfera padrão (Standard Atmosphere ICAO / US Standard 1976)
        para uma dada altitude ortométrica/elipsoidal em metros.

        Parâmetros:
            altitude_m: Altitude do receptor acima do nível médio do mar (m).
        """
        alt_clamped = max(-500.0, min(11000.0, float(altitude_m)))
        h_km = alt_clamped / 1000.0

        # Parâmetros padrão ao nível do mar (MSL)
        t_sl = 288.15      # 15.0 °C
        p_sl = 1013.25     # hPa
        rh_sl = 50.0       # %

        # Gradiente térmico troposférico padrão: -6.5 K / km
        temp_k = t_sl - 6.5 * h_km

        # Equação barométrica politrópica (expoente g*M / (R*L) ≈ 5.255877)
        pressure_hpa = p_sl * math.pow(1.0 - (0.0065 * alt_clamped) / t_sl, 5.255877)

        # Decaimento suave de umidade relativa com altitude
        rh_pct = rh_sl * math.exp(-0.0006396 * alt_clamped)
        rh_pct = max(10.0, min(100.0, rh_pct))

        return cls(
            pressure_hpa=pressure_hpa,
            temperature_k=temp_k,
            relative_humidity_pct=rh_pct,
        )
