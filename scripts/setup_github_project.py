#!/usr/bin/env python3
"""
Script de Automação do GitHub Projects para o Brazilian RPS Sim.
Cria Labels, Milestones (Históricos e Futuros), cadastra Issues com rastreabilidade
e popula o Project #2 ('RPS-BR Mission Control & Engineering Board').
"""

import json
import subprocess
import time
from typing import List, Dict, Any

REPO = "Rj-mwe/brazilian-rps-sim"
PROJECT_NUMBER = 2
OWNER = "Rj-mwe"

def run_cmd(cmd: List[str], check: bool = True) -> str:
    res = subprocess.run(cmd, capture_output=True, text=True)
    if check and res.returncode != 0:
        print(f"❌ Erro ao executar: {' '.join(cmd)}\n{res.stderr}")
        raise RuntimeError(res.stderr)
    return res.stdout.strip()

# 1. Criação de Labels
LABELS = [
    {"name": "layer:domain", "color": "1d76db", "desc": "Hexagonal: Domínio Puro & Matemática Sem Framework"},
    {"name": "layer:application", "color": "5319e7", "desc": "Hexagonal: Casos de Uso, DTOs & Orquestração"},
    {"name": "layer:adapter", "color": "0052cc", "desc": "Hexagonal: Adaptadores ROS 2 Inbound/Outbound"},
    {"name": "layer:visualization", "color": "e99695", "desc": "Renderização 3D, Gazebo Sim & OGRE 2"},
    {"name": "domain:astrodynamics", "color": "1f618d", "desc": "Mecânica Celeste, Órbitas & Astrodinâmica"},
    {"name": "domain:gnss", "color": "0e8a16", "desc": "Métricas GNSS, Pseudodistâncias & Solucionador PVT"},
    {"name": "domain:safety-critical", "color": "b60205", "desc": "Integridade RAIM, Limites HPL/VPL & Normas ICAO"},
    {"name": "type:feature", "color": "008672", "desc": "Nova funcionalidade ou modelo de engenharia"},
    {"name": "type:architecture", "color": "6f42c1", "desc": "Design patterns, refatoração e arquitetura"},
    {"name": "type:test", "color": "fbca04", "desc": "Suíte TDD, testes unitários ou de integração"},
    {"name": "priority:p0-critical", "color": "b60205", "desc": "Prioridade Máxima (Bloqueante)"},
    {"name": "priority:p1-high", "color": "d93f0b", "desc": "Prioridade Alta"},
    {"name": "priority:p2-medium", "color": "fbca04", "desc": "Prioridade Média"},
]

def setup_labels():
    print("\n🏷️ Configurando Labels padronizadas no repositório...")
    for l in LABELS:
        cmd = [
            "gh", "label", "create", l["name"],
            "--color", l["color"],
            "--description", l["desc"],
            "--repo", REPO,
            "--force"
        ]
        run_cmd(cmd, check=False)
        print(f"  ✓ Label criada/atualizada: {l['name']}")

# 2. Configuração de Milestones
MILESTONES = [
    {
        "title": "v0.1.0 - Arquitetura Hexagonal & Astrodinâmica Kepleriana",
        "desc": "Fundação matemática pura (VOs, Kepler Solver analítico, transformações ECI/ECEF/ENU) sob TDD e Ports & Adapters.",
        "state": "closed"
    },
    {
        "title": "v0.2.0 - Integração Gazebo Sim Harmonic & Geração Procedural",
        "desc": "Criação do pipeline SDFormat paramétrico, bridge ROS 2 e Builder Pattern para malhas glTF 2.0 binárias.",
        "state": "closed"
    },
    {
        "title": "v0.3.0 - Mecânica Celeste Heliocêntrica & Sistema Solar",
        "desc": "Translação e rotação física Sol-Terra-Lua com iluminação heliocêntrica, texturas 2K e cúpula celeste Hipparcos.",
        "state": "closed"
    },
    {
        "title": "v0.4.0 - Métricas Geométricas DOP & Visualização Radar STK",
        "desc": "Implementação dos padrões Strategy e Observer para cálculo de DOP contínuo e renderização de feixes nadir de alta fidelidade.",
        "state": "closed"
    },
    {
        "title": "v0.5.0 - Modelo Físico de Sinais & Pseudodistâncias GNSS",
        "desc": "Modelagem física de propagação de sinais: retardo ionosférico (Klobuchar), troposférico (Saastamoinen), relatividade e ruído térmico.",
        "state": "open"
    },
    {
        "title": "v0.6.0 - Solucionador de Navegação do Usuário (PVT Solver)",
        "desc": "Algoritmo de Mínimos Quadrados Ponderados Iterativo (Iterative WLS) para determinação de posição 3D e viés de relógio do receptor.",
        "state": "open"
    },
    {
        "title": "v0.7.0 - Integridade RAIM & Níveis de Proteção Aeronáutica",
        "desc": "Monitoramento Autônomo de Integridade do Receptor (RAIM com teste Chi-quadrado) e cálculo de HPL/VPL sob norma RTCA DO-229D.",
        "state": "open"
    },
    {
        "title": "v0.8.0 - Avaliação de Aumento Regional do RPS-BR sobre GPS",
        "desc": "Análise comparativa de melhoria de acurácia sobre o território brasileiro e telemetria de navegação em tópicos ROS 2.",
        "state": "open"
    }
]

def setup_milestones() -> Dict[str, int]:
    print("\n🎯 Configurando Milestones (Marcos Históricos e Futuros)...")
    milestone_map = {}
    
    # Lista existentes
    raw = run_cmd(["gh", "api", f"repos/{REPO}/milestones?state=all"])
    existing = json.loads(raw) if raw else []
    for m in existing:
        milestone_map[m["title"]] = m["number"]

    for m in MILESTONES:
        title = m["title"]
        if title not in milestone_map:
            # Cria como open inicialmente
            res = run_cmd([
                "gh", "api", f"repos/{REPO}/milestones",
                "-f", f"title={title}",
                "-f", f"description={m['desc']}",
                "-f", "state=open"
            ])
            data = json.loads(res)
            milestone_map[title] = data["number"]
            print(f"  ✓ Milestone criado: #{data['number']} - {title}")
        else:
            print(f"  ✓ Milestone existente: #{milestone_map[title]} - {title}")
            
    return milestone_map

# 3. Definição de Issues (Históricas e Futuras)
HISTORICAL_ISSUES = [
    {
        "title": "feat(domain): modelagem do domínio puro e astrodinâmica kepleriana (Value Objects)",
        "milestone": "v0.1.0 - Arquitetura Hexagonal & Astrodinâmica Kepleriana",
        "labels": ["layer:domain", "domain:astrodynamics", "type:feature", "type:test"],
        "body": """### 🛰️ Resumo Histórico da Implementação
Criação dos Value Objects imutáveis centrais da arquitetura hexagonal:
- `Vector3DVO`: Operações vetoriais 3D com álgebra linear intrínseca.
- `GeodeticCoordinatesVO`: Representação geodésica WGS-84 (Latitude, Longitude, Altitude).
- `KeplerianElementsVO`: Elementos orbitais clássicos ($a, e, i, \Omega, \omega, M$).
- `QuaternionVO`: Representação de atitude sem gimbal lock.

**Validação**: Suíte de testes unitários TDD em `tests/unit/test_value_objects.py` passando 100%.""",
        "priority": "P0"
    },
    {
        "title": "feat(domain): solucionador analítico da equação de Kepler com perturbação J2",
        "milestone": "v0.1.0 - Arquitetura Hexagonal & Astrodinâmica Kepleriana",
        "labels": ["layer:domain", "domain:astrodynamics", "type:feature", "type:test"],
        "body": """### 🛰️ Resumo Histórico da Implementação
Implementação do serviço de domínio puro `KeplerSolverService`:
- Solução iterativa robusta por Newton-Raphson da Equação Transcendental de Kepler ($M = E - e \sin E$).
- Cálculo de anomalia verdadeira ($\nu$) e raio vetor orbital.
- Modelagem de perturbações orbitais seculares devidas ao achatamento terrestre ($J_2$).

**Validação**: Testes em `tests/unit/test_kepler_solver_service.py` com convergência $\Delta < 10^{-12}$.""",
        "priority": "P0"
    },
    {
        "title": "feat(domain): transformações de referenciais geodésicos ECI <-> ECEF <-> ENU",
        "milestone": "v0.1.0 - Arquitetura Hexagonal & Astrodinâmica Kepleriana",
        "labels": ["layer:domain", "domain:astrodynamics", "type:feature", "type:test"],
        "body": """### 🛰️ Resumo Histórico da Implementação
Implementação de `CoordinateTransformService`:
- Transformação ECI (J2000 inercial) para ECEF (terrestre rotacionante) via Tempo Sideral Aparente de Greenwich (GAST).
- Conversão analítica ECEF para Geodético (Bowring / WGS-84).
- Transformação para sistema topocêntrico local ENU (East, North, Up) e cálculo de elevação/azimute de visibilidade.

**Validação**: Teste unitário `test_coordinate_transform_service.py` cobrindo 24h completas de rotação terrestre.""",
        "priority": "P0"
    },
    {
        "title": "feat(infra): geração procedural do mundo SDFormat com injeção de dependências",
        "milestone": "v0.2.0 - Integração Gazebo Sim Harmonic & Geração Procedural",
        "labels": ["layer:visualization", "type:feature"],
        "body": """### 🛰️ Resumo Histórico da Implementação
Criação do gerador procedural `world_generator.py`:
- Lê declarativamente `config/simulation_parameters.yaml` como Fonte Única da Verdade (SSoT).
- Injeta parâmetros orbitais e astronômicos diretamente nos plugins C++ via SDFormat 1.8.
- Eliminação total de parâmetros hardcoded em código compilado.""",
        "priority": "P1"
    },
    {
        "title": "feat(adapter): integração ROS 2 Jazzy e Gazebo Sim Harmonic via ros_gz_bridge",
        "milestone": "v0.2.0 - Integração Gazebo Sim Harmonic & Geração Procedural",
        "labels": ["layer:adapter", "type:feature"],
        "body": """### 🛰️ Resumo Histórico da Implementação
Conexão bidirecional entre ROS 2 e Gazebo Sim Harmonic:
- Sincronização do relógio de simulação via ponte `/clock`.
- Publicação de telemetria orbital (`/rps/sat_X/pose` e `/rps/sat_X/geodetic`).
- Implementação da Unix Rule of Silence no nó `Ros2ConstellationNode` para terminal limpo.""",
        "priority": "P1"
    },
    {
        "title": "feat(graphics): builder pattern para malhas glTF 2.0 binárias (.glb)",
        "milestone": "v0.2.0 - Integração Gazebo Sim Harmonic & Geração Procedural",
        "labels": ["layer:visualization", "type:architecture", "type:feature"],
        "body": """### 🛰️ Resumo Histórico da Implementação
Implementação do padrão Builder em `GltfMeshBuilder` (`gltf_builder.py`):
- Empacotamento binário direto no formato glTF 2.0 / GLB com alinhamento de 4 bytes.
- Suporte a múltiplas primitivas geométricas e materiais PBR independentes.
- Eliminação de artefatos visuais e renderização fluida no motor OGRE 2 do Gazebo.""",
        "priority": "P1"
    },
    {
        "title": "feat(plugin): simulação heliocêntrica e mecânica celeste realista do sistema Sol-Terra-Lua",
        "milestone": "v0.3.0 - Mecânica Celeste Heliocêntrica & Sistema Solar",
        "labels": ["domain:astrodynamics", "layer:visualization", "type:feature"],
        "body": """### 🛰️ Resumo Histórico da Implementação
Desenvolvimento de `CelestialMechanicsPlugin.cpp` e `CelestialSystemAggregate`:
- O Sol posicionado na origem inercial (0,0,0) com emissão de luz radial pontual de 500.000 km.
- Translação heliocêntrica da Terra com inclinação do eixo polar (obliquidade de 23.44°).
- Translação e rotação síncrona da Lua (inclinação de 5.145° e órbita de 27.32 dias) com fases lunares fotorrealistas.""",
        "priority": "P1"
    },
    {
        "title": "feat(graphics): texturização PBR 2K NASA Blue Marble e cúpula celeste Hipparcos",
        "milestone": "v0.3.0 - Mecânica Celeste Heliocêntrica & Sistema Solar",
        "labels": ["layer:visualization", "type:feature"],
        "body": """### 🛰️ Resumo Histórico da Implementação
Geração procedural dos corpos celestes com texturização fotorrealista PBR:
- Globo terrestre com textura diurna NASA Blue Marble e iluminação noturna urbana (Night Lights).
- Camada dinâmica de nuvens com deriva atmosférica física (`clouds_drift_factor`).
- Cúpula celeste esférica com catálogo Hipparcos de estrelas 360° com normais invertidas.""",
        "priority": "P2"
    },
    {
        "title": "feat(domain): cálculo analítico de métricas DOP via Strategy Pattern",
        "milestone": "v0.4.0 - Métricas Geométricas DOP & Visualização Radar STK",
        "labels": ["layer:domain", "domain:gnss", "type:architecture", "type:feature"],
        "body": """### 🛰️ Resumo Histórico da Implementação
Implementação da família de estratégias de diluição geométrica de precisão:
- `StandardLeastSquaresDopStrategy`: Matriz $G$ de cossenos diretores e matriz de covariância $(G^T G)^{-1}$.
- `ElevationMaskDopStrategy`: Filtragem por máscara de ângulo de corte.
- `WeightedElevationDopStrategy`: Ponderação estocástica proporcional ao ângulo de elevação.
- Cálculo de GDOP, PDOP, HDOP, VDOP e TDOP em Value Object `DopResultVO`.""",
        "priority": "P0"
    },
    {
        "title": "feat(application): monitoramento contínuo de DOP no Brasil via Observer Pattern",
        "milestone": "v0.4.0 - Métricas Geométricas DOP & Visualização Radar STK",
        "labels": ["layer:application", "domain:gnss", "type:architecture", "type:feature"],
        "body": """### 🛰️ Resumo Histórico da Implementação
Implementação do padrão Observer desacoplado para auditoria e telemetria:
- `CalculateGroundStationDopUseCase`: Avaliação simultânea para Brasília, Manaus, Rio de Janeiro, Porto Alegre e Fortaleza.
- `DopSubject`: Sujeito notificatório de eventos de navegação.
- `DopAlertThresholdObserver`: Emissão de alarmes operacionais quando $\text{PDOP} > 6.0$.
- `DopTelemetryBufferObserver`: Armazenamento de séries temporais e telemetria.""",
        "priority": "P1"
    },
    {
        "title": "feat(graphics): gaiola holográfica radar STK e feixes boresight com cores independentes",
        "milestone": "v0.4.0 - Métricas Geométricas DOP & Visualização Radar STK",
        "labels": ["layer:visualization", "type:feature"],
        "body": """### 🛰️ Resumo Histórico da Implementação
Modernização da renderização dos cones de cobertura dos 7 satélites:
- Separação em dois nós visuais SDF independentes: Gaiola Externa (`v_nadir_cage`) e Feixe Laser Central (`v_nadir_boresight`).
- Visualização estilo STK/NASA com anel de pegada no solo (Footprint) e mira crosshair.
- Cores de alto contraste: Dourado/Âmbar para gaiola IGSO, Laranja Vibrante Incandescente para feixe central IGSO, Ciano e Branco para GEOs.""",
        "priority": "P1"
    }
]

FUTURE_ISSUES = [
    {
        "title": "feat(domain): modelagem de retardo ionosférico para a região equatorial brasileira",
        "milestone": "v0.5.0 - Modelo Físico de Sinais & Pseudodistâncias GNSS",
        "labels": ["layer:domain", "domain:gnss", "priority:p0-critical", "type:feature"],
        "body": """### 1. Contexto Teórico & Motivação
O Brasil está sob a Anomalia de Ionização Equatorial (EIA), onde o retardo ionosférico é um dos maiores do planeta, variando drasticamente entre o dia e a noite.

### 2. Especificação Técnica
- Implementar `IonosphereKlobucharService` baseado nos 8 coeficientes de broadcast da mensagem de navegação.
- Suporte a retardo de caminho oblíquo através da função de obliquidade (Mapping Function).

### 3. Critérios de Aceitação TDD
- [ ] Teste de validação contra vetores analíticos de referência do IS-GPS-200.
- [ ] Teste de transição diurna/noturna (retardo mínimo à noite e pico solar às 14h locais).
- [ ] Tolerância de concordância < 1e-3 m.""",
        "priority": "P0"
    },
    {
        "title": "feat(domain): modelagem de retardo troposférico zenital e funções de mapeamento (Saastamoinen)",
        "milestone": "v0.5.0 - Modelo Físico de Sinais & Pseudodistâncias GNSS",
        "labels": ["layer:domain", "domain:gnss", "priority:p0-critical", "type:feature"],
        "body": """### 1. Contexto Teórico & Motivação
A troposfera atrasa o sinal GNSS através do componente hidrostático (ar seco) e do componente úmido (vapor d'água).

### 2. Especificação Técnica
- Implementar `TroposphereSaastamoinenService` calculando:
  $$\\Delta_{\\text{tropo}} = \\frac{0.002277}{\\cos(\\theta_z)} \\left[ P + \\left(\\frac{1255}{T} + 0.05\\right) e - B \\tan^2(\\theta_z) \\right]$$
- Modelo de atmosfera padrão com parâmetros por altitude do receptor.

### 3. Critérios de Aceitação TDD
- [ ] Teste do retardo ao zênite (~2.3 metros ao nível do mar).
- [ ] Teste de degradação com baixa elevação (5° a 15°).
- [ ] Suíte de testes unitários passando 100% no pytest.""",
        "priority": "P0"
    },
    {
        "title": "feat(domain): gerador de observáveis de pseudodistância com perturbações e ruído gaussiano",
        "milestone": "v0.5.0 - Modelo Físico de Sinais & Pseudodistâncias GNSS",
        "labels": ["layer:domain", "domain:gnss", "priority:p0-critical", "type:feature"],
        "body": """### 1. Contexto Teórico & Motivação
Montar a equação completa de pseudodistância bruta $\\rho$ para cada satélite visível pelo usuário:
$$\\rho_i = R_i + c \\cdot (\\delta t_{\\text{rx}} - \\delta t_{\\text{sat}}) + I_i + T_i + \\Delta_{\\text{rel}} + \\epsilon_i$$

### 2. Especificação Técnica
- Value Object `PseudorangeMeasurementVO`.
- Serviço `PseudorangeSimulationService` integrando range geométrico, erros de relógio, retardo atmosférico e ruído estocástico.

### 3. Critérios de Aceitação TDD
- [ ] Teste de range puramente geométrico sem ruído.
- [ ] Teste de injeção de viés de relógio do receptor.
- [ ] Teste de cálculo do termo relativístico orbital.""",
        "priority": "P0"
    },
    {
        "title": "feat(domain): solucionador iterativo de mínimos quadrados ponderados (WLS PVT Solver)",
        "milestone": "v0.6.0 - Solucionador de Navegação do Usuário (PVT Solver)",
        "labels": ["layer:domain", "domain:gnss", "priority:p1-high", "type:feature"],
        "body": """### 1. Contexto Teórico & Motivação
O receptor desconhece sua própria posição e o erro do seu oscilador local. O solucionador PVT calcula iterativamente $\\Delta \\mathbf{x} = (G^T W G)^{-1} G^T W \\Delta \\mathbf{\\rho}$.

### 2. Especificação Técnica
- Interface `IPvtSolverStrategy` (Strategy Pattern).
- Classe `IterativeWlsPvtSolver`: convergência com critério $\\|\\Delta \\mathbf{x}\\| < 10^{-4}\\text{ m}$.
- Value Object `PvtSolutionVO` com posição estimada, erro 3D e desvio de relógio.

### 3. Critérios de Aceitação TDD
- [ ] Teste de convergência exata a partir de uma posição inicial a 100 km de distância.
- [ ] Teste com 4, 5, 6 e 7 satélites visíveis.
- [ ] Erro de recuperação da posição real inferior ao ruído injetado.""",
        "priority": "P1"
    },
    {
        "title": "feat(application): caso de uso CalculateUserPvtUseCase para receptores estáticos e móveis",
        "milestone": "v0.6.0 - Solucionador de Navegação do Usuário (PVT Solver)",
        "labels": ["layer:application", "domain:gnss", "priority:p1-high", "type:feature"],
        "body": """### 1. Contexto Teórico & Motivação
Orquestrar o fluxo de navegação do usuário final no território brasileiro.

### 2. Especificação Técnica
- Caso de uso `CalculateUserPvtUseCase`.
- Suporte a múltiplos cenários: estação fixa de referência, navio na Bacia de Santos, aeronave na aerovia Rio-Brasília.
- DTOs limpos para desacoplamento de transporte.

### 3. Critérios de Aceitação TDD
- [ ] Teste de integração de 24h computando o erro RMS de posição.
- [ ] Verificação da melhora de acurácia com a constelação híbrida GEO+IGSO.""",
        "priority": "P1"
    },
    {
        "title": "feat(domain): algoritmo de integridade autônoma do receptor (RAIM) com detecção Chi-Quadrado",
        "milestone": "v0.7.0 - Integridade RAIM & Níveis de Proteção Aeronáutica",
        "labels": ["layer:domain", "domain:safety-critical", "priority:p1-high", "type:feature"],
        "body": """### 1. Contexto Teórico & Motivação
Na aviação e navegação crítica, o receptor deve detectar e excluir autonomamente satélites com anomalias (FDE - Fault Detection and Exclusion).

### 2. Especificação Técnica
- Cálculo do vetor de resíduos pós-ajuste: $\\mathbf{r} = \\Delta \\mathbf{\\rho} - G \\Delta \\mathbf{x}$.
- Estatística de teste: $s = \\mathbf{r}^T W \\mathbf{r} \\sim \\chi^2_{N-4}$.
- Limiar de alarme para probabilidade de falso alarme $P_{fa} = 10^{-5}$.

### 3. Critérios de Aceitação TDD
- [ ] Teste de aceitação em cenário nominal sem satélites falhos (sem falso alarme).
- [ ] Injeção intencional de erro de +50m em um IGSO e validação do disparo do alarme de integridade.""",
        "priority": "P1"
    },
    {
        "title": "feat(domain): cálculo dos níveis de proteção horizontal e vertical (HPL/VPL - RTCA DO-229D)",
        "milestone": "v0.7.0 - Integridade RAIM & Níveis de Proteção Aeronáutica",
        "labels": ["layer:domain", "domain:safety-critical", "priority:p1-high", "type:feature"],
        "body": """### 1. Contexto Teórico & Motivação
Cálculo dos limites de contenção de erro com integridade de $99.99999\\%$ ($1 - 10^{-7}$) para operações de aproximação de precisão LPV (Localizer Performance with Vertical Guidance).

### 2. Especificação Técnica
- Fórmulas analíticas do Apêndice J do documento RTCA DO-229D:
  $$\\text{HPL} = K_{H} \\cdot d_{\\text{major}}, \\quad \\text{VPL} = K_{V} \\cdot \\sigma_{V}$$
- Value Object `ProtectionLevelsVO`.

### 3. Critérios de Aceitação TDD
- [ ] Validação do elipsóide de erro horizontal ($d_{\\text{major}}, d_{\\text{minor}}$).
- [ ] Verificação de HPL < Limite de Alerta Horizontal (HAL = 40m para aproximação APV-I).""",
        "priority": "P1"
    },
    {
        "title": "feat(application): avaliação comparativa de aumento regional RPS-BR sobre GPS puro",
        "milestone": "v0.8.0 - Avaliação de Aumento Regional do RPS-BR sobre GPS",
        "labels": ["layer:application", "domain:gnss", "priority:p2-medium", "type:feature"],
        "body": """### 1. Contexto Teórico & Motivação
Demonstrar quantitativamente o ganho trazido pelo RPS-BR quando combinado com constelações globais (GPS L1/L5).

### 2. Especificação Técnica
- Caso de uso `EvaluateConstellationAugmentationUseCase`.
- Comparação lado a lado:
  - GPS Puro: PDOP médio, disponibilidade de RAIM, HPL.
  - GPS + RPS-BR (7 satélites): redução de PDOP, redução de HPL, disponibilidade 99.999%.

### 3. Critérios de Aceitação TDD
- [ ] Relatório comparativo gerado em tempo de teste.
- [ ] Comprovação de redução de mais de 35% no PDOP sobre o território brasileiro.""",
        "priority": "P2"
    },
    {
        "title": "feat(adapter): telemetria de navegação e integridade em tópicos ROS 2 padronizados",
        "milestone": "v0.8.0 - Avaliação de Aumento Regional do RPS-BR sobre GPS",
        "labels": ["layer:adapter", "domain:gnss", "priority:p2-medium", "type:feature"],
        "body": """### 1. Contexto Teórico & Motivação
Disponibilizar os dados de navegação e segurança operacional em tempo real para o ecossistema ROS 2.

### 2. Especificação Técnica
- Tópicos ROS 2:
  - `/rps/user/pvt`: Posição estimada, velocidade, erro 3D e desvio de relógio.
  - `/rps/user/integrity`: HPL, VPL, status RAIM e satélites excluídos.
- Implementação de `Ros2NavigationOutboundAdapter` desacoplado.""",
        "priority": "P2"
    }
]

def create_and_project_issues(milestone_map: Dict[str, int]):
    print("\n📝 Criando e Vinculando Issues ao GitHub Projects #2...")
    
    # Processa Históricas (Fechadas)
    print("\n--- Processando Issues Históricas (Registros Concluídos) ---")
    for item in HISTORICAL_ISSUES:
        m_title = item["milestone"]
        m_num = milestone_map[m_title]
        labels_str = ",".join(item["labels"])
        
        # Cria issue
        cmd = [
            "gh", "issue", "create",
            "--repo", REPO,
            "--title", item["title"],
            "--body", item["body"],
            "--milestone", m_title,
            "--label", labels_str
        ]
        issue_url = run_cmd(cmd)
        issue_num = issue_url.split("/")[-1]
        print(f"  ✓ Issue histórica criada: #{issue_num} ({item['title'][:45]}...)")
        
        # Fecha a issue no GitHub
        run_cmd(["gh", "issue", "close", issue_num, "--repo", REPO, "--reason", "completed"])
        
        # Adiciona ao Project 2
        run_cmd(["gh", "project", "item-add", str(PROJECT_NUMBER), "--owner", OWNER, "--url", issue_url])
        
        # Atualiza o Status para "Done" no Project
        run_cmd([
            "gh", "project", "item-edit", str(PROJECT_NUMBER),
            "--owner", OWNER,
            "--url", issue_url,
            "--field", "Status",
            "--value", "Done"
        ])
        
        # Atualiza a Prioridade
        run_cmd([
            "gh", "project", "item-edit", str(PROJECT_NUMBER),
            "--owner", OWNER,
            "--url", issue_url,
            "--field", "Priority",
            "--value", item["priority"]
        ])
        time.sleep(0.5)

    # Processa Futuras (Abertas / Backlog)
    print("\n--- Processando Issues Futuras (Backlog do Domínio GNSS & PVT) ---")
    for item in FUTURE_ISSUES:
        m_title = item["milestone"]
        m_num = milestone_map[m_title]
        labels_str = ",".join(item["labels"])
        
        # Cria issue aberta
        cmd = [
            "gh", "issue", "create",
            "--repo", REPO,
            "--title", item["title"],
            "--body", item["body"],
            "--milestone", m_title,
            "--label", labels_str
        ]
        issue_url = run_cmd(cmd)
        issue_num = issue_url.split("/")[-1]
        print(f"  ✓ Issue futura criada: #{issue_num} ({item['title'][:45]}...)")
        
        # Adiciona ao Project 2
        run_cmd(["gh", "project", "item-add", str(PROJECT_NUMBER), "--owner", OWNER, "--url", issue_url])
        
        # Define Status como "Todo"
        run_cmd([
            "gh", "project", "item-edit", str(PROJECT_NUMBER),
            "--owner", OWNER,
            "--url", issue_url,
            "--field", "Status",
            "--value", "Todo"
        ])
        
        # Define Prioridade
        run_cmd([
            "gh", "project", "item-edit", str(PROJECT_NUMBER),
            "--owner", OWNER,
            "--url", issue_url,
            "--field", "Priority",
            "--value", item["priority"]
        ])
        time.sleep(0.5)

    # Fecha os milestones históricos que foram concluídos
    print("\n🔒 Fechando Milestones Históricos concluídos...")
    for m in MILESTONES:
        if m["state"] == "closed":
            m_num = milestone_map[m["title"]]
            run_cmd([
                "gh", "api", "-X", "PATCH",
                f"repos/{REPO}/milestones/{m_num}",
                "-f", "state=closed"
            ])
            print(f"  ✓ Milestone #{m_num} ({m['title'][:35]}...) fechado como concluído.")

if __name__ == "__main__":
    print("🚀 Iniciando configuração completa do GitHub Projects...")
    setup_labels()
    m_map = setup_milestones()
    create_and_project_issues(m_map)
    print("\n✨ Configuração concluída com sucesso!")
    print(f"🔗 Acesse o seu Board: https://github.com/users/{OWNER}/projects/{PROJECT_NUMBER}")
