#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import math
import time
import random

class RobustGameAgent(Node):
    def __init__(self):
        super().__init__('autonomous_game_agent')

        # Publicador de comandos de velocidade
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # Assinantes de Sensores
        self.scan_sub = self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)

        # Loop de Controle a 10 Hz
        self.control_timer = self.create_timer(0.1, self.control_loop)
        self.hud_timer = self.create_timer(1.2, self.print_hud)

        # Estado do Robô e Métricas
        self.start_time = time.time()
        self.last_pos = None
        self.total_distance = 0.0
        self.score = 0
        self.agent_action = "Acelerando na Arena..."

        # Leituras do LiDAR
        self.dist_left = 10.0
        self.dist_front = 10.0
        self.dist_right = 10.0
        self.min_dist = 10.0
        self.has_scan = False

        # Variáveis de Navegação Estocástica
        self.escape_steps = 0
        self.escape_turn = 1.0
        self.wander_bias = 0.0
        self.last_wander_change = time.time()

        self.get_logger().info("🎮 [Game Agent v3] Robô Autônomo Robusto Pronto!")

    def odom_callback(self, msg: Odometry):
        current_x = msg.pose.pose.position.x
        current_y = msg.pose.pose.position.y

        if self.last_pos is not None:
            dx = current_x - self.last_pos[0]
            dy = current_y - self.last_pos[1]
            step_dist = math.hypot(dx, dy)
            if step_dist < 0.5:
                self.total_distance += step_dist
                self.score += int(step_dist * 150)

        self.last_pos = (current_x, current_y)

    def scan_callback(self, msg: LaserScan):
        ranges = msg.ranges
        n = len(ranges)
        if n == 0:
            return

        def clean_val(val):
            if math.isinf(val) or math.isnan(val) or val < msg.range_min:
                return msg.range_max
            return val

        clean_ranges = [clean_val(r) for r in ranges]

        # 3 Setores: Direita (0-60°), Frente (60-120°), Esquerda (120-180°)
        s = n // 3
        right_sector = clean_ranges[0:s]
        front_sector = clean_ranges[s:2*s]
        left_sector = clean_ranges[2*s:]

        self.dist_right = min(right_sector) if right_sector else 10.0
        self.dist_front = min(front_sector) if front_sector else 10.0
        self.dist_left = min(left_sector) if left_sector else 10.0
        self.min_dist = min(self.dist_right, self.dist_front, self.dist_left)
        self.has_scan = True

    def control_loop(self):
        if not self.has_scan:
            return

        cmd = Twist()
        now = time.time()

        # Atualiza o viés de exploração aleatória a cada 3 segundos
        if now - self.last_wander_change > 3.0:
            self.wander_bias = random.uniform(-0.3, 0.3)
            self.last_wander_change = now

        # 1. MODO DE ESCAPE DE EMERGÊNCIA (Ativo por ~1.0s após colisão/quase-colisão)
        if self.escape_steps > 0:
            cmd.linear.x = -0.2
            cmd.angular.z = self.escape_turn
            self.escape_steps -= 1
            self.agent_action = "🚨 Manobra de Evasão Rápida"

        # 2. DETECÇÃO DE OBSTÁCULO MUITO PERTO (< 0.40m) -> Dispara Escape
        elif self.min_dist < 0.40:
            self.escape_steps = 10  # 1.0 segundo (10 steps a 10Hz)
            self.escape_turn = 1.4 if self.dist_left > self.dist_right else -1.4
            cmd.linear.x = -0.2
            cmd.angular.z = self.escape_turn
            self.agent_action = "⚠️ Obstáculo Iminente: Dando ré"

        # 3. OBSTÁCULO À FRENTE (< 1.2m) -> Curva Suave
        elif self.dist_front < 1.2:
            cmd.linear.x = 0.25
            turn_dir = 1.0 if self.dist_left >= self.dist_right else -1.0
            # Adiciona viés aleatório para quebrar simetria
            cmd.angular.z = (turn_dir * 0.9) + self.wander_bias
            self.agent_action = f"↩️ Desviando para {'Esquerda' if cmd.angular.z > 0 else 'Direita'}"

        # 4. CAMINHO LIVRE (DEFAULT) -> Aceleração Constante para Frente!
        else:
            cmd.linear.x = 0.60
            cmd.angular.z = self.wander_bias
            self.agent_action = "⚡ Aceleração Livre / Explorando Arena"

        self.cmd_pub.publish(cmd)

    def print_hud(self):
        elapsed = time.time() - self.start_time
        hud = f"""
╔═══════════════════════════════════════════════════════════════════╗
║   🎮 MISSÃO ARENA GAZEBO: AGENTE AUTÔNOMO v3                       ║
╠═══════════════════════════════════════════════════════════════════╣
║ ⏱️  Tempo:     {elapsed:6.1f} s     | 🚗 Distância: {self.total_distance:5.2f} m      ║
║ 🏆 Pontuação: {self.score:6d} pts    | 🎲 Curva:     {self.wander_bias:+5.2f} rad/s    ║
║ 📡 LiDAR: [Esq: {self.dist_left:4.2f}m | Front: {self.dist_front:4.2f}m | Dir: {self.dist_right:4.2f}m]        ║
║ 🤖 Status: {self.agent_action:<53} ║
╚═══════════════════════════════════════════════════════════════════╝
"""
        print(hud)

def main(args=None):
    rclpy.init(args=args)
    node = RobustGameAgent()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        stop_cmd = Twist()
        node.cmd_pub.publish(stop_cmd)
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
