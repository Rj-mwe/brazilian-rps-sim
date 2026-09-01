/**
 * @file CelestialMechanicsPlugin.cpp
 * @brief Plugin C++ do Gazebo Harmonic para simulação analítica da Mecânica Celeste Sol-Terra-Lua
 *        com rotação polar acoplada (q_tilt * q_spin) e leitura declarativa de parâmetros via YAML.
 */

#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Util.hh>
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

namespace celestial_sim
{

// Constantes Astronômicas Heliocêntricas (Escala: 1 unidade = 1.000 km)
constexpr double DIST_EARTH_MOON = 384.4;        // Semieixo maior da órbita lunar (384.400 km)
constexpr double DIST_SUN_EARTH = 1200.0;        // Distância representativa Sol-Terra

constexpr double SECONDS_PER_DAY = 86164.0905;   // Dia Sidéreo da Terra (s)
constexpr double SECONDS_PER_MONTH = 27.321661 * 86400.0; // Mês Sidéreo Lunar (s)
constexpr double SECONDS_PER_YEAR = 365.256363 * 86400.0; // Ano Sideral da Terra (s)

constexpr double OMEGA_EARTH_SPIN = 2.0 * M_PI / SECONDS_PER_DAY;
constexpr double OMEGA_CLOUDS_SPIN = OMEGA_EARTH_SPIN * 1.035; 
constexpr double OMEGA_MOON_ORBIT = 2.0 * M_PI / SECONDS_PER_MONTH;
constexpr double OMEGA_EARTH_ORBIT = 2.0 * M_PI / SECONDS_PER_YEAR;

constexpr double OBLIQUITY_EARTH_DEG = 23.43928; // 23.44°
constexpr double INCLINATION_MOON_DEG = 5.145;   // 5.145°

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

class CelestialMechanicsPlugin : public gz::sim::System,
                                public gz::sim::ISystemConfigure,
                                public gz::sim::ISystemPreUpdate
{
private:
    gz::sim::Model model{gz::sim::kNullEntity};
    std::string body_type{"earth"};
    double time_scale{1.0};
    std::chrono::steady_clock::duration last_sim_time{std::chrono::steady_clock::duration::min()};

public:
    void Configure(const gz::sim::Entity &_entity,
                   const std::shared_ptr<const sdf::Element> &_sdf,
                   gz::sim::EntityComponentManager &_ecm,
                   gz::sim::EventManager &/*_eventMgr*/) override
    {
        this->model = gz::sim::Model(_entity);

        if (_sdf->HasElement("body_type"))
            this->body_type = _sdf->Get<std::string>("body_type");

        // Lê do simulation_parameters.yaml
        this->time_scale = load_time_multiplier_from_yaml();

        if (_sdf->HasElement("time_scale"))
        {
            double override_scale = _sdf->Get<double>("time_scale");
            if (override_scale != 1.0)
                this->time_scale = override_scale;
        }

        std::cout << "🌌 [CelestialPlugin] Entidade '" << this->model.Name(_ecm) 
                  << "' configurada como: " << this->body_type 
                  << " (Aceleração: " << this->time_scale << "x)\n";
    }

    void PreUpdate(const gz::sim::UpdateInfo &_info,
                   gz::sim::EntityComponentManager &_ecm) override
    {
        if (_info.simTime == this->last_sim_time)
            return;

        this->last_sim_time = _info.simTime;
        double sim_sec = std::chrono::duration<double>(_info.simTime).count() * this->time_scale;

        // 1. Órbita Heliocêntrica da Terra (Plano Z = 0)
        double theta_earth_orbit = OMEGA_EARTH_ORBIT * sim_sec;
        double cos_orbit = std::cos(theta_earth_orbit);
        double sin_orbit = std::sin(theta_earth_orbit);
        double earth_x = DIST_SUN_EARTH * cos_orbit;
        double earth_y = DIST_SUN_EARTH * sin_orbit;
        double earth_z = 0.0;

        // 2. Rotação Própria da Terra em torno do Polo Inclinado a 23.44° (q_tilt * q_spin)
        double theta_earth_spin = std::fmod(OMEGA_EARTH_SPIN * sim_sec, 2.0 * M_PI);
        double eps = OBLIQUITY_EARTH_DEG * M_PI / 180.0;
        gz::math::Quaterniond q_tilt(eps, 0.0, 0.0);
        gz::math::Quaterniond q_spin(0.0, 0.0, theta_earth_spin);
        gz::math::Quaterniond q_earth_axial = q_tilt * q_spin;

        // 3. Rotação das Nuvens (+3.5% Super-rotação)
        double theta_clouds_spin = std::fmod(OMEGA_CLOUDS_SPIN * sim_sec, 2.0 * M_PI);
        gz::math::Quaterniond q_clouds_spin(0.0, 0.0, theta_clouds_spin);
        gz::math::Quaterniond q_clouds_axial = q_tilt * q_clouds_spin;

        // 4. Órbita Lunar ao redor da Terra (Inclinada a 5.145°)
        double theta_moon = OMEGA_MOON_ORBIT * sim_sec;
        double i_moon = INCLINATION_MOON_DEG * M_PI / 180.0;
        double moon_rel_x = DIST_EARTH_MOON * std::cos(theta_moon);
        double moon_rel_y = DIST_EARTH_MOON * std::sin(theta_moon) * std::cos(i_moon);
        double moon_rel_z = DIST_EARTH_MOON * std::sin(theta_moon) * std::sin(i_moon);

        // 5. Aplicação da Pose no ECS
        gz::math::Pose3d pose;
        if (this->body_type == "earth")
        {
            pose.Set(gz::math::Vector3d(earth_x, earth_y, earth_z), q_earth_axial);
        }
        else if (this->body_type == "earth_clouds")
        {
            pose.Set(gz::math::Vector3d(earth_x, earth_y, earth_z), q_clouds_axial);
        }
        else if (this->body_type == "earth_trail")
        {
            pose.Set(gz::math::Vector3d(0.0, 0.0, 0.0), gz::math::Quaterniond::Identity);
        }
        else if (this->body_type == "moon")
        {
            pose.Set(gz::math::Vector3d(earth_x + moon_rel_x, earth_y + moon_rel_y, earth_z + moon_rel_z),
                     gz::math::Quaterniond::Identity);
        }
        else if (this->body_type == "moon_trail")
        {
            pose.Set(gz::math::Vector3d(earth_x, earth_y, earth_z),
                     gz::math::Quaterniond(i_moon, 0.0, 0.0));
        }
        else if (this->body_type == "sun")
        {
            pose.Set(gz::math::Vector3d(0.0, 0.0, 0.0), gz::math::Quaterniond::Identity);
        }

        auto poseComp = _ecm.Component<gz::sim::components::Pose>(this->model.Entity());
        if (poseComp)
        {
            *poseComp = gz::sim::components::Pose(pose);
            _ecm.SetChanged(this->model.Entity(), gz::sim::components::Pose::typeId, gz::sim::ComponentState::PeriodicChange);
        }
    }
};

} // namespace celestial_sim

GZ_ADD_PLUGIN(celestial_sim::CelestialMechanicsPlugin,
              gz::sim::System,
              celestial_sim::CelestialMechanicsPlugin::ISystemConfigure,
              celestial_sim::CelestialMechanicsPlugin::ISystemPreUpdate)

GZ_ADD_PLUGIN_ALIAS(celestial_sim::CelestialMechanicsPlugin,
                    "celestial_sim::CelestialMechanicsPlugin")
