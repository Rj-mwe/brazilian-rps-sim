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

## 🧬 8. Anatomia Canônica de um Fractal de Nível 3: Os 12 Elementos do Núcleo

Na teoria do **Hexágono Dourado** e da **Clean Fractal Hexagonal Architecture**, um *Smart Adapter de Nível 3 (Fractal)* não é um simples conversor de formatos; ele é um **Bounded Context autônomo** que reproduz com precisão cirúrgica a anatomia formal do Core do sistema.

O núcleo de um fractal de Nível 3 decompõe-se rigorosamente em **12 Elementos Canônicos** (4 na Camada de Aplicação e 8 na Camada de Domínio):

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                 OS 12 ELEMENTOS CANÔNICOS DO NÚCLEO FRACTAL                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CAMADA DE APLICAÇÃO DO FRACTAL (4 Elementos Canônicos):                    │
│  ├── 1. Application Services: Orquestradores de fluxo e casos de uso locais │
│  ├── 2. Data Transfer Objects (DTOs): Contratos de dados tipados locais     │
│  ├── 3. Mappers: Tradutores bidirecionais (NoC Envelope <-> DTO <-> Domínio)│
│  └── 4. Ports / Interfaces: Contratos de entrada (NoC) e saída (Drivers)    │
│                                                                             │
│  CAMADA DE DOMÍNIO DO FRACTAL (8 Elementos Táticos DDD):                    │
│  ├── 5. Aggregates: Raiz de consistência e integridade transacional         │
│  ├── 6. Entities: Objetos com identidade unívoca e ciclo de vida contínuo   │
│  ├── 7. Value Objects (VOs): Valores imutáveis com invariantes físicas      │
│  ├── 8. Domain Services: Lógica de cálculo e física pura do subsistema      │
│  ├── 9. Specifications: Predicados booleanos isolados para regras de negócio│
│  ├── 10. Policies: Estratégias de decisão e contingência dinâmica          │
│  ├── 11. Domain Events: Notificações de eventos e anomalias locais          │
│  └── 12. Factories: Construtores seguros de agregados e redes complexas     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Tabela Descritiva dos 12 Elementos Canônicos no Fractal

| Camada | Elemento | Papel no Fractal | Exemplo Prático (Adaptador Ngspice) |
| :--- | :--- | :--- | :--- |
| **Aplicação** | **1. Application Service** | Coordenar o fluxo de integração do passo, transição de estados locais e tratamento de timeout. | `NgspiceCoSimulationService`, `TransceiverMonitoringService` |
| **Aplicação** | **2. DTOs** | Estruturas imutáveis para transferência de parâmetros elétricos e telemetrias seriais. | `SpiceNetlistParametersDTO`, `CircuitTelemetryOutputDTO` |
| **Aplicação** | **3. Mappers** | Conversores puros e bidirecionais que isolam o domínio do fractal contra formatos de pacotes. | `SpiceTelemetryMapper`, `CircuitStateMapper` |
| **Aplicação** | **4. Ports / Interfaces** | Portas abstratas que definem o que a aplicação exige do exterior (inbound e outbound). | `INetworkInterface` (NoC), `INgspiceProcessDriver` |
| **Domínio** | **5. Aggregates** | Raiz transacional que garante leis fundamentais (ex.: Kirchhoff, conservação de carga). | `SatelliteCircuitAggregate` (unindo painéis, baterias e barramento) |
| **Domínio** | **6. Entities** | Elementos do circuito cuja identidade perdura ao longo de múltiplos passos temporais. | `CircuitNodeEntity` (nó `BUS_28V`), `TransistorDeviceEntity` |
| **Domínio** | **7. Value Objects** | Grandezas físicas com validação de limites e unidades no `__post_init__`. | `VoltsVO`, `AmperesVO`, `OhmVO`, `DecibelsVO`, `TransientResultVO` |
| **Domínio** | **8. Domain Services** | Rotinas que implementam equações e verificações sem pertencer a uma única entidade. | `NetlistTopologicalValidatorService`, `PowerBudgetCalculator` |
| **Domínio** | **9. Specifications** | Predicados reutilizáveis para checagens de integridade e segurança operacional. | `BatteryUnderVoltageSpecification`, `OperatingPointBoundedSpec` |
| **Domínio** | **10. Policies** | Regras de comutação comportamental sob anomalias ou regimes operacionais distintos. | `SolverConvergenceRemediationPolicy`, `BatteryAgingPolicy` |
| **Domínio** | **11. Domain Events** | Disparo de notificações semânticas internas quando ocorrem transições críticas. | `BatteryDepletionWarningEvent`, `TransmitterSagDetectedEvent` |
| **Domínio** | **12. Factories** | Fábricas que montam grafos complexos a partir de configurações astronômicas do Core. | `SatelliteCircuitFactory`, `GroundStationLnaFactory` |

---

## 🌐 9. A Integração com o NoC e o Verdadeiro Papel dos Drivers Locais

A relação entre o **Network on Core (NoC)** e os **Drivers Locais** no fractal resolve uma confusão conceitual frequente sobre onde reside a fronteira de transporte:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                FLUXO DE COMUNICAÇÃO DO FRACTAL: NoC vs. DRIVERS             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ═══════════════════════════════════════════════════════════════════════   │
│     MALHA DE ALTO NÍVEL DO NoC (Intra-Sistema: Core, Governança, Outros)   │
│   ═══════════════════════════════════════════════════════════════════════   │
│                                      │                                      │
│               MissionPacket          │ Canais Virtuais:                     │
│               (VC-Control / VC-CoSim)│ VC-Control (Passos e Sincronismo)    │
│                                      │ VC-CoSimulation (Matrizes e Vetores) │
│                                      ▼                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ 1. PORTA NoC DO FRACTAL (Edge Network Interface do Adaptador)       │   │
│   │    - Implementa INetworkInterface                                   │   │
│   │    - Recebe STEP_REQUEST e injeta STEP_CONFIRMED                    │   │
│   └──────────────────────────────────┬──────────────────────────────────┘   │
│                                      │ DTOs Desempacotados                  │
│                                      ▼                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ 2. CAMADA DE APLICAÇÃO & DOMÍNIO DO FRACTAL                         │   │
│   │    - Os 12 Elementos Canônicos executam a física do subsistema      │   │
│   │    - Invoca portas internas abstratas: INgspiceProcessDriver        │   │
│   └──────────────────────────────────┬──────────────────────────────────┘   │
│                                      │ Comandos Nativos de E/S              │
│                                      ▼                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ 3. ADAPTER DRIVER / TRANSPORT LAYER (Fronteira com o Mundo Externo) │   │
│   │    - async_process_driver.py (Subprocesso POSIX /usr/bin/ngspice)   │   │
│   │    - in_memory_mock_driver.py (Testes herméticos sem SO)            │   │
│   │    - shm_raw_reader.py (Leitura de binários em /dev/shm)            │   │
│   └──────────────────────────────────┬──────────────────────────────────┘   │
│                                      │ Pipes stdin/stdout / Buffers         │
│                                      ▼                                      │
│                       [ Binário Ngspice / Hardware ]                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

1. **A Comunicação Inter-Subsistemas É 100% Unificada no NoC:**
   * O fractal **NÃO expõe portas diretas acopladas para o Core ou para outros adaptadores**.
   * Não há drivers de acoplamento lateral (*cross-adapter drivers*). Toda a coordenação com a física orbital do Core, com o relógio da Governança ou com o motor 3D do Cesium transita **exclusivamente pelos Canais Virtuais do NoC** (`VC-Control`, `VC-CoSimulation`, `VC-Telemetry`).
   * A porta de entrada do fractal para o ecossistema RPS-BR é a sua **Network Interface (NI)**.
2. **O Escopo Estrito da Camada de Drivers (`drivers/`):**
   * A pasta `drivers/` dentro de um fractal **não se comunica com outros módulos de software do projeto**.
   * Sua função é única e exclusiva: atuar como o **transceiver físico de baixo nível** com o agente externo concreto (o processo POSIX `/usr/bin/ngspice`, a porta serial de um receptor GNSS físico, ou o contexto WebGL da placa gráfica).

---

## 🏛️ 10. O Sub-Core de Aplicação no Fractal e a Governança Subordinada

Uma dúvida central de projeto é: **Deve o Fractal de Nível 3 possuir seu próprio Sub-Core de Aplicação e seu próprio Sub-Core de Governança?**

### 1. O Sub-Core de Aplicação Local É Necessário:
* Sim. Para coordenar os casos de uso específicos do subsistema (ex.: sintetizar uma netlist a partir da irradiância solar, disparar a integração transiente, capturar os resultados e calcular o ponto de operação quiescente), o fractal necessita de uma **Camada de Aplicação Local** autônoma contendo seus próprios Services, DTOs, Mappers e Portas.

### 2. A Governança do Fractal É Passiva e Subordinada:
* **Não deve existir um Sub-Core de Governança Ativo no Fractal.**
* Se o adaptador fractal instanciar seu próprio mestre de relógio ou seu próprio escalonador concorrente de background, cria-se o caos temporal: dois relógios mestres disputando o controle dos passos de integração, resultando em deriva temporal e quebra da conformidade com a norma **IEEE 1516 (HLA)**.
* **O Princípio da Governança Subordinada:**
  * O fractal possui apenas um **Supervisor de Integridade Local (*Local Failure Supervisor*)**, responsável por monitorar divergência numérica do integrador trapezoidal ou violação de invariantes locais;
  * Seu ciclo de vida temporal é **estritamente escravo e subordinado** às diretrizes do `ClockMaster` central do Core, que habita em `rps_br/core/application/governance/`. O fractal avança somente quando recebe `STEP_REQUEST` do NoC e pausa imediatamente quando a Governança emite `MISSION_PAUSE`.

---

## 🌲 11. Isomorfismo Estrutural vs. Auto-Similaridade Semântica na Árvore Física

Ao projetar a disposição dos arquivos no sistema de arquivos, surge uma questão fundamental de engenharia de software: **A fidelidade da reprodução fractal deve ser literal (espelhando a pasta `core/` no interior do adaptador) ou uma auto-similaridade semântica pragmática?**

No nível macro do projeto (`rps_br/`), o "conteúdo plasmático" do sistema (o núcleo puro de regras e orquestração) é mantido segregado na pasta `core/`, enquanto os adaptadores habitam a pasta irmã `adapters/` e a infraestrutura habita em `infrastructure/`.

Confrontam-se dois modelos de design para a árvore física de um fractal de Nível 3:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│              CONFRONTO: MODELO ISOMÓRFICO LITERAL vs. MODELO CANÔNICO       │
├──────────────────────────────────────┬──────────────────────────────────────┤
│    ABORDAGEM A: ISOMORFISMO LITERAL  │    ABORDAGEM B: SEMÂNTICA CANÔNICA   │
│       (Espelhamento Recursivo)       │        (Bounded Context Plano)       │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ rps_br/adapters/ngspice/             │ rps_br/adapters/ngspice/             │
│ ├── core/              <-- PLASMA    │ ├── application/       <-- APLICAÇÃO │
│ │   ├── application/                 │ │   ├── dtos/                        │
│ │   │   ├── dtos/                    │ │   ├── mappers/                     │
│ │   │   ├── mappers/                 │ │   ├── services/                    │
│ │   │   └── services/                │ │   └── ports/                       │
│ │   └── domain/        <-- DOMÍNIO   │ ├── domain/            <-- DOMÍNIO   │
│ │       ├── aggregates/              │ │   ├── aggregates/                  │
│ │       ├── entities/                │ │   ├── entities/                    │
│ │       └── value_objects/           │ │   ├── value_objects/               │
│ ├── adapters/          <-- DRIVERS   │ │   └── ... (8 elementos DDD)        │
│ │   └── async_driver.py              │ ├── drivers/           <-- DRIVERS   │
│ └── infrastructure/    <-- SUBSTRATOS│ │   └── async_driver.py              │
│     └── netlist_compiler.py          │ └── substrates/        <-- SUBSTRATOS│
│                                      │     └── netlist_compiler.py          │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ • Pró: Cópia 1:1 exata da raiz.      │ • Pró: Fidelidade total aos 12 ele-  │
│ • Contra: Hiper-aninhamento estéril  │   mentos sem burocracia de pastas.   │
│   (caminhos quilométricos em imports)│ • Pró: Imports concisos e idiomáticos│
│ • Contra: Confusão cognitiva com o   │ • Pró: Alinhado ao PEP 20            │
│   verdadeiro Core do sistema.        │   ("Flat is better than nested").    │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

### Recomendação Formal de Engenharia para o RPS-BR

A literatura clássica de Domain-Driven Design (Eric Evans, Vaughn Vernon) e as normas de arquitetura de software de missão crítica (ESA ECSS-E-ST-40C / NASA Systems Engineering Handbook) recomendam formalmente a **Abordagem B (Auto-Similaridade Semântica Canônica)**:

1. **A Auto-Similaridade é Conceitual e de Contratos, Não de Nomes de Pastas:**
   * A propriedade fractal reside no fato de que o subsistema possui seu próprio Domínio isolado, seus próprios Casos de Uso, suas próprias Portas e seus próprios Substratos.
   * Inserir uma pasta redundante `core/` dentro de `adapters/ngspice/` introduz o antipadrão de **Hiper-Aninhamento (*Over-Nesting / Deep Hierarchy Smell*)**, forçando imports artificiais como:
     `from rps_br.adapters.ngspice.core.domain.aggregates.circuit import SatelliteCircuitAggregate`
     em vez da forma límpida e expressiva:
     `from rps_br.adapters.ngspice.domain.aggregates.circuit import SatelliteCircuitAggregate`.
2. **Preservação da Singularidade do Core da Missão:**
   * No vocabulário ubíquo de todo o projeto, **"O Core"** refere-se exclusivamente ao Núcleo da Missão de Radionavegação e Astrodinâmica (`rps_br/core/`). Ter múltiplos subdiretórios chamados `core/` espalhados pelo repositório geraria ruído cognitivo severo para novos engenheiros e ferramentas de análise estática.
3. **Isolamento Plasmático Preservado:**
   * O "conteúdo plasmático" do fractal permanece 100% puro dentro de `adapters/ngspice/domain/` e `adapters/ngspice/application/`. Ele **não depende de nenhum detalhe externo de `drivers/` ou `substrates/`**, garantindo a mesma inviolabilidade da Regra de Dependência Concêntrica observada no hexágono central.
4. **Prontidão para Desacoplamento Externo (*Standalone Extraction*):**
   * Caso o módulo Ngspice precise futuramente ser extraído para um pacote Python independente no PyPI (ex.: `brazilian-rps-ngspice`), a estrutura da Abordagem B já corresponde exatamente ao layout padrão de um pacote autônomo, dispensando qualquer refatoração.

---

## 🗂️ 12. Árvore Canônica Completa de um Fractal de Nível 3

Consolidando todas as decisões arquiteturais, a topologia canônica final de um Smart Adapter Fractal de Nível 3 é especificada formalmente como:

```text
rps_br/adapters/ngspice/
├── __init__.py                     # Fachada pública do Fractal: exporta fábrica e Network Interface
├── noc_interface.py                # EDGE NETWORK INTERFACE: Transceiver conectado ao NoC central
│
├── application/                    # CAMADA DE APLICAÇÃO DO FRACTAL (4 Elementos Canônicos)
│   ├── __init__.py                 # Fachada dos casos de uso locais
│   ├── services/                   # 1. APPLICATION SERVICES (Orquestradores de fluxo e transientes)
│   │   ├── ngspice_simulation_service.py
│   │   └── circuit_convergence_monitor.py
│   ├── dtos/                       # 2. DTOs LOCAIS (Contratos de dados desacoplados do Core)
│   │   ├── circuit_parameters_dto.py
│   │   └── transient_telemetry_dto.py
│   ├── mappers/                    # 3. MAPPERS (Conversores NoC Packet <-> DTO <-> Domínio)
│   │   ├── spice_telemetry_mapper.py
│   │   └── netlist_dto_mapper.py
│   └── ports/                      # 4. INTERFACES / PORTAS INTERNAS DO FRACTAL
│       ├── ngspice_process_port.py # INgspiceProcessDriver (contrato do driver)
│       └── netlist_compiler_port.py# INetlistCompilerSubstrate (contrato do compilador)
│
├── domain/                         # CAMADA DE DOMÍNIO DO FRACTAL (8 Elementos Táticos DDD)
│   ├── __init__.py                 # Fachada ontológica do circuito
│   ├── aggregates/                 # 5. AGGREGATES (Raiz transacional e invariantes de Kirchhoff)
│   │   └── satellite_circuit_aggregate.py
│   ├── entities/                   # 6. ENTITIES (Identidade unívoca de dispositivos e nós)
│   │   ├── circuit_node_entity.py
│   │   └── spice_device_entity.py
│   ├── value_objects/              # 7. VALUE OBJECTS (Grandezas físicas e invariantes imutáveis)
│   │   ├── electrical_units_vo.py  # VoltsVO, AmperesVO, OhmsVO, FaradsVO
│   │   ├── transient_result_vo.py  # Vetores temporais de tensão e corrente
│   │   └── spice_directive_vo.py   # .tran, .step, .options
│   ├── services/                   # 8. DOMAIN SERVICES (Física pura de semicondutores e validação)
│   │   ├── netlist_topology_service.py
│   │   └── power_budget_domain_service.py
│   ├── specifications/             # 9. SPECIFICATIONS (Predicados de invariantes e limites)
│   │   ├── battery_undervoltage_spec.py
│   │   └── thermal_junction_limit_spec.py
│   ├── policies/                   # 10. POLICIES (Estratégias de convergência e envelhecimento)
│   │   ├── solver_convergence_policy.py
│   │   └── battery_cycle_aging_policy.py
│   ├── events/                     # 11. DOMAIN EVENTS (Notificações de estado e anomalias)
│   │   ├── battery_critical_depletion_event.py
│   │   └── rf_amplifier_compression_event.py
│   └── factories/                  # 12. FACTORIES (Hidratação segura de grafos de circuitos)
│       └── satellite_circuit_factory.py
│
├── drivers/                        # ADAPTADORES LOCAIS PRIVADOS (Fronteira com o Mundo Externo)
│   ├── __init__.py
│   ├── async_process_driver.py     # Implementação real via subprocess POSIX (/usr/bin/ngspice)
│   ├── in_memory_mock_driver.py    # Implementação mock hermética para testes unitários rápidos
│   └── shm_raw_reader.py           # Leitor de buffers vetoriais em /dev/shm
│
└── substrates/                     # SUBSTRATOS LOCAIS PRIVADOS (Fundação Técnica do Fractal)
    ├── __init__.py
    ├── netlist_compiler.py         # Substrato de compilação textual e higienização de netlists
    └── model_library_cache.py      # Cache em disco de bibliotecas de transistores e diodos
```

