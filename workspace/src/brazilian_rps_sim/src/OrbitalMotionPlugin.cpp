/**
 * @file OrbitalMotionPlugin.cpp
 * @brief Plugin C++ do Gazebo Harmonic para simulação analítica dos satélites do RPS-BR.
 * 
 * Funcionalidades:
 * - Resolução da Equação de Kepler por Newton-Raphson para satélites GEO e IGSO.
 * - Transformação analítica de coordenadas: Perifocal (PQW) -> Inercial (ECI J2000) -> Terrestre (ECEF).
 * - Apontamento Nadir contínuo (antenas do satélite apontadas para o centro da Terra).
 */

#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/components/Pose.hh>
#include <gz/sim/components/Name.hh>
#include <gz/plugin/Register.hh>
#include <gz/math/Pose3.hh>
#include <gz/math/Vector3.hh>
#include <gz/math/Quaternion.hh>
#include <cmath>
#include <iostream>

namespace brazilian_rps
{

class OrbitalMotionPlugin : public gz::sim::System,
                            public gz::sim::ISystemConfigure,
                            public gz::sim::ISystemPreUpdate
{
private:
    gz::sim::Model model{gz::sim::kNullEntity};
    
    // Parâmetros Orbitais Keplerianos
    double a{42.164};                   // Semieixo maior em escala (42.164 unidades = 42.164 km)
    double e{0.05};                     // Excentricidade orbital
    double inc{29.0 * M_PI / 180.0};    // Inclinação orbital (rad)
    double raan{310.0 * M_PI / 180.0};  // Longitude do Nó Ascendente - RAAN (rad)
    double argp{270.0 * M_PI / 180.0};  // Argumento do Perigeu (rad)
    double m0{0.0};                     // Anomalia Média inicial (rad)
    double time_scale{300.0};           // Fator de aceleração temporal (300x)
    
    // Velocidades Angulares
    double mean_motion{7.292115e-5};    // Velocidade angular orbital média (rad/s)
    double earth_rotation{7.292115e-5};  // Rotação sidérea da Terra (rad/s)

public:
    void Configure(const gz::sim::Entity &_entity,
                   const std::shared_ptr<const sdf::Element> &_sdf,
                   gz::sim::EntityComponentManager &_ecm,
                   gz::sim::EventManager &/*_eventMgr*/) override
    {
        this->model = gz::sim::Model(_entity);

        if (_sdf->HasElement("semi_major_axis"))
            this->a = _sdf->Get<double>("semi_major_axis");
        if (_sdf->HasElement("eccentricity"))
            this->e = _sdf->Get<double>("eccentricity");
        if (_sdf->HasElement("inclination_deg"))
            this->inc = _sdf->Get<double>("inclination_deg") * M_PI / 180.0;
        if (_sdf->HasElement("raan_deg"))
            this->raan = _sdf->Get<double>("raan_deg") * M_PI / 180.0;
        if (_sdf->HasElement("arg_perigee_deg"))
            this->argp = _sdf->Get<double>("arg_perigee_deg") * M_PI / 180.0;
        if (_sdf->HasElement("mean_anomaly_deg"))
            this->m0 = _sdf->Get<double>("mean_anomaly_deg") * M_PI / 180.0;
        if (_sdf->HasElement("time_scale"))
            this->time_scale = _sdf->Get<double>("time_scale");

        std::cout << "🛰️ [OrbitalPlugin] Satélite " << this->model.Name(_ecm) 
                  << " ativo: a=" << this->a << " e=" << this->e 
                  << " inc=" << (this->inc * 180.0 / M_PI) << "° (Scale: " << this->time_scale << "x)\n";
    }

    void PreUpdate(const gz::sim::UpdateInfo &_info,
                   gz::sim::EntityComponentManager &_ecm) override
    {
        if (_info.paused)
            return;

        // Tempo de simulação acelerado acumulado
        double sim_sec = std::chrono::duration<double>(_info.simTime).count() * this->time_scale;

        // 1. Cálculo da Anomalia Média M(t)
        double M = std::fmod(this->m0 + this->mean_motion * sim_sec, 2.0 * M_PI);
        if (M < 0) M += 2.0 * M_PI;

        // 2. Resolução da Equação Transcendental de Kepler por Newton-Raphson
        double E = M;
        for (int k = 0; k < 15; ++k)
        {
            double f = E - this->e * std::sin(E) - M;
            double f_prime = 1.0 - this->e * std::cos(E);
            double dE = -f / f_prime;
            E += dE;
            if (std::abs(dE) < 1e-8) break;
        }

        // 3. Anomalia Verdadeira nu e Raio Orbital r
        double sin_nu = (std::sqrt(1.0 - this->e * this->e) * std::sin(E)) / (1.0 - this->e * std::cos(E));
        double cos_nu = (std::cos(E) - this->e) / (1.0 - this->e * std::cos(E));
        double nu = std::atan2(sin_nu, cos_nu);
        double r = this->a * (1.0 - this->e * std::cos(E));

        // 4. Posição no Plano Orbital Perifocal (PQW)
        double p_x = r * std::cos(nu);
        double p_y = r * std::sin(nu);

        // 5. Rotação para o Referencial Inercial Celeste (ECI J2000)
        double c_O = std::cos(this->raan), s_O = std::sin(this->raan);
        double c_i = std::cos(this->inc),  s_i = std::sin(this->inc);
        double c_w = std::cos(this->argp), s_w = std::sin(this->argp);

        double x_eci = (c_O * c_w - s_O * s_w * c_i) * p_x + (-c_O * s_w - s_O * c_w * c_i) * p_y;
        double y_eci = (s_O * c_w + c_O * s_w * c_i) * p_x + (-s_O * s_w + c_O * c_w * c_i) * p_y;
        double z_eci = (s_w * s_i) * p_x + (c_w * s_i) * p_y;

        // 6. Rotação para o Referencial Terrestre Fixo (ECEF)
        double theta = this->earth_rotation * sim_sec;
        double c_th = std::cos(theta), s_th = std::sin(theta);

        double x_ecef =  c_th * x_eci + s_th * y_eci;
        double y_ecef = -s_th * x_eci + c_th * y_eci;
        double z_ecef = z_eci;

        // 7. Apontamento de Atitude Nadir (Eixo Z apontado para o centro da Terra)
        gz::math::Vector3d pos(x_ecef, y_ecef, z_ecef);
        gz::math::Vector3d dir_to_earth = (-pos).Normalized();
        gz::math::Quaterniond rot;
        rot.SetFrom2Axes(gz::math::Vector3d::UnitZ, dir_to_earth);

        // 8. Aplicação da Pose no Gazebo
        auto poseComp = _ecm.Component<gz::sim::components::Pose>(this->model.Entity());
        if (poseComp)
        {
            *poseComp = gz::sim::components::Pose(gz::math::Pose3d(pos, rot));
            _ecm.SetChanged(this->model.Entity(), gz::sim::components::Pose::typeId, gz::sim::ComponentState::PeriodicChange);
        }
    }
};

} // namespace brazilian_rps

GZ_ADD_PLUGIN(brazilian_rps::OrbitalMotionPlugin,
              gz::sim::System,
              brazilian_rps::OrbitalMotionPlugin::ISystemConfigure,
              brazilian_rps::OrbitalMotionPlugin::ISystemPreUpdate)

GZ_ADD_PLUGIN_ALIAS(brazilian_rps::OrbitalMotionPlugin, "brazilian_rps::OrbitalMotionPlugin")
