# 🧩 Teoria dos Adaptadores Inteligentes e Arquitetura Hexagonal Fractal

Este documento estabelece a teoria, a taxonomia e as regras de design para a construção de adaptadores na Arquitetura Hexagonal do **Brazilian RPS Sim**, cobrindo desde adaptadores passivos simples até fractais autônomos de Nível 3.

---

## 🎯 1. A Dicotomia: *Thin Adapters* vs. *Smart Adapters*

Nem todo adaptador em uma Arquitetura Hexagonal necessita da mesma densidade estrutural. A complexidade do adaptador é estritamente proporcional à complexidade de estado do agente externo com o qual ele se comunica:

1. **Adaptadores Finos (*Thin / Passive Adapters*):**
   * Adequados para protocolos *stateless*, canais unidirecionais simples ou serializadores imediatos (ex.: exportador CSV/JSON em lote, logger textual, endpoints REST simples de leitura).
   * Operam apenas como conversores de tipos: $\text{DTO}_{\text{Core}} \to \text{Payload}_{\text{Externo}}$. Não possuem máquinas de estado, laços temporais ou ciclo de vida autônomo.
2. **Adaptadores Inteligentes (*Smart / Rich Adapters*):**
   * Mandatórios quando o sistema periférico possui **seu próprio relógio de execução, ciclo de vida de nós, concorrência interna ou restrições rígidas de sincronismo** (ex.: CesiumJS com WebGL render loop, Gazebo Sim com motor físico ODE/OGRE 2, ROS 2 com DDS/rmw e Ngspice com solver transiente analógico).
   * Um adaptador fino falha perante esses sistemas porque o sistema externo tem vida própria e tenderá a divergir silenciosamente (como observado quando o Cesium animava órbitas com a simulação pausada).

---

## 🏛️ 2. A Estrutura em Três Camadas de um *Smart Adapter*

Para evitar que a complexidade do mundo externo contamine o Core e garantir que os contratos sejam respeitados, o *Smart Adapter* decompõe-se internamente em três camadas:

```text
[ Core do Sistema (Domínio & Casos de Uso) ]
                     ▲
                     │ Porta Soberana (IClockPort, ITelemetryPort, IControlPort)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                 ADAPTADOR INTELIGENTE (SMART ADAPTER)        │
│                                                             │
│  1. Adapter Application Layer                               │
│     ├── Orquestrador de Ciclo de Vida (Init / Teardown)     │
│     ├── Gerenciador de Sincronismo Temporal & Anti-Deriva  │
│     ├── Detecção de Pausa & Watchdogs de Heartbeat          │
│     └── Tradutor de Intenção e Comandos de Controle         │
│                                                             │
│  2. Adapter Domain Layer                                    │
│     ├── Modelo Conceitual do Protocolo Externo              │
│     │   (Ex: Netlist AST no Ngspice, Scene Graph no Cesium, │
│     │    QoS Profiles no ROS 2, Sentenças NMEA 0183)        │
│     └── Invariantes & Validações da Tecnologia Específica   │
│                                                             │
│  3. Adapter Driver / Transport Layer                        │
│     ├── Sockets Web (WebSocket / TCP / UDP)                 │
│     ├── Subprocess IPC (stdio pipes / POSIX signals)        │
│     └── Bindings C++/Middleware (rclpy / DDS)               │
└─────────────────────────────────────────────────────────────┘
                     ▲
                     ▼
[ Sistema ou Engine Externa (CesiumJS, Gazebo, ROS 2, Ngspice) ]
```

* **Adapter Application Layer:** Responsável por governar a ponte de controle entre a sessão do Core e a sessão externa. Implementa políticas de tolerância a falhas, reconexão, amortecimento de jitter de rede e sincronização de relógio.
* **Adapter Domain Layer:** Representa a ontologia da tecnologia externa. O Core de radionavegação não deve conhecer o que é uma *directive `.tran`*, um *nó SPICE*, um *pacote CZML* ou um *perfil de QoS Transient Local*. Esse vocabulário pertence legitimamente ao Domínio do Adaptador.
* **Adapter Driver / Transport Layer:** O código de baixo nível que lida com I/O de rede, pipes de sistema operacional ou chamadas nativas C/C++.

---

## 🌀 3. A Natureza Fractal da Arquitetura Hexagonal (*Fractal Hexagons*)

Conforme formulado por Alistair Cockburn, a Arquitetura Hexagonal é **recursiva e fractal**:
> *"Cada hexágono representa um Bounded Context. Ao ampliarmos uma das arestas (um Adaptador), descobrimos no seu interior um outro hexágono completo."*

O adaptador não é um mero script "colado" na borda; ele é um **micro-sistema autônomo** com suas próprias portas internas:
* Uma porta interna voltada para a aplicação do Core;
* Seu próprio domínio de protocolo/tecnologia;
* Portas de saída secundárias conectadas aos drivers de comunicação física.

Essa separação fractal impede o vazamento de abstrações (*leaky abstractions*), permitindo substituir, por exemplo, o CesiumJS por Unreal Engine 5, ou o Ngspice por Xyce/LTspice, sem alterar uma única linha do Core do RPS-BR.

---

## ⏱️ 4. Regulação Temporal Formal (Conformidade com IEEE 1516 / HLA)

Para simulações distribuídas em engenharia aeroespacial, o tempo não é um parâmetro trivial de transporte. Adotamos os princípios da norma **IEEE 1516 (High Level Architecture - HLA)**:
* **Time-Regulating Entity:** O Core atua como regulador soberano do relógio virtual em modo *Standalone*.
* **Time-Constrained Entity:** Todos os *Smart Adapters* de visualização ou co-simulação (Cesium, Dashboard, Displays) são entidades estritamente restritas pelo tempo, proibidas de avançar o estado sem a respectiva autorização temporal (*Time Advance Grant*).
* **Master Co-Simulation Mode:** Quando o Gazebo Sim é ativado, o Gazebo assume temporariamente a regulação da física de corpo rígido, transmitindo pulsos `/clock` que o Core ingere e redistribui para os demais federados escravos.

---

## ⚠️ 5. O Antipadrão do "Adaptador de Utilidades" e Acoplamento Lateral

Em grandes projetos de engenharia de software, surge com frequência a tentação de consolidar múltiplas pequenas rotinas de suporte (parsers auxiliares, conversores de formato, cálculo de checksums, manipuladores de string) em um único "Adaptador de Utilidades" (*Utility/Common Adapter*). Essa prática é um **antipadrão grave** na Arquitetura Hexagonal:

1. **Violação do Princípio da Responsabilidade Única (SRP) e Contratos de Portas:**
   * Cada porta do Core expressa uma intenção de negócio coesa (ex.: `ITelemetryExportPort`, `ISerialLogPort`, `IClockPort`).
   * Um adaptador "faz-tudo" implementa portas díspares ou expõe interfaces genéricas sem coesão semântica, transformando-se em uma *God Class* (*Blob*).
   * Ele acopla desnecessariamente dependências externas heterogêneas (ex.: bibliotecas de rede, parsers XML, drivers seriais) em consumidores que precisavam de apenas uma função pontual.
2. **A Regra de Ouro sobre Acoplamento Lateral (*Adapter-to-Adapter*):**
   * **Adaptadores nunca devem depender diretamente de outros adaptadores.** Se o adaptador ROS 2 importar diretamente classes internas do adaptador FastAPI/REST, cria-se uma malha de dependências cruzadas que destrói a modularidade hexagonal.
   * Se dois ou mais adaptadores necessitam de lógica compartilhada (ex.: conversão de coordenadas, rotinas matemáticas, serialização NMEA comum), essa lógica deve residir em:
     * **`infrastructure/common` ou `infrastructure/utils`:** Para utilitários técnicos puros e sem estado (*Shared Kernel* de infraestrutura);
     * **`core/domain/shared`:** Se a função representar uma regra de cálculo, invariante matemática ou conversão de unidades do domínio aeroespacial.

---

## 📊 6. Taxonomia e Níveis de Complexidade de Adaptadores (Nível 1 a Nível 3)

A decomposição interna de um adaptador segue o princípio da proporcionalidade, categorizando-se em três níveis de maturidade arquitetural:

| Nível de Maturidade | Classificação | Camada de Aplicação do Adaptador | Camada de Domínio do Adaptador | Casos de Uso Típicos |
| :--- | :--- | :--- | :--- | :--- |
| **Nível 1** | **Thin / Direct Adapter** | **Inexistente:** Apenas função/método de tradução direta ($\text{DTO} \to \text{Payload}$). | **Inexistente:** Sem conceitos ontológicos locais. | Exportador CSV, gravador de logs stdout, endpoint REST simples de leitura. |
| **Nível 2** | **Smart / Composite Adapter** | **Presente (4 Elementos Canônicos):** Application Service, DTOs locais, Mappers e Interfaces de Driver. | **Leve / Parcial:** Value Objects de protocolo e enums de estado (sem agregados pesados). | Cesium Viewer (`CesiumClockSynchronizer`, `JulianDateVO`), Dashboard WebSocket Hub. |
| **Nível 3** | **Fractal / Autonomous Engine Adapter** | **Completa (4 Elementos):** Orquestrador de transientes, buffers de sincronismo, observadores e tratadores de erro. | **Rica (Elementos Táticos DDD):** Agregados de tecnologia (ex: `SatelliteCircuitAggregate`), Entidades, VOs, Domain Services e Factories. | Co-simulador Ngspice, simuladores SDR (Software-Defined Radio), bridges robóticas avançadas. |

### A Composição Canônica da *Adapter Application Layer*
Quando um adaptador atinge o Nível 2 ou 3, sua camada de aplicação reproduz de fato a mesma estrutura em 4 elementos canônicos da camada de aplicação do Core:
1. **Adapter Application Services:** Orquestram a sequência de execução local (ex.: `NgspiceCoordinatorService`, `CesiumClockSyncService`).
2. **Adapter DTOs:** Estruturas de dados próprias da tecnologia externa (ex.: `SpiceTransientOutputDTO`, `CesiumFrameStateDTO`), blindando o Core contra peculiaridades do protocolo.
3. **Adapter Mappers:** Conversores bidirecionais estritos ($\text{Core DTO} \longleftrightarrow \text{Adapter DTO}$), assegurando que evoluções nas APIs de bibliotecas externas não afetem o Core.
4. **Adapter Driver Interfaces:** Portas internas do próprio adaptador (ex.: `INgspiceProcessDriver`), permitindo testar a lógica do adaptador com mocks sem disparar processos no sistema operacional.

---

## 🛠️ 7. A Camada de Driver e Transporte (*Adapter Driver / Transport Layer*)

A terceira camada de um *Smart Adapter* é a **fronteira física de contato com o ambiente hospedeiro**. Ela é responsável por interagir diretamente com o Sistema Operacional, protocolos de rede de baixo nível, bibliotecas C nativas ou hardware físico.

```text
┌─────────────────────────────────────────────────────────────┐
│                 ADAPTER APPLICATION LAYER                   │
│         (Orquestração, Máquina de Estados, Mappers)         │
└──────────────────────────────┬──────────────────────────────┘
                               │
               usa interface   ▼
┌─────────────────────────────────────────────────────────────┐
│              INTERFACE DE DRIVER (Porta Interna)            │
│               ex: INgspiceProcessDriver                     │
└──────────────────────────────┬──────────────────────────────┘
                               │
         implementada por      ▼
┌─────────────────────────────────────────────────────────────┐
│           ADAPTER DRIVER / TRANSPORT IMPLEMENTATION         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 1. Gestão de Processos & Sinais POSIX (SIGTERM/KILL)  │  │
│  │ 2. Streams Assíncronos sem Deadlock (stdin/stdout)    │  │
│  │ 3. Timeouts Rígidos de Execução (Evita Hangs de CPU)  │  │
│  │ 4. Memória Compartilhada / I/O em /dev/shm            │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
              [ Binário Externo / SO / Hardware ]
```

---

## 🧬 8. Adaptadores Fractais de Nível 3: Adaptadores Internos e Substratos Privados

Uma característica notável dos Smart Adapters de Nível 3 (como o Ngspice) é que eles **podem possuir seus próprios adaptadores de borda e seus próprios substratos locais privados**:

```text
rps_br/adapters/ngspice/
├── __init__.py               # Fachada pública do adaptador fractal
├── application/              # Camada de Aplicação do Fractal
│   ├── services/             # NgspiceCoSimulationService
│   └── dtos/                 # DTOs de circuito e telemetria elétrica
├── domain/                   # Domínio Rico do Fractal (8 Elementos DDD)
│   ├── aggregates/           # SatelliteCircuitAggregate
│   ├── entities/             # CircuitNodeEntity, ComponentEntity
│   ├── value_objects/        # ResistanceVO, CapacitanceVO, TransientResultVO
│   ├── specifications/       # BatteryUnderVoltageSpecification
│   ├── policies/             # SolverConvergenceRemediationPolicy
│   └── services/             # NetlistTopologicalValidatorService
├── ports/                    # Portas Internas do Fractal
│   ├── driver_port.py        # INgspiceProcessDriver
│   └── parser_port.py        # INetlistParserPort
├── drivers/                  # ADAPTADORES LOCAIS DO FRACTAL
│   ├── async_process_driver.py # Adaptador de subprocesso POSIX real
│   ├── mock_process_driver.py  # Adaptador mock para testes unitários
│   └── shm_driver.py           # Adaptador de leitura em /dev/shm
└── substrates/               # SUBSTRATOS LOCAIS PRIVADOS (Infraestrutura Local)
    ├── netlist_compiler.py   # Gerador/compilador procedural de sintaxe SPICE
    └── model_cache.py        # Cache em disco de bibliotecas de semicondutores
```

### Regra de Subsidiariedade de Substratos:
1. **Substrato Global (`rps_br/infrastructure/`):** Utilizado para recursos de missão compartilhados (enlace de NoC em memória compartilhada, carregador de parâmetros YAML da simulação, cofre de telemetria da missão).
2. **Substrato Local Privado (`adapters/<fractal>/substrates/`):** Utilizado estritamente para suporte técnico específico daquela tecnologia (parser de netlists SPICE, cache de shaders 3D, drivers seriais de hardware dedicado).
