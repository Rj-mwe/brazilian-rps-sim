"""
Value Object: PseudorangeMeasurementVO
======================================
Representa a medição completa de pseudodistância bruta (raw pseudorange)
para um satélite observado, discriminando cada uma das contribuições físicas:
distância geométrica Euclidiana, tempo de trânsito, retardos atmosféricos
(ionosfera e troposfera), viés do oscilador do receptor, erro de relógio do satélite,
efeito relativístico orbital e ruído térmico residual.

Conforme especificações:
- IS-GPS-200 (Seção 20.3.3)
- RTCA DO-229D (Apêndice A e J)
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PseudorangeMeasurementVO:
    """
    Medição de pseudodistância GNSS com discriminação analítica de erros.

    Atributos:
        satellite_id: Identificador do satélite (ex: "RPS-GEO-1", "RPS-IGSO-1").
        pseudorange_m: Pseudodistância bruta final calculada em metros (ρ).
        geometric_range_m: Distância geométrica Euclidiana pura em metros (R).
        ionospheric_delay_m: Retardo ionosférico oblíquo de grupo em metros (I).
        tropospheric_delay_m: Retardo troposférico oblíquo em metros (T).
        receiver_clock_bias_m: Desvio de relógio do receptor em metros (c * δt_rx).
        satellite_clock_bias_m: Desvio de relógio do satélite em metros (c * δt_sat).
        relativistic_delay_m: Correção relativística periódica da órbita em metros (Δ_rel).
        noise_m: Ruído residual térmico / estocástico em metros (ε).
        elevation_deg: Ângulo de elevação do satélite visto pelo receptor em graus.
        azimuth_deg: Ângulo de azimute do satélite em graus.
        transit_time_sec: Tempo estimado de voo do sinal em segundos (τ = R / c).
    """

    satellite_id: str
    pseudorange_m: float
    geometric_range_m: float
    ionospheric_delay_m: float
    tropospheric_delay_m: float
    receiver_clock_bias_m: float
    satellite_clock_bias_m: float
    relativistic_delay_m: float
    noise_m: float
    elevation_deg: float
    azimuth_deg: float
    transit_time_sec: float

    def __post_init__(self) -> None:
        if not self.satellite_id:
            raise ValueError("satellite_id não pode ser vazio.")
        if self.geometric_range_m <= 0.0:
            raise ValueError(f"geometric_range_m deve ser estritamente positivo: {self.geometric_range_m}")
        if self.pseudorange_m <= 0.0:
            raise ValueError(f"pseudorange_m deve ser estritamente positivo: {self.pseudorange_m}")
        if self.transit_time_sec <= 0.0:
            raise ValueError(f"transit_time_sec deve ser estritamente positivo: {self.transit_time_sec}")
