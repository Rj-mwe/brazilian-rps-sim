"""
Domain Service: TroposphereSaastamoinenService
==============================================
Implementa o modelo clássico e analítico de Saastamoinen (1972, 1973) para o
cálculo determinístico do retardo troposférico (componentes hidrostática e úmida)
em sinais de radiofrequência GNSS / SBAS / RPS.

Normas e Referências:
- Saastamoinen, J. (1972). Atmospheric Correction for the Troposphere and
  Stratosphere in Radio Ranging of Satellites. Geophysical Monograph Series.
- IERS Conventions (2010), Technical Note No. 36, Capítulo 9.
- RTCA DO-229D / DO-229E (Apêndice A.4.4.11 - Tropospheric Model).
"""

import math
from rps_br.core.domain.shared.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO
from rps_br.core.domain.signal_propagation.value_objects.TroposphericWeatherVO import TroposphericWeatherVO
from rps_br.core.domain.signal_propagation.value_objects.TroposphericDelayVO import TroposphericDelayVO


class TroposphereSaastamoinenService:
    """
    Serviço de domínio para cálculo analítico do retardo troposférico.
    """

    SPEED_OF_LIGHT: float = 299792458.0  # m/s

    @classmethod
    def compute_delay(
        cls,
        user_coords: GeodeticCoordinatesVO,
        elevation_deg: float,
        weather: TroposphericWeatherVO | None = None,
    ) -> TroposphericDelayVO:
        """
        Calcula o retardo troposférico zenital e oblíquo para um satélite observado
        a partir de coordenadas geodésicas receptoras.

        Parâmetros:
            user_coords: Coordenadas geodésicas WGS-84 da estação (latitude, longitude, altitude).
            elevation_deg: Ângulo de elevação do satélite em graus (-90° a 90°).
            weather: Condições meteorológicas locais (opcional; se None, utiliza Atmosfera Padrão).

        Retorno:
            TroposphericDelayVO contendo ZHD, ZWD, ZTD, atrasos oblíquos e fator de escala m(el).
        """
        # 1. Se nenhuma condição meteorológica in-situ for fornecida, deriva a atmosfera padrão na altitude
        h_km = max(0.0, float(user_coords.altitude_km))
        if weather is None:
            weather = TroposphericWeatherVO.standard_at_altitude(h_km * 1000.0)

        p_0 = weather.pressure_hpa
        t_0 = weather.temperature_k
        e_0 = weather.water_vapor_pressure_hpa

        # 2. Coordenadas receptoras: altitude em km e latitude em radianos
        phi_rad = math.radians(user_coords.latitude_deg)

        # 3. Componente Hidrostática Zenital (ZHD - Zenith Hydrostatic Delay)
        # Fórmula de Saastamoinen clássica (IERS Conventions 2010):
        # f(phi, H) = 1 - 0.00266 * cos(2*phi) - 0.00028 * H_km
        f_phi_h = 1.0 - 0.00266 * math.cos(2.0 * phi_rad) - 0.00028 * h_km
        zhd_m = (0.0022768 * p_0) / f_phi_h

        # 4. Componente Úmida Zenital (ZWD - Zenith Wet Delay)
        # Saastamoinen (1972):
        # ZWD = 0.002277 * (1255 / T_0 + 0.05) * e_0
        zwd_m = 0.002277 * ((1255.0 / t_0) + 0.05) * e_0

        # Retardo Zenital Total (ZTD)
        ztd_m = zhd_m + zwd_m

        # 5. Função de Mapeamento Oblíquo (Slant Mapping Function)
        # Para evitar singularidades numéricas (divisão por zero quando el <= 0°),
        # adota-se a formulação de mapeamento de Chao / Black & Eisner contínua:
        # m(el) = 1 / (sin(el) + 0.00143 / (tan(el) + 0.0445))
        elev_clamped = max(0.0, min(90.0, float(elevation_deg)))
        
        if elev_clamped >= 89.99:
            mapping_factor = 1.0
        else:
            el_rad = math.radians(elev_clamped)
            sin_el = math.sin(el_rad)
            tan_el = math.tan(el_rad)
            denominator = sin_el + (0.00143 / (tan_el + 0.0445))
            mapping_factor = 1.0 / denominator

        # 6. Cálculo dos Retardos na Linha de Visada (Slant Delays)
        slant_hydro_m = zhd_m * mapping_factor
        slant_wet_m = zwd_m * mapping_factor
        slant_total_m = ztd_m * mapping_factor
        slant_total_sec = slant_total_m / cls.SPEED_OF_LIGHT

        return TroposphericDelayVO(
            zhd_m=zhd_m,
            zwd_m=zwd_m,
            zenith_total_delay_m=ztd_m,
            slant_hydrostatic_delay_m=slant_hydro_m,
            slant_wet_delay_m=slant_wet_m,
            slant_total_delay_m=slant_total_m,
            slant_total_delay_sec=slant_total_sec,
            mapping_factor=mapping_factor,
            elevation_deg=float(elevation_deg),
        )
