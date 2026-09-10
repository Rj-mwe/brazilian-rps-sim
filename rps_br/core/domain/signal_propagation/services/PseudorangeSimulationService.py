"""
Domain Service: PseudorangeSimulationService
============================================
Serviço puro de domínio para geração determinística e estocástica de medições
de pseudodistância bruta (raw pseudoranges) para sinais GNSS / SBAS / RPS.

Modela a equação completa de rádio da pseudodistância:
    ρ_i = R_i + c*(δt_rx - δt_sat) + I_i + T_i + Δ_rel,i + ε_i

Normas de Referência:
- IS-GPS-200 (Seções 20.3.3.3.3.1 e 20.3.3.5.2)
- RTCA DO-229D / DO-229E (Apêndices A e J)
"""

import math
import random
from typing import Dict, Optional

from rps_br.core.domain.shared.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO
from rps_br.core.domain.shared.value_objects.Vector3DVO import Vector3DVO
from rps_br.core.domain.astrodynamics.aggregates.ConstellationAggregate import ConstellationAggregate
from rps_br.core.domain.astrodynamics.services.CoordinateTransformService import CoordinateTransformService
from rps_br.core.domain.signal_propagation.value_objects.PseudorangeMeasurementVO import PseudorangeMeasurementVO
from rps_br.core.domain.signal_propagation.value_objects.KlobucharCoefficientsVO import KlobucharCoefficientsVO
from rps_br.core.domain.signal_propagation.value_objects.TroposphericWeatherVO import TroposphericWeatherVO
from rps_br.core.domain.signal_propagation.services.IonosphereKlobucharService import IonosphereKlobucharService
from rps_br.core.domain.signal_propagation.services.TroposphereSaastamoinenService import TroposphereSaastamoinenService


class PseudorangeSimulationService:
    """
    Serviço de simulação de observáveis de pseudodistância de radionavegação.
    """

    SPEED_OF_LIGHT: float = 299792458.0  # m/s

    @classmethod
    def compute_pseudorange(
        cls,
        sat_name: str,
        r_sat_eci: Vector3DVO,
        v_sat_eci: Vector3DVO,
        r_sat_ecef: Vector3DVO,
        user_coords: GeodeticCoordinatesVO,
        gps_time_sec: float = 0.0,
        receiver_clock_bias_s: float = 0.0,
        satellite_clock_bias_s: float = 0.0,
        include_ionosphere: bool = True,
        include_troposphere: bool = True,
        include_relativity: bool = True,
        klobuchar_coefficients: Optional[KlobucharCoefficientsVO] = None,
        tropospheric_weather: Optional[TroposphericWeatherVO] = None,
        noise_sigma_m: float = 0.0,
        elevation_weighted_noise: bool = True,
        rng: Optional[random.Random] = None,
    ) -> PseudorangeMeasurementVO:
        """
        Calcula a pseudodistância completa para um satélite individual.
        """
        # 1. Ângulos topocêntricos e distância puramente geométrica Euclidiana
        elevation_deg, azimuth_deg, range_km = CoordinateTransformService.compute_topocentric_look_angles(
            r_sat_ecef.to_numpy(), user_coords.latitude_deg, user_coords.longitude_deg, alt_gs_km=user_coords.altitude_km
        )
        geometric_range_m = range_km * 1000.0
        transit_time_sec = geometric_range_m / cls.SPEED_OF_LIGHT

        # 2. Correção Relativística Orbital (IS-GPS-200): Δ_rel = -2*(r . v)/c
        # r em km, v em km/s -> r . v em km^2/s = 1e6 m^2/s
        if include_relativity:
            dot_r_v_m2_s = r_sat_eci.dot(v_sat_eci) * 1.0e6
            relativistic_delay_m = -2.0 * dot_r_v_m2_s / cls.SPEED_OF_LIGHT
        else:
            relativistic_delay_m = 0.0

        # 3. Retardo Ionosférico de Grupo (Klobuchar)
        if include_ionosphere:
            if klobuchar_coefficients is None:
                klobuchar_coefficients = KlobucharCoefficientsVO.brazilian_equatorial_high_solar()
            iono_delay_vo = IonosphereKlobucharService.compute_delay(
                user_coords=user_coords,
                elevation_deg=max(0.0, elevation_deg),
                azimuth_deg=azimuth_deg,
                gps_time_sec=gps_time_sec,
                coefficients=klobuchar_coefficients,
            )
            ionospheric_delay_m = iono_delay_vo.slant_delay_m
        else:
            ionospheric_delay_m = 0.0

        # 4. Retardo Troposférico Oblíquo (Saastamoinen)
        if include_troposphere:
            tropo_delay_vo = TroposphereSaastamoinenService.compute_delay(
                user_coords=user_coords,
                elevation_deg=max(0.0, elevation_deg),
                weather=tropospheric_weather,
            )
            tropospheric_delay_m = tropo_delay_vo.slant_total_delay_m
        else:
            tropospheric_delay_m = 0.0

        # 5. Desvios de Relógio (Clock Biases convertidos para metros)
        receiver_clock_bias_m = receiver_clock_bias_s * cls.SPEED_OF_LIGHT
        satellite_clock_bias_m = satellite_clock_bias_s * cls.SPEED_OF_LIGHT

        # 6. Ruído Estocástico / Térmico do Receptor (Gaussiano)
        if noise_sigma_m > 0.0:
            if rng is None:
                rng = random.Random()
            if elevation_weighted_noise and elevation_deg > 0.0:
                sin_el = math.sin(math.radians(max(5.0, elevation_deg)))
                effective_sigma = noise_sigma_m / sin_el
            else:
                effective_sigma = noise_sigma_m
            noise_m = rng.gauss(0.0, effective_sigma)
        else:
            noise_m = 0.0

        # 7. Equação Fundamental da Pseudodistância
        pseudorange_m = (
            geometric_range_m
            + receiver_clock_bias_m
            - satellite_clock_bias_m
            + ionospheric_delay_m
            + tropospheric_delay_m
            + relativistic_delay_m
            + noise_m
        )

        return PseudorangeMeasurementVO(
            satellite_id=sat_name,
            pseudorange_m=pseudorange_m,
            geometric_range_m=geometric_range_m,
            ionospheric_delay_m=ionospheric_delay_m,
            tropospheric_delay_m=tropospheric_delay_m,
            receiver_clock_bias_m=receiver_clock_bias_m,
            satellite_clock_bias_m=satellite_clock_bias_m,
            relativistic_delay_m=relativistic_delay_m,
            noise_m=noise_m,
            elevation_deg=elevation_deg,
            azimuth_deg=azimuth_deg,
            transit_time_sec=transit_time_sec,
        )

    @classmethod
    def simulate_constellation_pseudoranges(
        cls,
        constellation: ConstellationAggregate,
        user_coords: GeodeticCoordinatesVO,
        gps_time_sec: float = 0.0,
        elevation_mask_deg: float = 5.0,
        receiver_clock_bias_s: float = 0.0,
        satellite_clock_biases_s: Optional[Dict[str, float]] = None,
        include_ionosphere: bool = True,
        include_troposphere: bool = True,
        include_relativity: bool = True,
        klobuchar_coefficients: Optional[KlobucharCoefficientsVO] = None,
        tropospheric_weather: Optional[TroposphericWeatherVO] = None,
        noise_sigma_m: float = 0.0,
        elevation_weighted_noise: bool = True,
        random_seed: Optional[int] = None,
    ) -> Dict[str, PseudorangeMeasurementVO]:
        """
        Simula as medições de pseudodistância para todos os satélites da constelação
        que se encontram acima da máscara de elevação em relação à estação do usuário.
        """
        rng = random.Random(random_seed) if random_seed is not None else random.Random()
        measurements: Dict[str, PseudorangeMeasurementVO] = {}

        for sat in constellation.satellites:
            # Avaliação prévia de visibilidade
            el, az, _ = CoordinateTransformService.compute_topocentric_look_angles(
                sat.r_ecef.to_numpy(), user_coords.latitude_deg, user_coords.longitude_deg, alt_gs_km=user_coords.altitude_km
            )
            if el < elevation_mask_deg:
                continue

            sat_bias_s = (
                satellite_clock_biases_s.get(sat.name, 0.0)
                if satellite_clock_biases_s is not None
                else 0.0
            )

            measurement = cls.compute_pseudorange(
                sat_name=sat.name,
                r_sat_eci=sat.r_eci,
                v_sat_eci=sat.v_eci,
                r_sat_ecef=sat.r_ecef,
                user_coords=user_coords,
                gps_time_sec=gps_time_sec,
                receiver_clock_bias_s=receiver_clock_bias_s,
                satellite_clock_bias_s=sat_bias_s,
                include_ionosphere=include_ionosphere,
                include_troposphere=include_troposphere,
                include_relativity=include_relativity,
                klobuchar_coefficients=klobuchar_coefficients,
                tropospheric_weather=tropospheric_weather,
                noise_sigma_m=noise_sigma_m,
                elevation_weighted_noise=elevation_weighted_noise,
                rng=rng,
            )
            measurements[sat.name] = measurement

        return measurements
