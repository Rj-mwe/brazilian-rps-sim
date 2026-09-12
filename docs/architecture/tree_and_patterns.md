# 🌲 Árvore do Projeto & Catálogo de Padrões de Projeto

Este documento detalha o mapeamento estrutural dos arquivos do repositório **Brazilian RPS Sim** e o catálogo formal de padrões de projeto (*Design Patterns*) implementados na arquitetura.

---

## 🌲 1. Árvore do Projeto Anotada

```text
brazilian-rps-sim/
├── config/                          # Configurações declarativas da simulação
│   └── simulation_parameters.yaml   # Parâmetros orbitais dos 7 satélites, estações e relógio
├── docs/                            # Documentação técnica e científica de engenharia
│   ├── adr/                         # Architectural Decision Records formais (0001 a 0005)
│   ├── architecture/                # Módulos detalhados da arquitetura do sistema
│   ├── api.md                       # Especificação da API REST, WebSockets e NMEA 0183
│   ├── cli.md                       # Manual de uso e automação da CLI rps-sim
│   ├── testing.md                   # Engenharia de testes, pirâmide e tolerâncias
│   ├── quality_safety.md            # Qualidade, confiabilidade e segurança (DO-178C, ECSS)
│   ├── algorithms_complexity.md     # Análise assintótica de algoritmos e estruturas de dados
│   ├── architecture.md              # Documento-mestre e índice executivo de arquitetura
│   └── index.md                     # Portal de entrada e índice geral da documentação
├── papers/                          # [CIDADÃO DE PRIMEIRA CLASSE] Artigos científicos
│   └── sbas_brazil_journal/         # Manuscrito formal em Typst para periódicos aeroespaciais
│       ├── main.typ                 # Código-fonte do artigo em Typst
│       ├── README.md                # Instruções de compilação
│       └── paper_rps_brazil.pdf     # PDF compilado do artigo
├── rps_br/                          # Pacote Python principal da biblioteca
│   ├── core/                        # NÚCLEO PURO (Hexágono Central - Zero dependências externas)
│   │   ├── application/             # Casos de Uso, Orquestração, NoC e Governança
│   │   │   ├── dtos/                # Data Transfer Objects com tipagem estática
│   │   │   ├── interfaces/          # Portas abstratas de casos de uso (driven/driving)
│   │   │   ├── mappers/             # Mapeadores entre entidades e DTOs
│   │   │   ├── services/            # Casos de uso: SimulationSessionService, CalculateGroundStationDopUseCase
│   │   │   ├── noc/                 # [NETWORK ON CORE] Malha lógica de transporte, envelopes e canais virtuais
│   │   │   └── governance/          # [SUB-CORE DE GOVERNANÇA] Mestre do relógio, compliance e ciclo de vida
│   │   └── domain/                  # Domínio Astrodinâmico e de Radionavegação
│   │       ├── astrodynamics/       # Agregados de Satélite/Constelação, Políticas de Órbita
│   │       ├── navigation_pvt/      # Estratégias de cálculo DOP e Observadores de alerta
│   │       ├── signal_propagation/  # Modelos de retardo Saastamoinen e Klobuchar
│   │       └── shared/              # Value Objects fundamentais (Vector3D, Geodetic, Keplerian)
│   ├── adapters/                    # ADAPTADORES DE BORDA (Ports & Adapters)
│   │   ├── api/                     # Gateway Unificado de APIs (FastAPI, WebSockets, NMEA 0183)
│   │   │   ├── rest/                # Rotas RESTful modulares de telemetria e controle
│   │   │   ├── streaming/           # Loop assíncrono de streaming WebSocket a 1 Hz
│   │   │   ├── nmea/                # Gerador e emulador de sentenças NMEA 0183 ($GNGGA, etc.)
│   │   │   └── server.py            # Servidor FastAPI principal agregador
│   │   ├── ui/                      # Dashboard SPA Independente (HTML5, Tailwind, Chart.js)
│   │   ├── cesium/                  # Adaptador 3D Cesium (Builder CZML WGS84 e visualizador)
│   │   ├── cli/                     # Adaptador CLI autônomo (rps-sim)
│   │   ├── ros2/                    # Nós de temporização e tópicos de robótica em ROS 2 Jazzy
│   │   ├── gazebo/                  # Descrição de mundos SDF, modelos 3D e controle de física
│   │   └── export/                  # Exportador de séries temporais de trajetória (JSON/CSV)
│   └── infrastructure/              # INFRAESTRUTURA DE APOIO (Substrato Técnico Vanguard)
│       ├── config/                  # Carregamento e validação de arquivos YAML
│       ├── noc/                     # Drivers de enlace físico concreto do NoC (/dev/shm, IPC)
│       └── persistence/             # Repositórios de telemetria histórica e séries temporais
├── scripts/                         # Executáveis e lançadores de conveniência
│   ├── rps-sim                      # Atalho para a CLI
│   ├── rps_constellation_node       # Executável do nó ROS 2 de dinâmica
│   └── rps_web_bridge_node          # Executável da ponte de relógio ROS 2 -> Web
├── tests/                           # SUÍTE DE TESTES AUTOMATIZADOS (78 testes no Pytest)
│   ├── integration/                 # Testes de missão de longa duração (24 horas)
│   └── unit/                        # Testes unitários particionados por domínio e adaptadores
├── dashboard.sh                     # Script shell de inicialização rápida do API Gateway
└── setup.py                         # Manifesto oficial de empacotamento Python / ROS 2
```

---

## 🎨 2. Catálogo de Padrões de Projeto (*Design Patterns*) Implementados

### A. Padrão Strategy (*Estratégia de Cálculo de DOP*)
* **Problema:** Diferentes cenários operacionais exigem diferentes métodos de seleção e ponderação de satélites para cálculo de GDOP/PDOP/HDOP/VDOP.
* **Solução:** A interface `IDopCalculationStrategy` desacopla o algoritmo de cálculo do caso de uso.
* **Estratégias Implementadas:**
  * `StandardLeastSquaresDopStrategy`: Inversão matricial de mínimos quadrados clássica.
  * `ElevationMaskDopStrategy`: Descarta satélites abaixo de um ângulo de corte ($\theta_i < \theta_{\text{mask}}$).
  * `WeightedElevationDopStrategy`: Pondera a matriz de covariância pelo seno da elevação ($\sin^2 el$).

### B. Padrão Strategy (*Solucionador de Navegação PVT*)
* **Problema:** Um receptor GNSS pode alternar entre algoritmos numéricos de posicionamento (ex: Mínimos Quadrados Simples, Mínimos Quadrados Ponderados, Filtro de Kalman Estendido - EKF, ou Factor Graphs) sem que a camada de aplicação ou casos de uso dependam da implementação matemática específica.
* **Solução:** A interface `IPvtSolverStrategy` define o contrato universal de resolução de estado $\mathbf{x} = [x, y, z, c \cdot \delta t_{\text{rx}}]^T$.
* **Estratégias Implementadas:**
  * `IterativeWlsPvtSolver`: Algoritmo iterativo de Gauss-Newton com matriz de pesos estocásticos baseada no seno da elevação e conversão geodésica WGS-84 integrada (para a formulação matemática rigorosa das equações de pseudodistância e convergência de mínimos quadrados, consulte [`docs/math_theory/pvt_least_squares.md`](../math_theory/pvt_least_squares.md)).

### C. Padrão Observer (*Notificação e Alertas de Degradação de Sinal*)
* **Problema:** Quando o PDOP ultrapassa limites operacionais de aproximação aeronáutica ($PDOP > 6.0$), múltiplos subsistemas precisam ser notificados sem acoplamento direto.
* **Solução:** A classe `DopSubject` mantém uma lista de observadores (`IDopObserver`):
  * `DopAlertThresholdObserver`: Dispara alarmes quando a precisão geométrica é violada.
  * `DopLoggingObserver`: Registra eventos em logs de telemetria.
  * `DopTelemetryBufferObserver`: Armazena as amostras em buffer circular para a interface gráfica.

### D. Padrão Facade (*Fachada Modular via `__init__.py`*)
* **Problema:** Proteger consumidores de conhecerem a árvore profunda de diretórios internos e evitar quebras quando arquivos internos são refatorados.
* **Solução:** Todos os subpacotes (`core.domain.astrodynamics`, `core.domain.navigation_pvt`, `core.application.dtos`, `adapters.api`, etc.) atuam como Fachadas explícitas exportando seus símbolos públicos através de `__all__`.

### E. Padrão Singleton Thread-Safe com Lock Reentrante
* **Problema:** Garantir que rotas HTTP assíncronas do FastAPI, o laço de streaming WebSocket e os pulsos de física externa acessem uma visão unificada e atômica da simulação.
* **Solução:** As classes `TelemetryHub` e `SimulationSessionService` implementam o padrão Singleton protegido por `threading.RLock`, permitindo reentrância segura e eliminando condições de corrida.

### F. Padrão Micro-Frontend Embed (*2D Leaflet $\leftrightarrow$ 3D Cesium*)
* **Problema:** Um globo 3D WebGL (CesiumJS) consome recursos intensivos de GPU e shaders, o que provocaria travamentos e colisões na DOM se executado no mesmo escopo JavaScript que os gráficos Chart.js e tabelas do painel 2D.
* **Solução:** O visualizador Cesium roda em uma rota dedicada (`/cesium/viewer`) e é embutido na aplicação principal via `<iframe>` isolado. A troca entre a projeção 2D e o globo 3D ocorre instantaneamente apenas alternando a visibilidade dos containers, com desacoplamento total de contextos gráficos.
