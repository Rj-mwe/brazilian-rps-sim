#!/usr/bin/env python3
"""
Nó ROS 2 para propagação e publicação da telemetria da Constelação RPS-BR
100% sincronizado com o relógio de simulação do Gazebo (use_sim_time: True).
"""

import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, TransformStamped
from tf2_ros import TransformBroadcaster
from std_msgs.msg import String

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

import json

class RPSOrbitPublisherNode(Node):
    def __init__(self):
        super().__init__('rps_orbit_publisher_node')

        self.declare_parameter('time_multiplier', 1.0) # Base 1:1 sincronizada com o simulador
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

        self.timer = self.create_timer(0.05, self.orbit_step) # 20 Hz sincronizado

        self.get_logger().info(f"🛰️ [Constelação RPS-BR] {len(self.constellation)} satélites ativos e sincronizados (Tempo Real 1:1)")

    def orbit_step(self):
        now_time = self.get_clock().now()
        sim_time_sec = now_time.nanoseconds * 1e-9 * self.time_mult
        now_stamp = now_time.to_msg()

        for idx, sat in enumerate(self.constellation):
            sat_id = idx + 1

            # Propagação analítica orbital
            r_eci, v_eci = propagate_orbit_eci(sat['elements'], sim_time_sec)
            r_ecef = eci_to_ecef(r_eci, sim_time_sec)
            lat, lon, alt = ecef_to_lat_lon_alt(r_ecef)

            # Publicação da Pose em coordenadas do mundo renderizado
            msg_pose = PoseStamped()
            msg_pose.header.stamp = now_stamp
            msg_pose.header.frame_id = 'earth_frame'
            msg_pose.pose.position.x = float(r_ecef[0] * self.scale)
            msg_pose.pose.position.y = float(r_ecef[1] * self.scale)
            msg_pose.pose.position.z = float(r_ecef[2] * self.scale)
            msg_pose.pose.orientation.w = 1.0
            self.pose_pubs[idx].publish(msg_pose)

            # Publicação dos dados geodésicos em JSON
            geo_data = {
                "id": sat_id,
                "name": sat["name"],
                "type": sat["type"],
                "latitude_deg": round(lat, 4),
                "longitude_deg": round(lon, 4),
                "altitude_km": round(alt, 2),
                "sim_time_sec": round(sim_time_sec, 2)
            }
            msg_geo = String()
            msg_geo.data = json.dumps(geo_data)
            self.geo_pubs[idx].publish(msg_geo)

def main(args=None):
    rclpy.init(args=args)
    node = RPSOrbitPublisherNode()
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
