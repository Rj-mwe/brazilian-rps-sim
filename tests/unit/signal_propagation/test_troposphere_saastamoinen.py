"""
Testes Unitários: Modelo de Retardo Troposférico de Saastamoinen
================================================================
Verificação da modelagem hidrostática (seca) e úmida do retardo troposférico
conforme as especificações do IERS Conventions e RTCA DO-229D.
"""

import math
import pytest
from rps_br.core.domain.shared.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO
from rps_br.core.domain.signal_propagation.value_objects.TroposphericWeatherVO import TroposphericWeatherVO
from rps_br.core.domain.signal_propagation.value_objects.TroposphericDelayVO import TroposphericDelayVO
from rps_br.core.domain.signal_propagation.services.TroposphereSaastamoinenService import TroposphereSaastamoinenService


class TestTroposphereSaastamoinen:
    @pytest.fixture
    def sea_level_station(self) -> GeodeticCoordinatesVO:
        """Estação costeira ao nível do mar (Santos/SP, Lat: -23.96°, Lon: -46.33°, Alt: 5.0m = 0.005km)."""
        return GeodeticCoordinatesVO(latitude_deg=-23.96, longitude_deg=-46.33, altitude_km=0.005)

    @pytest.fixture
    def highland_station(self) -> GeodeticCoordinatesVO:
        """Estação em planalto elevado (Brasília/DF, Lat: -15.79°, Lon: -47.88°, Alt: 1172.0m = 1.172km)."""
        return GeodeticCoordinatesVO(latitude_deg=-15.79, longitude_deg=-47.88, altitude_km=1.172)

    @pytest.fixture
    def standard_sea_level_weather(self) -> TroposphericWeatherVO:
        """Atmosfera padrão ao nível do mar (1013.25 hPa, 15°C / 288.15 K, RH 50%)."""
        return TroposphericWeatherVO(
            pressure_hpa=1013.25,
            temperature_k=288.15,
            relative_humidity_pct=50.0,
        )

    # --------------------------------------------------------------------------
    # 1. Testes do Value Object de Clima (TroposphericWeatherVO)
    # --------------------------------------------------------------------------
    def test_weather_vo_creation_and_immutability(self, standard_sea_level_weather):
        """Garante que o VO é instanciado corretamente e é imutável."""
        assert standard_sea_level_weather.pressure_hpa == 1013.25
        assert standard_sea_level_weather.temperature_k == 288.15
        assert standard_sea_level_weather.relative_humidity_pct == 50.0
        assert standard_sea_level_weather.water_vapor_pressure_hpa > 0.0

        with pytest.raises(Exception):
            standard_sea_level_weather.pressure_hpa = 1000.0  # Imutável

    def test_weather_vo_validation_invariants(self):
        """Verifica que grandezas fisicamente impossíveis disparam ValueError."""
        # Pressão negativa ou nula
        with pytest.raises(ValueError, match="Pressão atmosférica"):
            TroposphericWeatherVO(pressure_hpa=-10.0, temperature_k=288.15, relative_humidity_pct=50.0)

        # Temperatura abaixo do zero absoluto
        with pytest.raises(ValueError, match="Temperatura absoluta"):
            TroposphericWeatherVO(pressure_hpa=1013.25, temperature_k=-5.0, relative_humidity_pct=50.0)

        # Umidade relativa inválida
        with pytest.raises(ValueError, match="Umidade relativa"):
            TroposphericWeatherVO(pressure_hpa=1013.25, temperature_k=288.15, relative_humidity_pct=150.0)

    def test_weather_vo_standard_atmosphere_at_altitude(self):
        """Verifica o decaimento barométrico e de temperatura na atmosfera padrão."""
        w_sea = TroposphericWeatherVO.standard_at_altitude(altitude_m=0.0)
        assert pytest.approx(w_sea.pressure_hpa, rel=1e-3) == 1013.25
        assert pytest.approx(w_sea.temperature_k, rel=1e-3) == 288.15

        # A 1000 m: gradiente térmico de -6.5 K/km
        w_1k = TroposphericWeatherVO.standard_at_altitude(altitude_m=1000.0)
        assert pytest.approx(w_1k.temperature_k, rel=1e-3) == 288.15 - 6.5
        assert w_1k.pressure_hpa < w_sea.pressure_hpa
        assert 890.0 < w_1k.pressure_hpa < 910.0

    # --------------------------------------------------------------------------
    # 2. Testes de Precisão Física de Saastamoinen (Zenith Delays)
    # --------------------------------------------------------------------------
    def test_zenith_hydrostatic_delay_sea_level(self, sea_level_station, standard_sea_level_weather):
        """
        O retardo hidrostático zenital (ZHD) ao nível do mar e pressão de 1013.25 hPa
        deve situar-se estritamente em torno de 2.30 a 2.31 metros (benchmark clássico do IERS).
        """
        delay = TroposphereSaastamoinenService.compute_delay(
            user_coords=sea_level_station,
            elevation_deg=90.0,
            weather=standard_sea_level_weather,
        )

        assert pytest.approx(delay.zhd_m, abs=0.02) == 2.307
        assert delay.elevation_deg == 90.0
        assert pytest.approx(delay.mapping_factor, abs=1e-3) == 1.0

    def test_zenith_wet_delay_magnitude(self, sea_level_station, standard_sea_level_weather):
        """
        A parcela úmida zenital (ZWD) sob condições moderadas (15°C, 50% RH)
        representa cerca de 5% a 10% do retardo total (entre 0.05 m e 0.15 m).
        """
        delay = TroposphereSaastamoinenService.compute_delay(
            user_coords=sea_level_station,
            elevation_deg=90.0,
            weather=standard_sea_level_weather,
        )

        assert 0.05 <= delay.zwd_m <= 0.20
        assert delay.zenith_total_delay_m == pytest.approx(delay.zhd_m + delay.zwd_m, abs=1e-5)
        assert 2.35 <= delay.zenith_total_delay_m <= 2.50

    # --------------------------------------------------------------------------
    # 3. Testes da Função de Mapeamento e Escala com a Elevação
    # --------------------------------------------------------------------------
    def test_slant_delay_elevation_scaling(self, sea_level_station, standard_sea_level_weather):
        """
        O atraso oblíquo na linha de visada deve aumentar conforme a elevação diminui:
        - Em 90°: m ≈ 1.0 (atraso zenital puro)
        - Em 30°: m ≈ 2.0 (csc(30°) = 2.0)
        - Em 10°: m ≈ 5.7 (csc(10°) ≈ 5.76)
        """
        d_90 = TroposphereSaastamoinenService.compute_delay(sea_level_station, 90.0, standard_sea_level_weather)
        d_30 = TroposphereSaastamoinenService.compute_delay(sea_level_station, 30.0, standard_sea_level_weather)
        d_10 = TroposphereSaastamoinenService.compute_delay(sea_level_station, 10.0, standard_sea_level_weather)

        # Mapeamento
        assert pytest.approx(d_90.mapping_factor, abs=0.01) == 1.0
        assert pytest.approx(d_30.mapping_factor, abs=0.05) == 2.0
        assert pytest.approx(d_10.mapping_factor, abs=0.20) == 5.7

        # Retardo total oblíquo
        assert d_90.slant_total_delay_m == pytest.approx(d_90.zenith_total_delay_m, abs=1e-3)
        assert pytest.approx(d_30.slant_total_delay_m, abs=0.1) == d_90.zenith_total_delay_m * 2.0
        assert d_10.slant_total_delay_m > d_30.slant_total_delay_m > d_90.slant_total_delay_m
        assert 12.0 <= d_10.slant_total_delay_m <= 15.0

    # --------------------------------------------------------------------------
    # 4. Testes de Redução por Altitude (Topografia Brasileira)
    # --------------------------------------------------------------------------
    def test_altitude_reduction_highland(self, highland_station):
        """
        Em altitudes elevadas (Brasília a 1172 m), a densidade e a pressão da coluna de ar
        são substancialmente menores, reduzindo o retardo zenital para cerca de 2.0 a 2.15 m.
        """
        delay_bsb = TroposphereSaastamoinenService.compute_delay(
            user_coords=highland_station,
            elevation_deg=90.0,
            weather=None,  # Deve utilizar atmosfera padrão na altitude da estação
        )

        assert delay_bsb.zhd_m < 2.15
        assert 1.95 <= delay_bsb.zenith_total_delay_m <= 2.20

    # --------------------------------------------------------------------------
    # 5. Testes de Unidades e Conversão Temporal
    # --------------------------------------------------------------------------
    def test_delay_vo_temporal_conversion(self, sea_level_station, standard_sea_level_weather):
        """Verifica a conversão para tempo de propagação via velocidade da luz c."""
        c = TroposphereSaastamoinenService.SPEED_OF_LIGHT
        delay = TroposphereSaastamoinenService.compute_delay(sea_level_station, 45.0, standard_sea_level_weather)

        expected_sec = delay.slant_total_delay_m / c
        assert pytest.approx(delay.slant_total_delay_sec, rel=1e-6) == expected_sec
        # Atraso em metros ~3.3m -> atraso em tempo ~11 nanossegundos
        assert 1.0e-8 <= delay.slant_total_delay_sec <= 2.0e-8

    # --------------------------------------------------------------------------
    # 6. Testes de Robustez Numérica na Linha do Horizonte
    # --------------------------------------------------------------------------
    def test_horizon_stability(self, sea_level_station, standard_sea_level_weather):
        """Garante que elevações muito baixas ou zero graus não geram divisão por zero."""
        delay_0 = TroposphereSaastamoinenService.compute_delay(sea_level_station, 0.0, standard_sea_level_weather)
        delay_neg = TroposphereSaastamoinenService.compute_delay(sea_level_station, -2.0, standard_sea_level_weather)

        assert not math.isnan(delay_0.slant_total_delay_m)
        assert not math.isinf(delay_0.slant_total_delay_m)
        assert delay_0.slant_total_delay_m > 0.0

        assert not math.isnan(delay_neg.slant_total_delay_m)
        assert delay_neg.slant_total_delay_m == delay_0.slant_total_delay_m
