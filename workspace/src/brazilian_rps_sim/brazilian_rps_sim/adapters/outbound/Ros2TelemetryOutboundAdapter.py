"""
Adaptador de Saída ROS 2 implementando ITelemetryOutboundPort.
Converte VOs e Agregados em mensagens ROS 2 padrão (PoseStamped, String JSON sucinta).
"""

import json
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String

from brazilian_rps_sim.core.domain.interfaces.ITelemetryOutboundPort import ITelemetryOutboundPort
from brazilian_rps_sim.core.domain.value_objects.Vector3DVO import Vector3DVO
from brazilian_rps_sim.core.domain.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO
from brazilian_rps_sim.core.domain.value_objects.QuaternionVO import QuaternionVO

class Ros2TelemetryOutboundAdapter(ITelemetryOutboundPort):
    def __init__(self, node: Node, total_satellites: int = 7, render_scale: float = 0.001):
        self.node = node
        self.render_scale = render_scale
        self.pose_pubs = {}
        self.geo_pubs = {}

        for sat_id in range(1, total_satellites + 1):
            self.pose_pubs[sat_id] = node.create_publisher(PoseStamped, f'/rps/sat_{sat_id}/pose', 10)
            self.geo_pubs[sat_id] = node.create_publisher(String, f'/rps/sat_{sat_id}/geodetic', 10)

        # Publicadores Celestes
        self.earth_pose_pub = node.create_publisher(PoseStamped, '/celestial/earth/pose', 10)
        self.moon_pose_pub = node.create_publisher(PoseStamped, '/celestial/moon/pose', 10)
        self.moon_phase_pub = node.create_publisher(String, '/celestial/moon/phase', 10)

    def publish_satellite_state(self, sat_id: int, name: str, sat_type: str,
                                r_ecef: Vector3DVO, geodetic: GeodeticCoordinatesVO,
                                attitude: QuaternionVO, t_sec: float) -> None:
        now_stamp = self.node.get_clock().now().to_msg()

        # 1. Mensagem de Pose 3D
        if sat_id in self.pose_pubs:
            msg_pose = PoseStamped()
            msg_pose.header.stamp = now_stamp
            msg_pose.header.frame_id = 'earth_frame'
            msg_pose.pose.position.x = r_ecef.x * self.render_scale
            msg_pose.pose.position.y = r_ecef.y * self.render_scale
            msg_pose.pose.position.z = r_ecef.z * self.render_scale
            msg_pose.pose.orientation.x = attitude.x
            msg_pose.pose.orientation.y = attitude.y
            msg_pose.pose.orientation.z = attitude.z
            msg_pose.pose.orientation.w = attitude.w
            self.pose_pubs[sat_id].publish(msg_pose)

        # 2. Mensagem Geodésica JSON Sucinta e Clara
        if sat_id in self.geo_pubs:
            geo_data = {
                "id": sat_id,
                "name": name,
                "type": sat_type,
                "lat": round(geodetic.latitude_deg, 2),
                "lon": round(geodetic.longitude_deg, 2),
                "alt_km": round(geodetic.altitude_km, 1),
                "t_sec": round(t_sec, 1)
            }
            msg_geo = String()
            msg_geo.data = json.dumps(geo_data, ensure_ascii=False)
            self.geo_pubs[sat_id].publish(msg_geo)

    def publish_celestial_state(self, celestial_state: dict) -> None:
        now_stamp = self.node.get_clock().now().to_msg()
        earth_pos = celestial_state['earth_pos']
        earth_rot = celestial_state['earth_rot']
        moon_rel_pos = celestial_state['moon_rel_pos']
        moon_illum = celestial_state['moon_illumination_pct']

        msg_earth = PoseStamped()
        msg_earth.header.stamp = now_stamp
        msg_earth.header.frame_id = 'sun_frame'
        msg_earth.pose.position.x = earth_pos.x
        msg_earth.pose.position.y = earth_pos.y
        msg_earth.pose.position.z = earth_pos.z
        msg_earth.pose.orientation.x = earth_rot.x
        msg_earth.pose.orientation.y = earth_rot.y
        msg_earth.pose.orientation.z = earth_rot.z
        msg_earth.pose.orientation.w = earth_rot.w
        self.earth_pose_pub.publish(msg_earth)

        msg_moon = PoseStamped()
        msg_moon.header.stamp = now_stamp
        msg_moon.header.frame_id = 'earth_frame'
        msg_moon.pose.position.x = moon_rel_pos.x
        msg_moon.pose.position.y = moon_rel_pos.y
        msg_moon.pose.position.z = moon_rel_pos.z
        msg_moon.pose.orientation.w = 1.0
        self.moon_pose_pub.publish(msg_moon)

        msg_phase = String()
        msg_phase.data = f"{moon_illum:.0f}%"
        self.moon_phase_pub.publish(msg_phase)
