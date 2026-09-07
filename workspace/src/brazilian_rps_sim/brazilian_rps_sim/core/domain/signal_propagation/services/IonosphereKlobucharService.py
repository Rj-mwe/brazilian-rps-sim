"""
Domain Service: IonosphereKlobucharService
==========================================
Implementa o modelo analítico padrão de retardo ionosférico de Klobuchar
segundo os requisitos normativos do IS-GPS-200 (Seção 20.3.3.5.2.5) e
RTCA DO-229D (Apêndice A.4.4.10).

Projetado para simular a Anomalia de Ionização Equatorial (EIA) e a dinâmica
de retardo diurno/noturno sobre o território brasileiro.
"""

import math
from brazilian_rps_sim.core.domain.shared.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO
from brazilian_rps_sim.core.domain.signal_propagation.value_objects.KlobucharCoefficientsVO import KlobucharCoefficientsVO
from brazilian_rps_sim.core.domain.signal_propagation.value_objects.IonosphericDelayVO import IonosphericDelayVO


class IonosphereKlobucharService:
    """
    Serviço de cálculo determinístico do retardo ionosférico de Klobuchar.
    """

    SPEED_OF_LIGHT: float = 299792458.0  # m/s
    GPS_L1_FREQ_HZ: float = 1575.42e6    # Hz
    NIGHTTIME_DELAY_SEC: float = 5.0e-9  # 5 nanossegundos padrão

    @classmethod
    def compute_delay(
        cls,
        user_coords: GeodeticCoordinatesVO,
        elevation_deg: float,
        azimuth_deg: float,
        gps_time_sec: float,
        coefficients: KlobucharCoefficientsVO,
        frequency_hz: float = GPS_L1_FREQ_HZ,
    ) -> IonosphericDelayVO:
        """
        Calcula o retardo ionosférico para um satélite observado a partir de uma dada posição.

        Parâmetros:
            user_coords: Coordenadas geodésicas WGS-84 do receptor (lat, lon, alt).
            elevation_deg: Ângulo de elevação do satélite em graus (0 a 90).
            azimuth_deg: Azimute do satélite em graus (0 a 360).
            gps_time_sec: Tempo GPS em segundos da semana (0 a 604800).
            coefficients: Objeto KlobucharCoefficientsVO contendo as 4 tuplas alpha e beta.
            frequency_hz: Frequência da portadora em Hz (padrão L1: 1575.42 MHz).

        Retorno:
            IonosphericDelayVO com métricas verticais e oblíquas em segundos e metros.
        """
        # 1. Conversão para unidades angulares em semi-círculos (semi-circles = graus / 180)
        # Limita elevação mínima a 0 para cálculo do IPP
        elev_clamped = max(0.0, min(90.0, float(elevation_deg)))
        e_sc = elev_clamped / 180.0
        a_sc = (float(azimuth_deg) % 360.0) / 180.0
        phi_u_sc = user_coords.latitude_deg / 180.0
        lambda_u_sc = user_coords.longitude_deg / 180.0

        # 2. Ângulo central da Terra entre o usuário e o IPP (Ionospheric Pierce Point)
        # Altura média da camada ionosférica adotada: h_iono = 350 km
        psi_sc = (0.0137 / (e_sc + 0.11)) - 0.022

        # 3. Latitude geodésica do ponto de penetração ionosférico (IPP)
        phi_i_sc = phi_u_sc + (psi_sc * math.cos(a_sc * math.pi))
        # Limite máximo de latitude subionisférica: +/- 0.416 semi-círculos (~74.88 graus)
        phi_i_sc = max(-0.416, min(0.416, phi_i_sc))

        # 4. Longitude geodésica do IPP
        lambda_i_sc = lambda_u_sc + (
            (psi_sc * math.sin(a_sc * math.pi)) / math.cos(phi_i_sc * math.pi)
        )

        # 5. Latitude geomagnética do IPP (polo geomagnético em 78.3°N, 291.0°E / 69.0°W)
        phi_m_sc = phi_i_sc + (0.064 * math.cos((lambda_i_sc - 1.617) * math.pi))

        # 6. Hora solar local no IPP (em segundos do dia)
        # t = 4.32e4 * lambda_i + t_gps
        t_local = (43200.0 * lambda_i_sc) + (gps_time_sec % 86400.0)
        t_local = t_local % 86400.0
        if t_local < 0.0:
            t_local += 86400.0

        # 7. Fator de obliquidade (Mapping Function F)
        # Modela o aumento de espessura de camada ao se afastar do zênite
        obliquity_factor = 1.0 + (16.0 * math.pow(0.53 - e_sc, 3))

        # 8. Amplitude do retardo diurno (A_I)
        alpha = coefficients.alpha
        amp_sec = alpha[0] + (alpha[1] * phi_m_sc) + (alpha[2] * phi_m_sc**2) + (alpha[3] * phi_m_sc**3)
        amp_sec = max(0.0, amp_sec)

        # 9. Período da curva diurna (P_I)
        beta = coefficients.beta
        period_sec = beta[0] + (beta[1] * phi_m_sc) + (beta[2] * phi_m_sc**2) + (beta[3] * phi_m_sc**3)
        period_sec = max(72000.0, period_sec)  # Período mínimo de 72.000 segundos (20 horas)

        # 10. Fase do retardo ionosférico (x) com pico às 14:00 (50.400 segundos)
        phase_rad = (2.0 * math.pi * (t_local - 50400.0)) / period_sec

        # 11. Retardo vertical (T_v)
        # Se |x| < 1.57 (~pi/2), está sob a curva diurna (aproximação de Taylor de 4ª ordem)
        # Caso contrário, aplica-se o piso noturno constante de 5 ns
        if abs(phase_rad) < 1.57:
            x2 = phase_rad * phase_rad
            x4 = x2 * x2
            poly_expansion = 1.0 - (x2 / 2.0) + (x4 / 24.0)
            vertical_delay_l1_sec = cls.NIGHTTIME_DELAY_SEC + (amp_sec * poly_expansion)
            is_nighttime = False
        else:
            vertical_delay_l1_sec = cls.NIGHTTIME_DELAY_SEC
            is_nighttime = True

        # 12. Retardo oblíquo (Slant Delay) na frequência L1
        slant_delay_l1_sec = obliquity_factor * vertical_delay_l1_sec

        # 13. Escalonamento por frequência da portadora: retardo varia inversamente com f^2
        freq_ratio = cls.GPS_L1_FREQ_HZ / float(frequency_hz)
        freq_scale = freq_ratio * freq_ratio

        slant_delay_sec = slant_delay_l1_sec * freq_scale
        slant_delay_meters = slant_delay_sec * cls.SPEED_OF_LIGHT

        return IonosphericDelayVO(
            vertical_delay_s=vertical_delay_l1_sec,
            slant_delay_s=slant_delay_sec,
            slant_delay_m=slant_delay_meters,
            obliquity_factor=obliquity_factor,
            pierce_point_lat_deg=phi_i_sc * 180.0,
            pierce_point_lon_deg=lambda_i_sc * 180.0,
            geomagnetic_lat_deg=phi_m_sc * 180.0,
            is_nighttime=is_nighttime,
            frequency_hz=float(frequency_hz),
        )
