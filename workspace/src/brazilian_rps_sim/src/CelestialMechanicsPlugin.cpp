/**
 * @file CelestialMechanicsPlugin.cpp
 * @brief Plugin C++ do Gazebo Harmonic para simulação analítica da Mecânica Celeste Sol-Terra-Lua
 *        com suporte total a avanço por passos discretos (Stepping) e reprodução contínua.
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
#include <string>

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
        if (_sdf->HasElement("time_scale"))
            this->time_scale = _sdf->Get<double>("time_scale");

        std::cout << "🌌 [CelestialPlugin] Entidade '" << this->model.Name(_ecm) 
                  << "' configurada como: " << this->body_type 
                  << " (Aceleração: " << this->time_scale << "x)\n";
    }

    void PreUpdate(const gz::sim::UpdateInfo &_info,
                   gz::sim::EntityComponentManager &_ecm) override
    {
        // Executa sempre que o tempo de simulação avançar (seja em Play contínuo ou por botão Step!)
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

        // 2. Rotação Própria da Terra (Eixo Inclinado a 23.44°)
        double earth_spin_angle = std::fmod(OMEGA_EARTH_SPIN * sim_sec, 2.0 * M_PI);
        double eps = OBLIQUITY_EARTH_DEG * M_PI / 180.0;
        gz::math::Quaterniond q_tilt(eps, 0.0, 0.0);
        gz::math::Quaterniond q_spin(0.0, 0.0, earth_spin_angle);
        gz::math::Quaterniond q_earth = q_tilt * q_spin;

        // 3. Rotação Zonal das Nuvens (+3.5% Super-rotação)
        double clouds_spin_angle = std::fmod(OMEGA_CLOUDS_SPIN * sim_sec, 2.0 * M_PI);
        gz::math::Quaterniond q_cloud_spin(0.0, 0.0, clouds_spin_angle);
        gz::math::Quaterniond q_clouds = q_tilt * q_cloud_spin;

        // 4. Órbita Geocêntrica da Lua
        double theta_moon_orbit = OMEGA_MOON_ORBIT * sim_sec;
        double inc_moon = INCLINATION_MOON_DEG * M_PI / 180.0;

        double moon_rel_x = DIST_EARTH_MOON * std::cos(theta_moon_orbit);
        double moon_rel_y = DIST_EARTH_MOON * std::sin(theta_moon_orbit) * std::cos(inc_moon);
        double moon_rel_z = DIST_EARTH_MOON * std::sin(theta_moon_orbit) * std::sin(inc_moon);

        double moon_x = earth_x + moon_rel_x;
        double moon_y = earth_y + moon_rel_y;
        double moon_z = earth_z + moon_rel_z;

        // 5. Travamento de Maré da Lua
        double moon_yaw = std::atan2(-moon_rel_y, -moon_rel_x);
        gz::math::Quaterniond q_moon(0.0, inc_moon, moon_yaw);

        // 6. Determinação da Pose Alvo
        gz::math::Pose3d target_pose;
        if (this->body_type == "earth")
        {
            target_pose = gz::math::Pose3d(gz::math::Vector3d(earth_x, earth_y, earth_z), q_earth);
        }
        else if (this->body_type == "earth_clouds")
        {
            target_pose = gz::math::Pose3d(gz::math::Vector3d(earth_x, earth_y, earth_z), q_clouds);
        }
        else if (this->body_type == "moon")
        {
            target_pose = gz::math::Pose3d(gz::math::Vector3d(moon_x, moon_y, moon_z), q_moon);
        }
        else if (this->body_type == "moon_trail")
        {
            target_pose = gz::math::Pose3d(gz::math::Vector3d(earth_x, earth_y, earth_z), gz::math::Quaterniond::Identity);
        }
        else if (this->body_type == "earth_trail" || this->body_type == "sun")
        {
            target_pose = gz::math::Pose3d(gz::math::Vector3d(0.0, 0.0, 0.0), gz::math::Quaterniond::Identity);
        }

        // 7. Atualização no ECM
        auto poseComp = _ecm.Component<gz::sim::components::Pose>(this->model.Entity());
        if (poseComp)
        {
            *poseComp = gz::sim::components::Pose(target_pose);
            _ecm.SetChanged(this->model.Entity(), gz::sim::components::Pose::typeId, gz::sim::ComponentState::PeriodicChange);
        }
    }
};

} // namespace celestial_sim

GZ_ADD_PLUGIN(celestial_sim::CelestialMechanicsPlugin,
              gz::sim::System,
              celestial_sim::CelestialMechanicsPlugin::ISystemConfigure,
              celestial_sim::CelestialMechanicsPlugin::ISystemPreUpdate)

GZ_ADD_PLUGIN_ALIAS(celestial_sim::CelestialMechanicsPlugin, "celestial_sim::CelestialMechanicsPlugin")
