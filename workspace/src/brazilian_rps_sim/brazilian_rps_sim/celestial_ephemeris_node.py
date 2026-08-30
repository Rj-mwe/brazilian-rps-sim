#!/usr/bin/env python3
"""
Nó ROS 2: Efemérides e Mecânica Celeste do Sistema Sol-Terra-Lua
Transmite poses 3D, fases da Lua e estado de rotação terrestre em tempo real.
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, TransformStamped
from std_msgs.msg import String, Float64
from tf2_ros import TransformBroadcaster

import math
import time
import json

# Constantes Astronômicas
DIST_EARTH_MOON_KM = 384400.0
DIST_SUN_EARTH_KM = 149597870.7
R_EARTH_KM = 6378.137
R_MOON_KM = 1737.4
R_SUN_KM = 696340.0

SECONDS_PER_DAY = 86164.0905
SECONDS_PER_MONTH = 27.321661 * 86400.0
SECONDS_PER_YEAR = 365.256363 * 86400.0
SYNODIC_MONTH = 29.530589 * 86400.0 # Período das Fases da Lua

OMEGA_EARTH_SPIN = 2.0 * math.pi / SECONDS_PER_DAY
OMEGA_MOON_ORBIT = 2.0 * math.pi / SECONDS_PER_MONTH
OMEGA_EARTH_ORBIT = 2.0 * math.pi / SECONDS_PER_YEAR
OBLIQUITY_EARTH_RAD = math.radians(23.43928)
INCLINATION_MOON_RAD = math.radians(5.145)

class CelestialEphemerisNode(Node):
    def __init__(self):
        super().__init__('celestial_ephemeris_node')

        self.declare_parameter('time_multiplier', 86400.0) # 1s real = 1 dia simulado (86400x)
        self.time_mult = self.get_parameter('time_multiplier').get_parameter_value().double_value

        self.tf_broadcaster = TransformBroadcaster(self)

        # Publicadores
        self.earth_pose_pub = self.create_publisher(PoseStamped, '/celestial/earth/pose', 10)
        self.moon_pose_pub = self.create_publisher(PoseStamped, '/celestial/moon/pose', 10)
        self.sun_pose_pub = self.create_publisher(PoseStamped, '/celestial/sun/pose', 10)
        self.moon_phase_pub = self.create_publisher(String, '/celestial/moon/phase', 10)
        self.summary_pub = self.create_publisher(String, '/celestial/summary', 10)

        self.sim_time_sec = 0.0
        self.last_wall_time = time.time()
        self.last_log_day = -1
        self.timer = self.create_timer(0.05, self.ephemeris_step) # 20 Hz

        self.get_logger().info(f"🌌 [Mecânica Celeste] Sol-Terra-Lua ativo! (1s real = 1 dia simulado)")

    def ephemeris_step(self):
        now_wall = time.time()
        dt_wall = now_wall - self.last_wall_time
        self.last_wall_time = now_wall

        self.sim_time_sec += dt_wall * self.time_mult
        now_stamp = self.get_clock().now().to_msg()

        # 1. Posição da Terra ao redor do Sol (Heliocêntrico)
        theta_earth = OMEGA_EARTH_ORBIT * self.sim_time_sec
        dist_sun_earth_render = 1200.0

        earth_x = dist_sun_earth_render * math.cos(theta_earth)
        earth_y = dist_sun_earth_render * math.sin(theta_earth)
        earth_z = 0.0

        # Rotação e inclinação da Terra
        earth_spin_deg = math.degrees((OMEGA_EARTH_SPIN * self.sim_time_sec) % (2.0 * math.pi))

        # 2. Posição da Lua ao redor da Terra
        theta_moon = OMEGA_MOON_ORBIT * self.sim_time_sec
        dist_moon_render = 384.4

        moon_rel_x = dist_moon_render * math.cos(theta_moon)
        moon_rel_y = dist_moon_render * math.sin(theta_moon) * math.cos(INCLINATION_MOON_RAD)
        moon_rel_z = dist_moon_render * math.sin(theta_moon) * math.sin(INCLINATION_MOON_RAD)

        # 3. Fase da Lua (Ângulo de elongação Sol-Terra-Lua)
        synodic_phase_angle = ((self.sim_time_sec % SYNODIC_MONTH) / SYNODIC_MONTH) * 360.0
        phase_name = self.get_moon_phase_name(synodic_phase_angle)
        illumination_pct = 0.5 * (1.0 - math.cos(math.radians(synodic_phase_angle))) * 100.0

        # 4. Publicação das Poses
        earth_pose = PoseStamped()
        earth_pose.header.stamp = now_stamp
        earth_pose.header.frame_id = "sun_center"
        earth_pose.pose.position.x = earth_x
        earth_pose.pose.position.y = earth_y
        earth_pose.pose.position.z = earth_z
        earth_pose.pose.orientation.w = 1.0
        self.earth_pose_pub.publish(earth_pose)

        moon_pose = PoseStamped()
        moon_pose.header.stamp = now_stamp
        moon_pose.header.frame_id = "earth_center"
        moon_pose.pose.position.x = moon_rel_x
        moon_pose.pose.position.y = moon_rel_y
        moon_pose.pose.position.z = moon_rel_z
        moon_pose.pose.orientation.w = 1.0
        self.moon_pose_pub.publish(moon_pose)

        # 5. Resumo e Calendário Astronômico
        days_sim = self.sim_time_sec / 86400.0
        years_sim = days_sim / 365.25
        
        summary_data = {
            "calendario_simulado": {
                "dias_decorridos": round(days_sim, 2),
                "anos_decorridos": round(years_sim, 3),
                "voltas_terra_spin": round(days_sim, 1),
                "rotacao_graus": round(earth_spin_deg, 1)
            },
            "lua": {
                "fase": phase_name,
                "iluminacao_pct": round(illumination_pct, 1),
                "distancia_km": DIST_EARTH_MOON_KM
            }
        }
        sum_msg = String()
        sum_msg.data = json.dumps(summary_data)
        self.summary_pub.publish(sum_msg)

        # Log periódico a cada 5 dias simulados
        curr_int_day = int(days_sim)
        if curr_int_day > self.last_log_day and curr_int_day % 5 == 0:
            self.last_log_day = curr_int_day
            self.get_logger().info(
                f"⏱️ [Tempo Astronômico] Dia {days_sim:.1f} ({years_sim:.2f} anos) | "
                f"Terra: {days_sim:.1f} rotações diárias | Lua: {phase_name} ({illumination_pct:.0f}%)"
            )

    def get_moon_phase_name(self, angle_deg: float) -> str:
        if angle_deg < 22.5 or angle_deg >= 337.5:
            return "Lua Nova"
        elif 22.5 <= angle_deg < 67.5:
            return "Lua Crescente"
        elif 67.5 <= angle_deg < 112.5:
            return "Quarto Crescente"
        elif 112.5 <= angle_deg < 157.5:
            return "Gibosa Crescente"
        elif 157.5 <= angle_deg < 202.5:
            return "Lua Cheia"
        elif 202.5 <= angle_deg < 247.5:
            return "Gibosa Minguante"
        elif 247.5 <= angle_deg < 292.5:
            return "Quarto Minguante"
        else:
            return "Lua Minguante"

def main(args=None):
    rclpy.init(args=args)
    node = CelestialEphemerisNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
