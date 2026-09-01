/**
 * @file CelestialMechanicsPlugin.cpp
 * @brief Plugin C++ do Gazebo Harmonic para simulação analítica da Mecânica Celeste Sol-Terra-Lua
 *        com rotação polar acoplada (q_tilt * q_spin), anéis orbitais e Injeção de Dependências via SDFormat.
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

class CelestialMechanicsPlugin : public gz::sim::System,
                                public gz::sim::ISystemConfigure,
                                public gz::sim::ISystemPreUpdate
{
private:
    gz::sim::Model model{gz::sim::kNullEntity};
    std::string body_type{"earth"};

    // 💉 Parâmetros Injetados via SDFormat (Dependency Injection)
    double time_scale{3600.0};
    double dist_sun_earth{1200.0};
    double dist_earth_moon{384.4};
    double obliquity_earth_deg{23.43928};
    double clouds_drift_factor{1.035};
    double sidereal_day_sec{86164.0905};
    double sidereal_year_sec{31558149.76};
    double sidereal_month_sec{2360591.51};
    double inclination_moon_deg{5.145};

    // Velocidades Angulares Derivadas
    double omega_earth_spin{0.0};
    double omega_clouds_spin{0.0};
    double omega_moon_orbit{0.0};
    double omega_earth_orbit{0.0};

    std::chrono::steady_clock::duration last_sim_time{std::chrono::steady_clock::duration::min()};

public:
    void Configure(const gz::sim::Entity &_entity,
                   const std::shared_ptr<const sdf::Element> &_sdf,
                   gz::sim::EntityComponentManager &_ecm,
                   gz::sim::EventManager &/*_eventMgr*/) override
    {
        this->model = gz::sim::Model(_entity);

        // Leitura limpa das dependências injetadas pelo SDFormat
        if (_sdf->HasElement("body_type"))
            this->body_type = _sdf->Get<std::string>("body_type");
        if (_sdf->HasElement("time_scale"))
            this->time_scale = _sdf->Get<double>("time_scale");
        if (_sdf->HasElement("dist_sun_earth"))
            this->dist_sun_earth = _sdf->Get<double>("dist_sun_earth");
        if (_sdf->HasElement("dist_earth_moon"))
            this->dist_earth_moon = _sdf->Get<double>("dist_earth_moon");
        if (_sdf->HasElement("obliquity_deg"))
            this->obliquity_earth_deg = _sdf->Get<double>("obliquity_deg");
        if (_sdf->HasElement("clouds_drift_factor"))
            this->clouds_drift_factor = _sdf->Get<double>("clouds_drift_factor");
        if (_sdf->HasElement("sidereal_day_sec"))
            this->sidereal_day_sec = _sdf->Get<double>("sidereal_day_sec");
        if (_sdf->HasElement("sidereal_year_sec"))
            this->sidereal_year_sec = _sdf->Get<double>("sidereal_year_sec");
        if (_sdf->HasElement("sidereal_month_sec"))
            this->sidereal_month_sec = _sdf->Get<double>("sidereal_month_sec");
        if (_sdf->HasElement("moon_inclination_deg"))
            this->inclination_moon_deg = _sdf->Get<double>("moon_inclination_deg");

        // Cálculo determinístico das velocidades angulares com base nos parâmetros injetados
        this->omega_earth_spin = 2.0 * M_PI / this->sidereal_day_sec;
        this->omega_clouds_spin = this->omega_earth_spin * this->clouds_drift_factor;
        this->omega_moon_orbit = 2.0 * M_PI / this->sidereal_month_sec;
        this->omega_earth_orbit = 2.0 * M_PI / this->sidereal_year_sec;

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
        double theta_earth_orbit = this->omega_earth_orbit * sim_sec;
        double cos_orbit = std::cos(theta_earth_orbit);
        double sin_orbit = std::sin(theta_earth_orbit);
        double earth_x = this->dist_sun_earth * cos_orbit;
        double earth_y = this->dist_sun_earth * sin_orbit;
        double earth_z = 0.0;

        // 2. Rotação Própria da Terra em torno do Polo Inclinado a 23.44° (q_tilt * q_spin)
        double theta_earth_spin = std::fmod(this->omega_earth_spin * sim_sec, 2.0 * M_PI);
        double eps = this->obliquity_earth_deg * M_PI / 180.0;
        gz::math::Quaterniond q_tilt(eps, 0.0, 0.0);
        gz::math::Quaterniond q_spin(0.0, 0.0, theta_earth_spin);
        gz::math::Quaterniond q_earth_axial = q_tilt * q_spin;

        // 3. Rotação das Nuvens (Super-rotação com drift configurável)
        double theta_clouds_spin = std::fmod(this->omega_clouds_spin * sim_sec, 2.0 * M_PI);
        gz::math::Quaterniond q_clouds_spin(0.0, 0.0, theta_clouds_spin);
        gz::math::Quaterniond q_clouds_axial = q_tilt * q_clouds_spin;

        // 4. Órbita Lunar ao redor da Terra
        double theta_moon = this->omega_moon_orbit * sim_sec;
        double i_moon = this->inclination_moon_deg * M_PI / 180.0;
        double moon_rel_x = this->dist_earth_moon * std::cos(theta_moon);
        double moon_rel_y = this->dist_earth_moon * std::sin(theta_moon) * std::cos(i_moon);
        double moon_rel_z = this->dist_earth_moon * std::sin(theta_moon) * std::sin(i_moon);

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
        else if (this->body_type == "constellation_geo_ring")
        {
            pose.Set(gz::math::Vector3d(earth_x, earth_y, earth_z), q_tilt);
        }
        else if (this->body_type == "constellation_igso_trail")
        {
            pose.Set(gz::math::Vector3d(earth_x, earth_y, earth_z), q_earth_axial);
        }
        else if (this->body_type == "moon")
        {
            pose.Set(gz::math::Vector3d(earth_x + moon_rel_x, earth_y + moon_rel_y, earth_z + moon_rel_z),
                     gz::math::Quaterniond::Identity);
        }
        else if (this->body_type == "moon_trail")
        {
            pose.Set(gz::math::Vector3d(earth_x, earth_y, earth_z),
                     gz::math::Quaterniond::Identity);
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
