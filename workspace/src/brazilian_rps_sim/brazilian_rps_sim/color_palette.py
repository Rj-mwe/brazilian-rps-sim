#!/usr/bin/env python3
"""
Paleta de Cores e Resolvedor de Estilos para Marcadores e Linhas Orbitais.
Permite configurar cores por nome amigável ou valores RGB [r, g, b].
"""

COLOR_PALETTE = {
    # Ciano / Turquesa
    'cyan': (0.0, 0.90, 1.0),
    'ciano': (0.0, 0.90, 1.0),
    'turquoise': (0.0, 0.95, 0.85),
    
    # Âmbar / Ouro / Dourado
    'amber': (1.0, 0.80, 0.10),
    'gold': (1.0, 0.80, 0.10),
    'dourado': (1.0, 0.80, 0.10),
    'amarelo': (1.0, 0.95, 0.10),
    'yellow': (1.0, 0.95, 0.10),
    
    # Verde Neon / Esmeralda
    'neon_green': (0.10, 1.0, 0.30),
    'green': (0.10, 1.0, 0.30),
    'verde': (0.10, 1.0, 0.30),
    
    # Azul Elétrico
    'electric_blue': (0.15, 0.50, 1.0),
    'blue': (0.15, 0.50, 1.0),
    'azul': (0.15, 0.50, 1.0),
    
    # Magenta / Rosa Choque
    'magenta': (1.0, 0.15, 0.80),
    'pink': (1.0, 0.20, 0.70),
    'rosa': (1.0, 0.20, 0.70),
    
    # Laranja / Solar
    'orange': (1.0, 0.45, 0.05),
    'laranja': (1.0, 0.45, 0.05),
    
    # Roxo / Violeta
    'purple': (0.60, 0.20, 1.0),
    'violet': (0.65, 0.25, 1.0),
    'roxo': (0.60, 0.20, 1.0),
    
    # Vermelho
    'red': (1.0, 0.15, 0.15),
    'vermelho': (1.0, 0.15, 0.15),
    
    # Branco Puro
    'white': (0.95, 0.95, 1.0),
    'branco': (0.95, 0.95, 1.0)
}

def resolve_color(val, default=(1.0, 1.0, 1.0)):
    """Resolve uma cor a partir de string ou lista/tupla RGB."""
    if isinstance(val, str):
        key = val.lower().strip()
        return COLOR_PALETTE.get(key, default)
    elif isinstance(val, (list, tuple)) and len(val) >= 3:
        return (float(val[0]), float(val[1]), float(val[2]))
    return default
