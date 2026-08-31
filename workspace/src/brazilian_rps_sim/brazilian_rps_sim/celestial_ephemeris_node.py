#!/usr/bin/env python3
"""
Nó ROS 2 para cálculo e publicação analítica de efemérides astronômicas (Sol, Terra, Lua)
100% sincronizado com o relógio de simulação do Gazebo (use_sim_time: True).
"""

import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, TransformStamped
from tf2_ros import TransformBroadcaster
from std_msgs.msg import String

# Constantes Astronômicas
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

        self.declare_parameter('time_multiplier', 1.0) # Base 1:1 sincronizada com o simulador
        self.time_mult = self.get_parameter('time_multiplier').get_parameter_value().double_value

        self.tf_broadcaster = TransformBroadcaster(self)

        # Publicadores
        self.earth_pose_pub = self.create_publisher(PoseStamped, '/celestial/earth/pose', 10)
        self.moon_pose_pub = self.create_publisher(PoseStamped, '/celestial/moon/pose', 10)
        self.sun_pose_pub = self.create_publisher(PoseStamped, '/celestial/sun/pose', 10)
        self.moon_phase_pub = self.create_publisher(String, '/celestial/moon/phase', 10)
        self.summary_pub = self.create_publisher(String, '/celestial/summary', 10)

        self.last_log_sec = -1.0
        self.timer = self.create_timer(0.05, self.ephemeris_step) # 20 Hz sincronizado

        self.get_logger().info("🌌 [Mecânica Celeste] Sol-Terra-Lua ativo e sincronizado com o Gazebo (Tempo Real 1:1)")

    def ephemeris_step(self):
        now_time = self.get_clock().now()
        sim_time_sec = now_time.nanoseconds * 1e-9 * self.time_mult
        now_stamp = now_time.to_msg()

        # 1. Posição da Terra ao redor do Sol (Heliocêntrico)
        theta_earth = OMEGA_EARTH_ORBIT * sim_time_sec
        dist_sun_earth_render = 1200.0

        earth_x = dist_sun_earth_render * math.cos(theta_earth)
        earth_y = dist_sun_earth_render * math.sin(theta_earth)
        earth_z = 0.0

        # Rotação e inclinação da Terra
        earth_spin_deg = math.degrees((OMEGA_EARTH_SPIN * sim_time_sec) % (2.0 * math.pi))
        earth_spin_rad = math.radians(earth_spin_deg)

        qx = math.sin(OBLIQUITY_EARTH_RAD / 2.0) * math.cos(earth_spin_rad / 2.0)
        qy = -math.sin(OBLIQUITY_EARTH_RAD / 2.0) * math.sin(earth_spin_rad / 2.0)
        qz = math.cos(OBLIQUITY_EARTH_RAD / 2.0) * math.sin(earth_spin_rad / 2.0)
        qw = math.cos(OBLIQUITY_EARTH_RAD / 2.0) * math.cos(earth_spin_rad / 2.0)

        # 2. Posição da Lua (Geocêntrica + Heliocêntrica)
        theta_moon = OMEGA_MOON_ORBIT * sim_time_sec
        dist_earth_moon_render = 384.4

        moon_rel_x = dist_earth_moon_render * math.cos(theta_moon)
        moon_rel_y = dist_earth_moon_render * math.sin(theta_moon) * math.cos(INCLINATION_MOON_RAD)
        moon_rel_z = dist_earth_moon_render * math.sin(theta_moon) * math.sin(INCLINATION_MOON_RAD)

        moon_abs_x = earth_x + moon_rel_x
        moon_abs_y = earth_y + moon_rel_y
        moon_abs_z = earth_z + moon_rel_z

        # 3. Fase da Lua
        moon_elongation = (theta_moon - theta_earth) % (2.0 * math.pi)
        illumination_frac = (1.0 - math.cos(moon_elongation)) / 2.0 * 100.0

        elong_deg = math.degrees(moon_elongation)
        if elong_deg < 22.5 or elong_deg >= 337.5:
            phase_name = "Lua Nova"
        elif 22.5 <= elong_deg < 67.5:
            phase_name = "Lua Crescente Inicial"
        elif 67.5 <= elong_deg < 112.5:
            phase_name = "Quarto Crescente"
        elif 112.5 <= elong_deg < 157.5:
            phase_name = "Gibosa Crescente"
        elif 157.5 <= elong_deg < 202.5:
            phase_name = "Lua Cheia"
        elif 202.5 <= elong_deg < 247.5:
            phase_name = "Gibosa Minguante"
        elif 247.5 <= elong_deg < 292.5:
            phase_name = "Quarto Minguante"
        else:
            phase_name = "Lua Minguante"

        # Publicações ROS 2
        msg_earth = PoseStamped()
        msg_earth.header.stamp = now_stamp
        msg_earth.header.frame_id = 'sun_frame'
        msg_earth.pose.position.x = earth_x
        msg_earth.pose.position.y = earth_y
        msg_earth.pose.position.z = earth_z
        msg_earth.pose.orientation.x = qx
        msg_earth.pose.orientation.y = qy
        msg_earth.pose.orientation.z = qz
        msg_earth.pose.orientation.w = qw
        self.earth_pose_pub.publish(msg_earth)

        msg_moon = PoseStamped()
        msg_moon.header.stamp = now_stamp
        msg_moon.header.frame_id = 'earth_frame'
        msg_moon.pose.position.x = moon_rel_x
        msg_moon.pose.position.y = moon_rel_y
        msg_moon.pose.position.z = moon_rel_z
        msg_moon.pose.orientation.w = 1.0
        self.moon_pose_pub.publish(msg_moon)

        msg_phase = String()
        msg_phase.data = f"{phase_name} ({illumination_frac:.1f}%)"
        self.moon_phase_pub.publish(msg_phase)

        # Log periódico a cada 5 segundos de simTime
        if sim_time_sec - self.last_log_sec >= 5.0 or self.last_log_sec < 0:
            self.last_log_sec = sim_time_sec
            days = sim_time_sec / 86400.0
            self.get_logger().info(
                f"⏱️ [Tempo Simulado] {sim_time_sec:.1f}s (Dia {days:.3f}) | Terra: {earth_spin_deg:.1f}° | Lua: {phase_name} ({illumination_frac:.0f}%)"
            )

def main(args=None):
    rclpy.init(args=args)
    node = CelestialEphemerisNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()

if __name__ == '__main__':
    main()
