#!/usr/bin/env python3
"""
Nó auxiliar para posicionar a câmera do Gazebo com distanciamento confortável da Terra e Lua.
"""

import subprocess
import time
import sys

def focus_camera(target_model: str = "earth", delay_sec: float = 2.0):
    time.sleep(delay_sec)
    
    # 🎥 Posiciona a câmera a uma distância elegante e panorâmica do par Terra-Lua (Y = -600, Z = 150)
    # olhando em direção ao centro da Terra (X = 1200, Y = 0, Z = 0)
    cmd_move = [
        "gz", "service", "-s", "/gui/move_to/pose",
        "--reqtype", "gz.msgs.GUICamera",
        "--reptype", "gz.msgs.Boolean",
        "--req", 'pose: {position: {x: 1200.0, y: -620.0, z: 140.0}, orientation: {x: 0.0, y: 0.11, z: 0.707, w: 0.707}}'
    ]
    try:
        res = subprocess.run(cmd_move, capture_output=True, text=True, timeout=5)
        print(f"🎥 [CameraFocus] Câmera posicionada a distância panorâmica da Terra! ({res.stdout.strip()})")
    except Exception as e:
        print(f"⚠️ [CameraFocus] Aviso ao posicionar câmera: {e}")

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else "earth"
    focus_camera(target)
