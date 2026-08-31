/**
 * @file OrbitalMotionPlugin.cpp
 * @brief Plugin C++ do Gazebo Harmonic para simulação analítica dos satélites do RPS-BR
 *        com leitura declarativa de parâmetros via config/simulation_parameters.yaml.
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
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

namespace brazilian_rps
{

// Constantes Astronômicas Heliocêntricas
constexpr double DIST_SUN_EARTH = 1200.0;                   // Distância representativa Sol-Terra
constexpr double SECONDS_PER_YEAR = 365.256363 * 86400.0;   // Ano Sideral da Terra (s)
constexpr double OMEGA_EARTH_ORBIT = 2.0 * M_PI / SECONDS_PER_YEAR;

inline double load_time_multiplier_from_yaml()
{
    std::vector<std::string> paths = {
        "/home/rjgamito/ros2_ws/install/brazilian_rps_sim/share/brazilian_rps_sim/config/simulation_parameters.yaml",
        "/home/rjgamito/ros2_ws/src/brazilian_rps_sim/config/simulation_parameters.yaml",
        "/home/rjgamito/Projetos/Engenharia/Aeroespacial/brazilian-rps-sim/workspace/src/brazilian_rps_sim/config/simulation_parameters.yaml"
    };
    for (const auto &p : paths)
    {
        std::ifstream file(p);
        if (file.is_open())
        {
            std::string line;
            while (std::getline(file, line))
            {
                auto pos = line.find("time_multiplier:");
                if (pos != std::string::npos)
                {
                    std::stringstream ss(line.substr(pos + 16));
                    double val = 1.0;
                    if (ss >> val)
                        return val;
                }
            }
        }
    }
    return 1.0;
}

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
    double time_scale{1.0};             // Fator de aceleração temporal
    bool heliocentric{false};           // Se true, translada junto com a Terra ao redor do Sol

    // Velocidades Angulares
    double mean_motion{7.292115e-5};    // Velocidade angular orbital média (rad/s)
    double earth_rotation{7.292115e-5};  // Rotação sidérea da Terra (rad/s)

    std::chrono::steady_clock::duration last_sim_time{std::chrono::steady_clock::duration::min()};

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
        
        // Lê do simulation_parameters.yaml
        this->time_scale = load_time_multiplier_from_yaml();

        if (_sdf->HasElement("time_scale"))
        {
            double override_scale = _sdf->Get<double>("time_scale");
            if (override_scale != 1.0)
                this->time_scale = override_scale;
        }

        if (_sdf->HasElement("heliocentric"))
            this->heliocentric = _sdf->Get<bool>("heliocentric");

        std::cout << "🛰️ [OrbitalPlugin] Satélite " << this->model.Name(_ecm) 
                  << " ativo: a=" << this->a << " e=" << this->e 
                  << " inc=" << (this->inc * 180.0 / M_PI) << "° (Scale: " << this->time_scale 
                  << "x, Helio: " << (this->heliocentric ? "Sim" : "Não") << ")\n";
    }

    void PreUpdate(const gz::sim::UpdateInfo &_info,
                   gz::sim::EntityComponentManager &_ecm) override
    {
        if (_info.simTime == this->last_sim_time)
            return;

        this->last_sim_time = _info.simTime;
        double sim_sec = std::chrono::duration<double>(_info.simTime).count() * this->time_scale;

        // 1. Resolução Transcendental de Kepler (Newton-Raphson)
        double M = std::fmod(this->m0 + this->mean_motion * sim_sec, 2.0 * M_PI);
        double E = M;
        for (int iter = 0; iter < 15; ++iter)
        {
            double f = E - this->e * std::sin(E) - M;
            double f_prime = 1.0 - this->e * std::cos(E);
            double delta = -f / f_prime;
            E += delta;
            if (std::abs(delta) < 1e-9) break;
        }

        // 2. Anomalia Verdadeira e Raio Polar PQW
        double sin_nu = (std::sqrt(1.0 - this->e * this->e) * std::sin(E)) / (1.0 - this->e * std::cos(E));
        double cos_nu = (std::cos(E) - this->e) / (1.0 - this->e * std::cos(E));
        double nu = std::atan2(sin_nu, cos_nu);

        double r = this->a * (1.0 - this->e * std::cos(E));
        double p_x = r * std::cos(nu);
        double p_y = r * std::sin(nu);

        // 3. Matriz de Rotação Orbital (Perifocal -> ECI Inercial)
        double cos_O = std::cos(this->raan), sin_O = std::sin(this->raan);
        double cos_w = std::cos(this->argp), sin_w = std::sin(this->argp);
        double cos_i = std::cos(this->inc),  sin_i = std::sin(this->inc);

        double P_x = cos_O * cos_w - sin_O * sin_w * cos_i;
        double P_y = sin_O * cos_w + cos_O * sin_w * cos_i;
        double P_z = sin_w * sin_i;

        double Q_x = -cos_O * sin_w - sin_O * cos_w * cos_i;
        double Q_y = -sin_O * sin_w + cos_O * cos_w * cos_i;
        double Q_z = cos_w * sin_i;

        double eci_x = p_x * P_x + p_y * Q_x;
        double eci_y = p_x * P_y + p_y * Q_y;
        double eci_z = p_x * P_z + p_y * Q_z;

        // 4. Se for Heliocêntrico, translada com a Terra ao redor do Sol
        if (this->heliocentric)
        {
            double theta_earth_orbit = OMEGA_EARTH_ORBIT * sim_sec;
            eci_x += DIST_SUN_EARTH * std::cos(theta_earth_orbit);
            eci_y += DIST_SUN_EARTH * std::sin(theta_earth_orbit);
        }

        // 5. Apontamento de Atitude Nadir (Eixo Z apontando para o centro da Terra)
        gz::math::Vector3d earth_center(0, 0, 0);
        if (this->heliocentric)
        {
            double theta_earth_orbit = OMEGA_EARTH_ORBIT * sim_sec;
            earth_center.Set(DIST_SUN_EARTH * std::cos(theta_earth_orbit),
                             DIST_SUN_EARTH * std::sin(theta_earth_orbit),
                             0.0);
        }
        gz::math::Vector3d sat_pos(eci_x, eci_y, eci_z);
        gz::math::Vector3d to_earth = (earth_center - sat_pos).Normalized();

        gz::math::Quaterniond nadir_orientation;
        nadir_orientation.SetFrom2Axes(gz::math::Vector3d(0, 0, 1), to_earth);

        // 6. Atualização da Pose no ECS
        auto poseComp = _ecm.Component<gz::sim::components::Pose>(this->model.Entity());
        if (poseComp)
        {
            *poseComp = gz::sim::components::Pose(gz::math::Pose3d(sat_pos, nadir_orientation));
            _ecm.SetChanged(this->model.Entity(), gz::sim::components::Pose::typeId, gz::sim::ComponentState::PeriodicChange);
        }
    }
};

} // namespace brazilian_rps

GZ_ADD_PLUGIN(brazilian_rps::OrbitalMotionPlugin,
              gz::sim::System,
              brazilian_rps::OrbitalMotionPlugin::ISystemConfigure,
              brazilian_rps::OrbitalMotionPlugin::ISystemPreUpdate)

GZ_ADD_PLUGIN_ALIAS(brazilian_rps::OrbitalMotionPlugin,
                    "brazilian_rps::OrbitalMotionPlugin")
