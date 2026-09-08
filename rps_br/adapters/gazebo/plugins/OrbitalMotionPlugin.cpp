/**
 * @file OrbitalMotionPlugin.cpp
 * @brief Plugin C++ do Gazebo Harmonic para simulação analítica dos satélites do RPS-BR
 *        com Injeção de Dependências via SDFormat e alinhamento geométrico perfeito (Rx(eps)).
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
#include <string>

namespace brazilian_rps
{

class OrbitalMotionPlugin : public gz::sim::System,
                            public gz::sim::ISystemConfigure,
                            public gz::sim::ISystemPreUpdate
{
private:
    gz::sim::Model model{gz::sim::kNullEntity};
    
    // 💉 Parâmetros Orbitais e Astronômicos Injetados via SDFormat (Dependency Injection)
    double a{42.16414};                 // Semieixo maior em escala (1 unid = 1.000 km)
    double e{0.04};                     // Excentricidade orbital
    double inc{25.0 * M_PI / 180.0};    // Inclinação orbital (rad)
    double raan{42.0 * M_PI / 180.0};   // Longitude do Nó Ascendente - RAAN (rad)
    double argp{90.0 * M_PI / 180.0};   // Argumento do Perigeu (rad)
    double m0{180.0 * M_PI / 180.0};    // Anomalia Média inicial (rad)
    double time_scale{3600.0};          // Fator de aceleração temporal
    bool heliocentric{true};            // Translação heliocêntrica com a Terra
    double dist_sun_earth{1200.0};      // Distância Sol-Terra no mundo
    double obliquity_earth_deg{23.43928}; // Obliquidade da Terra (23.44°)
    double sidereal_year_sec{31558149.76};
    double sidereal_day_sec{86164.0905};

    // Velocidades Angulares Derivadas
    double mean_motion{7.292115e-5};    // Velocidade angular orbital média (rad/s)
    double omega_earth_orbit{0.0};      // Velocidade angular de translação heliocêntrica

    std::chrono::steady_clock::duration last_sim_time{std::chrono::steady_clock::duration::min()};

public:
    void Configure(const gz::sim::Entity &_entity,
                   const std::shared_ptr<const sdf::Element> &_sdf,
                   gz::sim::EntityComponentManager &_ecm,
                   gz::sim::EventManager &/*_eventMgr*/) override
    {
        this->model = gz::sim::Model(_entity);

        // Leitura limpa das dependências injetadas pelo SDFormat
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
        if (_sdf->HasElement("heliocentric"))
            this->heliocentric = _sdf->Get<bool>("heliocentric");
        if (_sdf->HasElement("dist_sun_earth"))
            this->dist_sun_earth = _sdf->Get<double>("dist_sun_earth");
        if (_sdf->HasElement("obliquity_deg"))
            this->obliquity_earth_deg = _sdf->Get<double>("obliquity_deg");
        if (_sdf->HasElement("sidereal_year_sec"))
            this->sidereal_year_sec = _sdf->Get<double>("sidereal_year_sec");
        if (_sdf->HasElement("sidereal_day_sec"))
            this->sidereal_day_sec = _sdf->Get<double>("sidereal_day_sec");

        // Cálculo determinístico das velocidades com base nos parâmetros injetados
        this->mean_motion = 2.0 * M_PI / this->sidereal_day_sec;
        this->omega_earth_orbit = 2.0 * M_PI / this->sidereal_year_sec;

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

        // 2. Anomalia Verdadeira (nu) e Raio Orbital (r)
        double nu = 2.0 * std::atan2(std::sqrt(1.0 + this->e) * std::sin(E / 2.0),
                                     std::sqrt(1.0 - this->e) * std::cos(E / 2.0));
        double r = this->a * (1.0 - this->e * std::cos(E));

        // 3. Posição no Plano Orbital (Perifocal P-Q-W)
        double u = this->argp + nu; // Argumento de latitude
        double x_orb = r * std::cos(u);
        double y_orb = r * std::sin(u) * std::cos(this->inc);
        double z_orb = r * std::sin(u) * std::sin(this->inc);

        // 4. Rotação pelo Nó Ascendente (RAAN) -> Referencial Inercial Equatorial (ECI)
        double x_eci = x_orb * std::cos(this->raan) - y_orb * std::sin(this->raan);
        double y_eci = x_orb * std::sin(this->raan) + y_orb * std::cos(this->raan);
        double z_eci = z_orb;

        // 5. Rotação Equatorial -> Eclíptica do Gazebo (Obliquidade eps = 23.43928°)
        double eps = this->obliquity_earth_deg * M_PI / 180.0;
        double cos_eps = std::cos(eps), sin_eps = std::sin(eps);

        double rot_x = x_eci;
        double rot_y = y_eci * cos_eps - z_eci * sin_eps;
        double rot_z = y_eci * sin_eps + z_eci * cos_eps;

        // 6. Translação Heliocêntrica (Centro na Terra orbitando o Sol a 1.200 unidades)
        double earth_x = 0.0;
        double earth_y = 0.0;
        if (this->heliocentric)
        {
            double theta_earth_orbit = this->omega_earth_orbit * sim_sec;
            earth_x = this->dist_sun_earth * std::cos(theta_earth_orbit);
            earth_y = this->dist_sun_earth * std::sin(theta_earth_orbit);
            rot_x += earth_x;
            rot_y += earth_y;
        }

        gz::math::Vector3d sat_pos(rot_x, rot_y, rot_z);

        // 7. Apontamento de Atitude Nadir (Eixo Z apontando para o centro da Terra)
        gz::math::Vector3d earth_center(earth_x, earth_y, 0.0);
        gz::math::Vector3d to_earth = (earth_center - sat_pos).Normalized();

        gz::math::Quaterniond nadir_orientation;
        nadir_orientation.SetFrom2Axes(gz::math::Vector3d(0, 0, 1), to_earth);

        // 8. Atualização da Pose no ECS
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
