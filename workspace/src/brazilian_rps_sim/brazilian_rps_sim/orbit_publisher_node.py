#!/usr/bin/env python3
"""
Nó ROS 2: Publicador de Telemetria Orbital para o Satélite GEO e o Satélite IGSO (Figura-8)
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, TransformStamped
from std_msgs.msg import String
from tf2_ros import TransformBroadcaster

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from brazilian_rps_sim.astrodynamics import (
        get_brazilian_rps_constellation,
        propagate_orbit_eci,
        eci_to_ecef,
        ecef_to_lat_lon_alt,
        compute_elevation_azimuth,
        R_EARTH
    )
except ImportError:
    from astrodynamics import (
        get_brazilian_rps_constellation,
        propagate_orbit_eci,
        eci_to_ecef,
        ecef_to_lat_lon_alt,
        compute_elevation_azimuth,
        R_EARTH
    )

import time
import json

class RPSOrbitPublisherNode(Node):
    def __init__(self):
        super().__init__('rps_orbit_publisher_node')

        self.declare_parameter('time_multiplier', 300.0)
        self.declare_parameter('render_scale', 1.0 / 1000.0)

        self.time_mult = self.get_parameter('time_multiplier').get_parameter_value().double_value
        self.scale = self.get_parameter('render_scale').get_parameter_value().double_value

        self.constellation = get_brazilian_rps_constellation()
        self.tf_broadcaster = TransformBroadcaster(self)

        self.pose_pubs = []
        self.geo_pubs = []
        for idx, sat in enumerate(self.constellation):
            sat_id = idx + 1
            pose_pub = self.create_publisher(PoseStamped, f'/rps/sat_{sat_id}/pose', 10)
            geo_pub = self.create_publisher(String, f'/rps/sat_{sat_id}/geodetic', 10)
            self.pose_pubs.append(pose_pub)
            self.geo_pubs.append(geo_pub)

        self.sim_time_sec = 0.0
        self.last_wall_time = time.time()
        self.timer = self.create_timer(0.05, self.orbital_step) # 20 Hz

        self.get_logger().info(f"🛰️ [RPS-BR] Telemetria Ativa: Sat 1 (GEO) + Sat 2 (IGSO Figura-8) - {self.time_mult:.0f}x")

    def orbital_step(self):
        now_wall = time.time()
        dt_wall = now_wall - self.last_wall_time
        self.last_wall_time = now_wall

        self.sim_time_sec += dt_wall * self.time_mult
        now_msg_time = self.get_clock().now().to_msg()

        for idx, sat in enumerate(self.constellation):
            sat_id = idx + 1

            r_eci = propagate_orbit_eci(sat, self.sim_time_sec)
            r_ecef = eci_to_ecef(r_eci, self.sim_time_sec)
            lat, lon, alt = ecef_to_lat_lon_alt(r_ecef)

            # PoseStamped
            pose_msg = PoseStamped()
            pose_msg.header.stamp = now_msg_time
            pose_msg.header.frame_id = "earth_center"
            pose_msg.pose.position.x = float(r_ecef[0] * self.scale)
            pose_msg.pose.position.y = float(r_ecef[1] * self.scale)
            pose_msg.pose.position.z = float(r_ecef[2] * self.scale)
            pose_msg.pose.orientation.w = 1.0
            self.pose_pubs[idx].publish(pose_msg)

            # String Geodésica
            geo_info = {
                "id": sat_id,
                "name": sat.name,
                "type": sat.sat_type,
                "lat_deg": round(lat, 2),
                "lon_deg": round(lon, 2),
                "alt_km": round(alt, 1),
                "orbit_hour": round((self.sim_time_sec / 3600.0) % 24.0, 2)
            }
            geo_msg = String()
            geo_msg.data = json.dumps(geo_info)
            self.geo_pubs[idx].publish(geo_msg)

def main(args=None):
    rclpy.init(args=args)
    node = RPSOrbitPublisherNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
