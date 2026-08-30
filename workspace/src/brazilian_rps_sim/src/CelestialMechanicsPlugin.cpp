/**
 * @file CelestialMechanicsPlugin.cpp
 * @brief Plugin C++ do Gazebo Harmonic para simulação analítica da Mecânica Celeste Sol-Terra-Lua.
 * 
 * Funcionalidades:
 * - Propagação Kepleriana heliocêntrica da Terra com rotação sidérea inclinada a 23.44°.
 * - Propagação geocêntrica da Lua com plano orbital inclinado a 5.145° e travamento de maré (Tidal Locking).
 * - Sincronização e translação rígida dos anéis 3D glTF de órbita.
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

// =============================================================================
// Constantes Astronômicas Fundamentais (Escala: 1 unidade = 1.000 km)
// =============================================================================
constexpr double R_EARTH_KM = 6.378137;          // Raio médio equatorial da Terra (6.378 km)
constexpr double R_MOON_KM = 1.7374;             // Raio médio da Lua (1.737 km)
constexpr double R_SUN_KM = 45.0;                // Escala visual representativa do Sol
constexpr double DIST_EARTH_MOON = 384.4;        // Semieixo maior da órbita lunar (384.400 km)
constexpr double DIST_SUN_EARTH = 1200.0;        // Distância representativa Sol-Terra

// Períodos e Frequências Angulares
constexpr double SECONDS_PER_DAY = 86164.0905;   // Dia Sidéreo da Terra (s)
constexpr double SECONDS_PER_MONTH = 27.321661 * 86400.0; // Mês Sidéreo Lunar (s)
constexpr double SECONDS_PER_YEAR = 365.256363 * 86400.0; // Ano Sideral da Terra (s)

constexpr double OMEGA_EARTH_SPIN = 2.0 * M_PI / SECONDS_PER_DAY;
constexpr double OMEGA_MOON_ORBIT = 2.0 * M_PI / SECONDS_PER_MONTH;
constexpr double OMEGA_EARTH_ORBIT = 2.0 * M_PI / SECONDS_PER_YEAR;

constexpr double OBLIQUITY_EARTH_DEG = 23.43928; // Obliqüidade da Eclíptica (23.44°)
constexpr double INCLINATION_MOON_DEG = 5.145;   // Inclinação orbital da Lua em relação à Eclíptica (5.145°)

/**
 * @class CelestialMechanicsPlugin
 * @brief Atualiza a cada passo de física a posição e orientação dos corpos celestes e trilhas.
 */
class CelestialMechanicsPlugin : public gz::sim::System,
                                public gz::sim::ISystemConfigure,
                                public gz::sim::ISystemPreUpdate
{
private:
    gz::sim::Model model{gz::sim::kNullEntity};
    std::string body_type{"earth"}; // Opções: "sun", "earth", "moon", "moon_trail", "earth_trail"
    double time_scale{86400.0};     // Escala de tempo: 1s real = 1 dia simulado (86.400x)

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
        if (_info.paused)
            return;

        // Tempo sideral simulado acumulado (em segundos)
        double sim_sec = std::chrono::duration<double>(_info.simTime).count() * this->time_scale;

        // 1. Órbita Heliocêntrica da Terra (Plano da Eclíptica Z = 0)
        double theta_earth_orbit = OMEGA_EARTH_ORBIT * sim_sec;
        double earth_x = DIST_SUN_EARTH * std::cos(theta_earth_orbit);
        double earth_y = DIST_SUN_EARTH * std::sin(theta_earth_orbit);
        double earth_z = 0.0;

        // 2. Rotação Própria da Terra (Eixo Inclinado a 23.44° com Spin Diário)
        double earth_spin_angle = std::fmod(OMEGA_EARTH_SPIN * sim_sec, 2.0 * M_PI);
        double eps = OBLIQUITY_EARTH_DEG * M_PI / 180.0;
        gz::math::Quaterniond q_tilt(eps, 0.0, 0.0);
        gz::math::Quaterniond q_spin(0.0, 0.0, earth_spin_angle);
        gz::math::Quaterniond q_earth = q_tilt * q_spin;

        // 3. Órbita Geocêntrica da Lua (Inclinada a 5.145° em relação à Eclíptica)
        double theta_moon_orbit = OMEGA_MOON_ORBIT * sim_sec;
        double inc_moon = INCLINATION_MOON_DEG * M_PI / 180.0;

        double moon_rel_x = DIST_EARTH_MOON * std::cos(theta_moon_orbit);
        double moon_rel_y = DIST_EARTH_MOON * std::sin(theta_moon_orbit) * std::cos(inc_moon);
        double moon_rel_z = DIST_EARTH_MOON * std::sin(theta_moon_orbit) * std::sin(inc_moon);

        double moon_x = earth_x + moon_rel_x;
        double moon_y = earth_y + moon_rel_y;
        double moon_z = earth_z + moon_rel_z;

        // 4. Travamento de Maré da Lua (Face Lunar sempre voltada para o centro da Terra)
        double moon_yaw = std::atan2(-moon_rel_y, -moon_rel_x);
        gz::math::Quaterniond q_moon(0.0, inc_moon, moon_yaw);

        // 5. Determinação da Pose Alvo com Álgebra Estrita de Quaternions
        gz::math::Pose3d target_pose;
        if (this->body_type == "earth")
        {
            target_pose = gz::math::Pose3d(gz::math::Vector3d(earth_x, earth_y, earth_z), q_earth);
        }
        else if (this->body_type == "moon")
        {
            target_pose = gz::math::Pose3d(gz::math::Vector3d(moon_x, moon_y, moon_z), q_moon);
        }
        else if (this->body_type == "moon_trail")
        {
            // O anel 3D translada rigidamente com o centro da Terra
            target_pose = gz::math::Pose3d(gz::math::Vector3d(earth_x, earth_y, earth_z), gz::math::Quaterniond::Identity);
        }
        else if (this->body_type == "earth_trail" || this->body_type == "sun")
        {
            // Fixos na origem do Sistema Solar
            target_pose = gz::math::Pose3d(gz::math::Vector3d(0.0, 0.0, 0.0), gz::math::Quaterniond::Identity);
        }

        // 6. Atualização de Pose no Entity Component Manager (ECM)
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
