#!/usr/bin/env python3
"""
Compatibilidade retroativa com rps_br.adapters.web.web_node.
O nó canônico de sincronização ROS 2 reside em rps_br.adapters.ros2.Ros2WebBridgeNode.
"""

from rps_br.adapters.ros2.Ros2WebBridgeNode import Ros2WebBridgeNode, main

# Alias para compatibilidade
WebAdapterRos2Node = Ros2WebBridgeNode

if __name__ == '__main__':
    main()
